# W13 brief — Promos / free-bet inventory event log + reference data

**Status:** draft Session 130; locked at operator approval.
**Lock anchor:** 2026-05-12 ACST (Adelaide local per DR-021;
exact lock timestamp captured in `sessions/SESSION_130.md`
at close).
**Workstream:** W13 (operational store sub-stream — promos
and free-bet inventory event log, plus the three reference
tables that promo events FK against). Second per-domain
event log table shipping in v3 after W14's
`cash_flow_events`; inherits the row-only repository plus
workflow-side adapter convention locked at W14.1.
**Recipient:** Claude Code, single bounded session.
**Brief location:** `dr029/w13_promos/w13_promos_brief.md`.
**Substrate inheritance:** W14 brief
(`dr029/w14_cash_flow/w14_cash_flow_brief.md`, 1,665 lines)
is the substantive template; W14.1 brief
(`dr029/w14_cash_flow/w14_1_adapter_brief.md`, 1,586 lines)
locks the v3 row-only-repository + workflow-side-adapter
convention W13 inherits.

---

## §1 — What this brief is and is not

### §1.1 — What this brief is

This brief commissions Code to **ship W13's substantive
operational-store surface** — a new per-domain event log
table (`promo_events`) plus three reference tables
(`promo_template`, `promo`, `warning_catalogue`) that
`promo_events` FK against — built directly to the W14.1 v3
convention from session one. Row-only repositories under
`store/repositories/`, workflow-side adapter at
`workflows/promos/v1/promo_store_adapter.py`, three-way
test split (schema / row-level repository / adapter-level
Pydantic) — same shape that W14.1 shipped clean at
Session 129.

The work has five anchors:

- **New schema file:** `store/schema/promos.py` — DDL for
  `promo_events` plus the three reference tables, indexes
  per the access patterns named in §5.1.2, FK constraints
  to W11 tables and to the reference tables, CHECK
  constraints on closed-enum columns,
  `apply_migrations(conn)` idempotent migration function.
  Mirrors `store/schema/cash_flow.py` (W14) in module shape;
  larger surface because four tables instead of two.
- **New domain file:** `domain/promos/__init__.py` —
  Pydantic v2 models encoding the nine event types from
  `architecture.md` §A.4 (the closed event-type set:
  `promo_observed` / `promo_journey_annotation` /
  `free_bet_credited` / `free_bet_deployed` /
  `free_bet_revoked` / `free_bet_expired` /
  `promo_cash_credited` / `accountcare_warning_raised` /
  `accountcare_warning_cleared`), plus reference data
  models (`PromoTemplate`, `Promo`,
  `WarningCatalogueEntry`), plus the
  FK-nullability-per-event-type model validator,
  Adelaide-local tz validators, `PAYLOAD_BY_EVENT_TYPE`
  dispatch table. Mirrors `domain/cash_flow/__init__.py`
  (W14, 526 lines) in pattern.
- **New repository file:**
  `store/repositories/promos.py` — row-only repository
  classes (`PromoEventRepository`,
  `PromoTemplateRepository`, `PromoRepository`,
  `WarningCatalogueRepository`) per the W14.1 row-only v3
  convention. `object`-typed surface for IDs and event
  types per the S129 finding (b) lock, with a per-module
  `_promo_event_type_value` helper for enum-vs-string
  normalisation. No `domain.promos` imports; DR-030
  module-boundary discipline holds from session one.
- **New adapter file:**
  `workflows/promos/v1/promo_store_adapter.py` — Pydantic ↔
  row translation surface. Exposes
  `append_event(PromoEvent) -> UUID`,
  `get_event(event_id) -> PromoEvent`, scoped list reads,
  supersession-aware reads, supersession-chain walk, plus
  reference data CRUD (template / promo / warning
  catalogue). Mirrors W14.1's
  `workflows/cash_flow/v1/cash_flow_store_adapter.py` (396
  lines) in structural shape.
- **New `store/__init__.py` additive edit** — adds the
  four new repository classes plus error types at
  alphabetical positions (`Promo*` between
  `PayeeRepository` / `CashFlow*` and `bets`/`accounts`
  entries — Code spots the alphabetical insertion points
  from the existing import block). Pattern matches W14's
  additive edit at S127.
- **Three new test files** at the W14.1-locked layout:
  - `tests/store/repositories/test_promos_schema.py` —
    DDL / migration / CHECK constraint / FK constraint
    tests across all four tables.
  - `tests/store/repositories/test_promos_repository.py` —
    row-level repository tests (append / get / list /
    supersession / FK enforcement / reference data CRUD).
  - `tests/workflows/promos/v1/test_promo_store_adapter.py`
    — adapter-level Pydantic tests (per-event-type
    discriminated-union round-trip, FK-nullability-per-
    event-type validation, Adelaide tz validation,
    supersession-aware reads returning Pydantic).

Plus the package marker files: `domain/promos/__init__.py`
contains the actual domain module (not empty);
`workflows/promos/__init__.py`,
`workflows/promos/v1/__init__.py`,
`tests/workflows/promos/__init__.py`,
`tests/workflows/promos/v1/__init__.py` are empty or
one-line per W14.1 precedent.

The work ships as **five new code files** (schema, domain,
repository, adapter, plus four empty package markers — the
package markers counted as one logical block) plus **three
new test files** plus **one edited file**
(`store/__init__.py`). Net new lines: ~2,000–2,800 across
code; ~1,800–2,400 across tests. Roughly 2x W14's
shipped surface, reflecting the bigger event-type count
(9 vs 8) and three reference tables (vs W14's one).

### §1.2 — What this brief is not

W13 explicitly does **not**:

- **Build the cascade-triggering logic.** §A.7 cascade
  rules (settlement-state change on a bet propagating to
  affected `free_bet_credited` / `promo_cash_credited`
  events via supersession) need a place in the codebase to
  fire. `workflows/burst_review/` is currently empty
  (`__init__.py` only) — the W8 burst-review surface
  named in `architecture.md` §C.1 is unbuilt. W13 ships
  the **adapter write surface that takes cascade payload
  fields** (the new credit event carries
  `cascaded_from_bet_id`, `cascaded_at_settlement_state`,
  `cascade_path` per §A.7) so cascades CAN be written
  cleanly once burst_review lands. W13 does not build the
  trigger; the trigger is a future workstream (likely the
  W8 burst-review build).
- **Build promo journey derivation.** §A.4 says "Promo
  journey is computed on read" — successive
  `promo_observed` events on the same `(promo_template_id,
  book_id, account_at_book_id)` triple form the journey
  timeline. W13 ships the event log that the derivation
  reads from; W13 does **not** build the
  `compute_journey()` derivation function. That lives
  alongside other read-derived state (FB inventory,
  AccountCare warning derivation) in a future read-side
  workstream — probably W12-adjacent or post-W17.
- **Build FB inventory derivation.** §A.9 names FB
  inventory as a computed-on-read surface against
  `promo_events`. W13 ships the event log; W12 (balances /
  read-side derivation) consumes it. The
  `latest_non_superseded_by_scope(event_type=...)` adapter
  read W13 ships is the substrate W12 will call against.
- **Build the AccountCare warning derivation.** §A.9 names
  "Active warnings per account_at_book" as `raised −
  cleared from promo_events, walking supersession`. W13
  ships the event types and the supersession-aware reads
  the derivation needs; the derivation function itself
  isn't W13 territory.
- **Touch DR-030, DR-027, DR-019, or any other DR.** Every
  governing DR W13 honours stays unchanged. No
  `decisions.md` edits this brief; the W13 brief
  references existing DRs and inherits their substance.
- **Touch `architecture.md`.** §A.4 is the substrate W13
  implements; W13 does not edit it. (The S130 close-out
  may flag minor amendments to §A.4 if W13 surfaces shape
  mismatches during build — those land at close-out, not
  during W13 execution.)
- **Touch `domain/cash_flow/__init__.py` or
  `store/schema/cash_flow.py` or
  `store/repositories/cash_flow.py` or
  `workflows/cash_flow/v1/cash_flow_store_adapter.py` or
  any W14-related test file.** W14 and W14.1 are closed
  (S129); all four shipped files are read-only for W13.
  Pattern reference only.
- **Touch W11 (`accounts.py` / `domain/accounts/` /
  `store/repositories/accounts.py`).** W13's FKs reach
  into W11's tables (`accounts`, `books`,
  `accounts_at_book`) but Code does not edit any W11 file.
  Read-only for pattern reference.
- **Touch W4 / W6 bet records.** W13's payload references
  `bet_id` values (in `triggering_bet_id`,
  `deploying_bet_id`, `cascaded_from_bet_id` payload
  fields), but those are stored as strings in the JSON
  payload at v3 day-one. **No SQL-level FK from
  `promo_events` payload-JSON values to `bets.bet_id` is
  enforced** — JSON payload values cannot have SQL FK
  constraints in SQLite. The Pydantic-side type
  annotation is `UUID` (operator-supplied or
  burst-review-supplied); referential consistency to
  `bets.bet_id` is checked at read time via the adapter or
  at burst-review-time via the W8 workflow. Same pattern
  W14 used for `triggering_bet_id`-shaped fields in cash
  flow events (none in W14, but the convention is
  consistent).
- **Build W12 / W15.** W12 (balances) and W15 (ops log)
  are sequenced after W13. W13 leaves them at
  `blocked-on-W13`.
- **Touch any other v3 module.** No `clients/`, no
  `contracts/`, no `ui/`, no `ops/`, no other workflows /
  their tests, no scripts / build config / pyproject.
- **Adopt Alembic.** Migration tool deferral carries
  forward unchanged per DR-031 (the v3 tech stack
  decision; Alembic locked but deferred). W13 uses the
  existing pre-Alembic `apply_migrations(conn)` pattern
  W11 / W14 established.
- **Change behaviour beyond shipping the named surface.**
  Every adapter read returns the data shape the spec
  names; every adapter write accepts the Pydantic input
  the spec names; every error class behaves per the W14
  precedent.

### §1.3 — Why W13 has the scope it does

Six software calls were made during brief drafting
(Session 130); naming them for visibility per
`standing_instructions.md` Cat 5:

- **Reference tables ship in W13 (option (i)) rather than
  pre-split or DDL-only.** Three reference tables
  (`promo_template`, `promo`, `warning_catalogue`) ship
  alongside `promo_events` with full schema + Pydantic +
  row-only repository + adapter CRUD methods. Matches W14's
  `payees` precedent. Alternatives considered: (ii)
  DDL-only with SQL-seeded reference data (rejected —
  leaves Python-side write surface incomplete, creates a
  carry-forward debt) and (iii) pre-split into
  W13a/W13b (rejected — partial-ship discipline per §9.1
  already handles the doesn't-fit case; pre-splitting
  trades coordination overhead for a risk the discipline
  catches). Operator confirmed (i) at S130 pre-draft
  surface.
- **Revocation and expiry are separate event types, not
  status-updates on credit events.** §A.4 lists
  `free_bet_revoked` and `free_bet_expired` as their own
  event types AND describes the supersession-based update
  mechanism. Reconciling the apparent inconsistency: W13
  ships them as discrete event types whose payloads carry
  `revoked_credit_event_id` / `expired_credit_event_id`
  FKs (in the JSON payload, not header) plus a
  revocation/expiry reason, with the event header's
  `supersedes_event_id` FK pointing at the prior credit.
  Inventory derivation walks the supersession chain to
  determine effective status. This is the cleaner reading
  of §A.4; the alternative (status-field updates via new
  credit events) collapses three event types into one and
  loses semantic clarity at no architectural benefit.
- **`promo_cash_credited` revocations are written as NEW
  `promo_cash_credited` events with status='rejected' +
  supersession FK** — there is no `promo_cash_revoked`
  event type. §A.4 lists no cash-revoke event type;
  rather than introduce one, W13 ships cash credit
  revocations via the status-update-via-supersession path
  symmetric to the original credit. Asymmetric with FB
  pattern but matches §A.4 verbatim. If this asymmetry
  bothers downstream consumers, a future architecture
  amendment can add `promo_cash_revoked` cleanly; the
  shipped W13 surface won't need backward-incompatible
  changes.
- **Cascade payload fields land as optional fields on
  `FreeBetCreditedPayload` / `PromoCashCreditedPayload`,
  not as separate subclasses.** When a settlement-state
  change on a bet triggers a cascade per §A.7, the new
  credit event written carries the cascade triple
  (`cascaded_from_bet_id`,
  `cascaded_at_settlement_state`, `cascade_path`) as
  optional fields on the base payload class plus
  `supersedes_event_id` on the event header. Three fields,
  all nullable; populated together when present, all NULL
  for normal triggered or freebie credits. Alternative
  considered: a separate `CascadedFreeBetCreditedPayload`
  subclass — rejected because the discriminator pattern
  works on `event_type_payload` literal which would have
  to differ, and that would add a 10th payload class for
  what is structurally a credit event with extra context.
  Operator confirmed at S130 pre-draft surface.
- **`promo_observed` events with payload-only
  `promo_template_id` (no SQL FK to `promo_template`).**
  The event-type's `promo_template_id` reference lives in
  the payload JSON, not the event header. Same pattern as
  W14's `external_payment` which carries `payee_id` in
  payload. The repository-layer FK enforcement only fires
  on the three header FKs (account_id / book_id /
  account_at_book_id); payload FKs are enforced by the
  adapter at write time (loading the referenced row to
  validate existence) and by the burst-review surface at
  read time for soft-coupled references. v3 day-one ships
  the adapter-side existence check on `promo_template_id`
  for `promo_observed` and `promo_journey_annotation`;
  payload FKs to `bets.bet_id` (in `triggering_bet_id`,
  `deploying_bet_id`, `cascaded_from_bet_id`) are NOT
  checked at write time — those references are validated
  at the burst-review surface that writes them.
- **`accountcare_warning_raised` payload includes
  `warning_type_id` as FK to `warning_catalogue`, payload
  validated at adapter write time.** Same pattern as
  `promo_template_id` above — closed-vocab reference
  validated at adapter layer, not at SQL FK. Keeps the
  event log schema clean (no FK explosion) and keeps the
  adapter as the validation boundary.

These are Cat 5 software/scope calls. Operator can
override any at any time before Code lock.

---
## §2 — Why this work exists

W13 (promos / free-bet inventory) is the **second
per-domain event log table in v3's operational store**.
W14 (cash flow events) shipped first at S127, refactored
to DR-030 compliance at W14.1 (S128 brief / Code execution
between sessions / S129 triage clean-close). The W14.1
refactor established the **v3 convention for per-domain
event log workstreams**: row-only repository at
`store/repositories/` (no `domain/` imports per DR-030)
plus workflow-side adapter at `workflows/<domain>/v1/`
owning Pydantic ↔ row translation. W13 ships against this
convention from session one — no DR-030 surgical fix
needed, because the convention is already locked.

The substantive surface W13 ships is `architecture.md`
§A.4 (the promo and credit chains): nine event types
covering observation, journey annotation, FB lifecycle
(credit / deploy / revoke / expire), cash credit, and
AccountCare warnings. Plus the three reference tables that
the event log FKs against:

- **`promo_template`** — kind-level mechanics (insurance /
  bonus / boost / EW cashback). ~10–30 rows. The
  closed-set catalogue from which specific promos are
  instances. `promo_observed` payloads carry
  `promo_template_id` referencing this table.
- **`promo`** — per-promo instance the operator takes a
  bet against. Bet records (per DR-032) carry
  `promo_instance_id` referencing this table; this is the
  W13-side substrate for the bet-record promo linkage.
- **`warning_catalogue`** — closed-vocab AccountCare
  warning types with severity baselines. The
  closed-schema-open-vocabulary pattern from Slice 4 — new
  warning types can be added by SQL seed without code
  changes. `accountcare_warning_raised` /
  `accountcare_warning_cleared` payloads carry
  `warning_type_id` referencing this table.

**Why all four tables ship together:** the four are
tightly coupled by FK structure. `promo_events` cannot
ship without `promo_template` / `promo` /
`warning_catalogue` existing (the payload validators
check existence at write time per Cat 5 software call
above). The reference tables are not used by anything
else in v3 today — pre-splitting them into a separate
workstream produces a transient state where reference
tables exist but `promo_events` doesn't, with no consumer
for the reference data in the gap. Shipping together is
the cleaner sequencing.

**Two governance anchors W13 honours:**

- **DR-027 + Session 124 amendment** (the two-database
  architecture, per-domain event-table internal shape).
  `promo_events` is the second instance of the per-domain
  event-table pattern; structural shape matches W14's
  `cash_flow_events` exactly (common event header columns,
  payload as JSON, supersession via `supersedes_event_id`
  self-FK, append-only writes, scoped reads by header FK).
- **DR-030 + Session 124 amendment** (the v3
  module-boundary discipline). W13 ships compliant from
  session one. `lint-imports` runs clean across all five
  contracts after W13 lands; no W13.1 surgical fix
  expected.

**Cross-domain anchors W13 references but does not
change:**

- **DR-019 + Session 124 amendment** (derived state on
  read). Promo events are pure event-log writes per the
  amendment's "the materialised-view-on-entity-row
  pattern applies to bet records but NOT to event
  tables" carve-out. FB inventory / AccountCare warning
  state / promo journey are read-derived from
  `promo_events` at read time.
- **DR-022** (book / account / account-at-book
  vocabulary). FKs on `promo_events` use this vocabulary
  identically to W14.
- **DR-032** (canonical-reference-layer / two-table bet
  record schema). `promo_events` payload references
  `bet_id` values for `triggering_bet_id` (credit
  events), `deploying_bet_id` (deployment events), and
  `cascaded_from_bet_id` (cascade-induced credit events).
  Cycle linkage to bet records flows through these
  payload-side references; SQL-level FK not enforced
  (payload JSON values cannot have SQL FKs in SQLite).
- **DR-021** (Adelaide local timestamps). Same validator
  pattern as W14 (`_ensure_adelaide_local` in
  `domain/promos/__init__.py`).

The pattern W13 establishes — same per-domain event-table
shape applied to a second, structurally larger domain
(nine event types vs eight; three reference tables vs
one) — is the template W15 (`ops_events`) reuses when its
workstream lands.

---
## §3 — Pre-reads

### §3.1 — Required reads (read before starting)

Read in order. These define what Code is implementing and
the conventions it must hold.

1. **`dr029/w14_cash_flow/w14_1_adapter_brief.md`** (1,586
   lines) — the v3 row-only-repository + workflow-side-
   adapter convention W13 inherits. Read end-to-end.
   Particularly load-bearing for W13: §5.1 (adapter
   shape — W13's adapter mirrors this), §5.2 (repository
   trim — W13's repository ships row-only from session
   one, no trim phase), §5.3 (three-way test split — W13
   inherits), §6.2 (build order — W13 follows a
   structurally similar sequence), §9.7 (dirty-tree
   handling — carries forward).

2. **`dr029/w14_cash_flow/w14_cash_flow_brief.md`** (1,665
   lines) — the substantive template W13 mirrors. Read
   end-to-end. Particularly load-bearing: §5.1
   (per-event-type Pydantic shape with discriminated union
   payload — W13 follows this pattern across 9 event
   types), §5.1.4 (FK-nullability-per-event-type validator
   — W13 follows this pattern), §5.1.5 (reference data
   shape for `payees` — W13's `promo_template` / `promo` /
   `warning_catalogue` follow this pattern x3), §5.2
   (schema DDL pattern — W13 mirrors the structural shape
   for `promo_events` + 3 reference tables), §5.3 (the
   ORIGINAL Pydantic-at-repository surface — W13 does NOT
   ship this; W13 ships row-only from session one per
   W14.1 convention), §5.4 (`store/__init__.py` additive
   edit pattern — W13 follows this for adding
   `Promo*Repository` and error classes at alphabetical
   positions), §5.5 (test shape — W13 follows the W14.1
   three-way split, not W14's two-way), §6.2 (build
   order — W13's sequencing in §6.2 of THIS brief follows
   the same pattern), §9.7 (dirty-tree handling — carries
   forward).

3. **`architecture.md` §A.4** (the substrate W13
   implements) — read end-to-end (the section runs lines
   276–333 in the rebuild folder's architecture.md). Names
   every event type, the three legs (observation /
   taking / crediting), the FB deployment chain, the FB
   lifecycle terminal events, cash credit handling.
   Carries the AccountCare warning event vocabulary by
   reference to Slice 4 work; the closed-vocab list lands
   in W13's `warning_catalogue` table.

4. **`architecture.md` §A.7** (cascade chains — what a
   settlement-state change on a bet does to credit
   events) — read in full. Locks the cascade payload
   shape W13 ships on credit event payloads. The §A.7
   cascade trigger itself is OUT of W13 scope (lives in
   the future burst_review build); W13 ships the WRITE
   surface for cascade-induced credit events so the
   trigger can land cleanly later.

5. **`architecture.md` §A.2** (per-domain event log spine
   + common event header pattern) — read end-to-end. The
   structural shape W13's `promo_events` carries.

6. **`architecture.md` §A.1** (entity references — the
   stable identifiers everything else hangs off) — read
   the `promo` / `promo_template` / `warning_catalogue`
   entity descriptions. W13's reference tables implement
   these.

7. **`decisions.md` DR-030** (the v3 module-boundary
   discipline + Session 124 amendment) — read body +
   amendment. The contract W13 ships compliant against.

8. **`decisions.md` DR-027** (the two-database
   architecture + Session 124 amendment locking
   per-domain event-table internal shape) — read body +
   amendment. The per-domain event log shape W13's
   `promo_events` is the second instance of.

9. **`decisions.md` DR-019** (derived state on read +
   Session 124 amendment) — read body + amendment.
   Critical asymmetry: applies to bet records but NOT to
   `promo_events` (FB inventory / journey / warning state
   are all read-derived from the event log).

10. **`decisions.md` DR-032** (canonical-reference-layer
    schema for bet records) — read in full. W13's
    payload-side references to `bet_id`
    (`triggering_bet_id`, `deploying_bet_id`,
    `cascaded_from_bet_id`) target the
    `bets.bet_id` column shape locked here.

11. **`decisions.md` DR-022** (book / account /
    account-at-book vocabulary) — read in full. FKs on
    `promo_events` header use this vocabulary.

12. **`bethub-v3/store/schema/cash_flow.py`** (212 lines)
    — the W14 schema file. W13's `store/schema/promos.py`
    mirrors this in module shape (DDL constants,
    `_add_column_if_missing` helper, `apply_migrations`
    function). Read end-to-end as the pattern template.

13. **`bethub-v3/domain/cash_flow/__init__.py`** (526
    lines) — the W14 domain file. W13's
    `domain/promos/__init__.py` mirrors this in structure
    (closed enums, `_PayloadBase`, per-event-type
    `_Payload` subclasses with `event_type_payload`
    discriminator, Adelaide-local tz validator,
    `PAYLOAD_BY_EVENT_TYPE` dispatch table). Read
    end-to-end as the pattern template.

14. **`bethub-v3/store/repositories/cash_flow.py`** (601
    lines, post-W14.1 trim) — the W14.1 row-only
    repository in the wild. W13's
    `store/repositories/promos.py` mirrors this shape:
    row dataclasses, repository class accepting
    `sqlite3.Connection`, row-level methods using
    `object` for ID types, `_event_type_value` enum-vs-
    string helper, supersession LEFT JOIN. Read
    end-to-end as the pattern template.

15. **`bethub-v3/workflows/cash_flow/v1/cash_flow_store_adapter.py`**
    (396 lines) — the W14.1 adapter in the wild. W13's
    `workflows/promos/v1/promo_store_adapter.py` mirrors
    this shape: adapter class taking
    `sqlite3.Connection`, public Pydantic-typed methods,
    module-level row↔Pydantic helpers. Read end-to-end
    as the pattern template.

16. **`bethub-v3/tests/store/repositories/test_cash_flow_repository.py`,
    `tests/store/repositories/test_cash_flow_schema.py`,
    `tests/workflows/cash_flow/v1/test_cash_flow_store_adapter.py`**
    — the W14.1-shipped test suite (relocated and
    reshaped at S128). Skim to confirm test layout, then
    read at depth when drafting W13's test files. The
    three-way split pattern is what W13 inherits.

17. **`bethub-v3/store/repositories/accounts.py`** —
    W11's row-only repository, the original v3 pattern.
    Skim for pattern reinforcement.

18. **`dr029/w11_accounts/w11_accounts_brief.md`** (967
    lines) — the W11 accounts brief; §5.3 explicitly
    locks "No domain imports — `store/` imports nothing
    in the project beyond `store.schema.*` per DR-030."
    Skim end-to-end if not already in working memory.

### §3.2 — Reference-only (read on demand)

- **`standing_instructions.md`** Cat 3 (filesystem and
  tooling discipline — `create_file` ban, verify-every-
  write, REPL discipline, pre-execution risk advisory,
  dirty-tree handling generally) and Cat 5 (operator /
  Claude division of labour).
- **`vision.md`** — non-negotiables. W13's substrate
  ships Job 2 (free-bet inventory spine) of the operator's
  vision; the operational picture stays unchanged at the
  Pydantic surface level.
- **`governance.md`** — DR-029 close-out named debt and
  deferred capabilities. W13 inherits the three pieces of
  named debt cleanly (W13 ships its own test suite, uses
  the existing pre-Alembic schema pattern, doesn't touch
  VPS orchestrator).
- **`v3_build_picture.md`** — current stream state. W13
  transitions from `blocked-on-W14` to `in flight` at
  S130 close (with this brief locked); transitions to
  `done` at the close after Code's W13 report triages
  clean.
- **`dr029/w14_cash_flow/w14_cash_flow_report.md`** (864
  lines) — Code's W14 execution report. Read on demand if
  a W13 design choice routes back to a W14 finding (e.g.
  test layout asymmetry §5.4, file-size overruns §5.8).
- **`dr029/w14_cash_flow/w14_1_adapter_report.md`** (923
  lines) — Code's W14.1 execution report. Read on demand
  if a W13 design choice routes back to a W14.1 finding
  (the `object`-typed surface lock; the brief constructor
  bridge; the three-way test split pattern).
- **`sessions/SESSION_129.md`** — W14.1 report triage
  record. Captures the S129 lock on the loose-typing v3
  convention, the (a)/(b)/(c) findings classification,
  and the forward routing to W13.
- **`sessions/SESSION_128.md`** — W14.1 brief drafting
  record. The pre-execution risk advisory exercise from
  S126 carried forward to S128's option-1 mid-session
  scope-expansion call.

Existing v3 codebase files (read-only browse for pattern
confirmation):

- `bethub-v3/store/schema/accounts.py` — W11 schema
  pattern reference.
- `bethub-v3/store/schema/bets.py` — bet record schema
  (informs `triggering_bet_id` / `deploying_bet_id` /
  `cascaded_from_bet_id` payload-side reference targets).
- `bethub-v3/domain/accounts/__init__.py` — W11 domain
  pattern reference.
- `bethub-v3/workflows/bet_entry/v1/` directory listing —
  package marker pattern.

---

## §4 — System access

- **Read-write** on the v3 codebase at
  `/Users/tim/Desktop/Projects/bethub-v3/` — limited to
  the named anchors:
  - **New files (greenfield writes):**
    - `domain/promos/__init__.py` (the W13 domain
      module — substantive, ~600–800 lines)
    - `store/schema/promos.py` (W13 schema DDL +
      migration, ~300–400 lines)
    - `store/repositories/promos.py` (W13 row-only
      repositories, ~700–900 lines)
    - `workflows/promos/__init__.py` (empty package
      marker)
    - `workflows/promos/v1/__init__.py` (empty package
      marker)
    - `workflows/promos/v1/promo_store_adapter.py` (W13
      adapter, ~500–700 lines)
    - `tests/store/repositories/test_promos_schema.py`
      (~500–700 lines)
    - `tests/store/repositories/test_promos_repository.py`
      (~600–800 lines)
    - `tests/workflows/promos/__init__.py` (empty
      package marker)
    - `tests/workflows/promos/v1/__init__.py` (empty
      package marker)
    - `tests/workflows/promos/v1/test_promo_store_adapter.py`
      (~700–900 lines)
  - **Edit (W14 / W11 alignment with `store/__init__.py`
    additive pattern):**
    - `store/__init__.py` — add `Promo*Repository` class
      names plus error classes (`PromoEventError`,
      `DuplicatePromoEventError`, etc.) at alphabetical
      positions in the existing import block. Pattern
      matches W14's S127 additive edit per W14 brief
      §5.4. No restructuring; pure addition.

  No other paths under `bethub-v3/` are touched.

- **Read-only** on the rebuild folder at
  `/Users/tim/Desktop/Projects/bethub-rebuild/` for all
  reference reads named in §3.

- **No VPS access.** W13 is operational-store work; no
  `capture.db` interaction.

- **No Betfair API access.** W13 is internal application
  code; no external API calls.

- **No live database access** beyond the in-memory /
  `tmp_path`-backed SQLite databases the test suite
  creates and tears down. No production-shape DB file is
  written by W13.

- **Filesystem tool:** Desktop Commander (`write_file`,
  `read_file`, `edit_block`, `list_directory`,
  `start_process`) or `projects-filesystem` MCP server
  (`write_file`, `edit_file`). `create_file` is banned
  per `standing_instructions.md` Cat 3. If Code is
  operating in a Claude Code CLI environment where these
  named tools are not loaded (per W14 report §5.7), the
  CLI's native `Write` / `Edit` tools are acceptable
  substitutes **provided the Cat 3 spirit holds**: every
  write followed by a read-back or test-exercise
  confirming the file landed at the real Mac path.

- **Adelaide local timestamps per DR-021** for every
  time-of-day reference in the report and any timestamp
  literals in test fixtures. ISO 8601 with timezone
  offset (`+09:30` ACST). Use
  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"`
  via `start_process` for session-start and session-close
  anchors.

- **Single bounded Code session.** If the work doesn't
  fit, that's a finding (per §9.1 partial-ship discipline),
  not a continuation. Partial-but-coherent ship beats
  complete-but-lost-coherence.

---
## §5 — Substantive scope

### §5.1 — Schema (`store/schema/promos.py`)

W13 ships four new tables: one event log (`promo_events`)
plus three reference tables (`promo_template`, `promo`,
`warning_catalogue`). DDL pattern mirrors
`store/schema/cash_flow.py` exactly — module-level DDL
constants, indexes, `_add_column_if_missing` helper (for
future additive migrations), `apply_migrations(conn)`
public surface.

#### §5.1.1 — Table ordering and FK dependencies

Migration order matters because the four tables have
internal FK dependencies:

1. **`warning_catalogue`** — no inbound FK dependencies.
   Self-contained reference table.
2. **`promo_template`** — no inbound FK dependencies.
   Self-contained reference table.
3. **`promo`** — FK to `promo_template.promo_template_id`
   (which book runs which template instance).
4. **`promo_events`** — FK to `accounts.account_id`,
   `books.book_id`, `accounts_at_book.account_at_book_id`
   (W11 tables), plus self-FKs on `parent_event_id` and
   `supersedes_event_id`.

`apply_migrations(conn)` creates them in that order;
`CREATE TABLE IF NOT EXISTS` semantics mean ordering is
forgiving on re-run but consistent ordering matters for
fresh migration.

#### §5.1.2 — Indexes

Sized to the access patterns the repository's read
methods expose:

**On `promo_events`:**

- `idx_promo_events_account_at_book` —
  `(account_at_book_id, recorded_at)`. Powers
  `list_rows_by_account_at_book(...)`.
- `idx_promo_events_account` — `(account_id,
  recorded_at)`. Powers `list_rows_by_account(...)`.
- `idx_promo_events_book` — `(book_id, recorded_at)`.
  Powers `list_rows_by_book(...)`.
- `idx_promo_events_event_type` — `(event_type,
  recorded_at)`. Powers `list_rows_by_event_type(...)`
  (analytical scans, e.g. "all `accountcare_warning_*`
  events across last 90 days").
- `idx_promo_events_correlation` — `(correlation_id)`.
  Powers `list_rows_by_correlation_id(...)` (walking a
  single operational unit's full event chain).
- `idx_promo_events_supersedes` —
  `(supersedes_event_id)`. Powers the supersession-aware
  LEFT JOIN reads.

**On `promo_template`:**

- `idx_promo_template_kind` — `(kind)`. Closed-vocab kind
  enum (insurance / bonus_winnings / price_boost /
  ew_cashback / other); index supports kind-scoped
  reference lookups.

**On `promo`:**

- `idx_promo_by_template` — `(promo_template_id)`.
  Supports "find all promo instances using template X".
- `idx_promo_by_book` — `(book_id)`. Supports
  "find all promo instances at book Y".

**On `warning_catalogue`:**

- `idx_warning_catalogue_severity` — `(severity)`.
  Closed-vocab severity enum; index supports severity-
  scoped reference reads.

Total: 9 indexes (6 on `promo_events`, 1 on
`promo_template`, 2 on `promo`, 1 on `warning_catalogue`).

#### §5.1.3 — Closed-enum CHECK constraints

Defence-in-depth alongside Pydantic enums in
`domain/promos/__init__.py`. Pattern: SQLite CHECK
constraint listing the closed-enum string values. Mirrors
the W14 pattern verbatim.

**`promo_events.event_type` CHECK** — nine values per
§A.4:

```
'promo_observed', 'promo_journey_annotation',
'free_bet_credited', 'free_bet_deployed',
'free_bet_revoked', 'free_bet_expired',
'promo_cash_credited', 'accountcare_warning_raised',
'accountcare_warning_cleared'
```

**`promo_events.source` CHECK** — three values:

```
'operator', 'system', 'integration'
```

**`promo_template.kind` CHECK** — five values:

```
'insurance', 'bonus_winnings', 'price_boost',
'ew_cashback', 'other'
```

**`promo.status` CHECK** — three values (whether this
specific promo instance is currently being run by the
book or is historical / expired):

```
'active', 'historical', 'discontinued'
```

**`warning_catalogue.severity` CHECK** — three values
matching DR-015 three-tier alert severity:

```
'red', 'amber', 'yellow'
```

#### §5.1.4 — `promo_events` DDL shape

The full table shape (W14 common event header + W13-
specific structure):

- `event_id TEXT PRIMARY KEY NOT NULL`
- `event_type TEXT NOT NULL CHECK (...)` (nine values)
- `recorded_at TEXT NOT NULL`
- `occurred_at TEXT NOT NULL`
- `account_id TEXT` (nullable; FK to W11 `accounts`)
- `book_id TEXT` (nullable; FK to W11 `books`)
- `account_at_book_id TEXT` (nullable; FK to W11
  `accounts_at_book`)
- `parent_event_id TEXT` (nullable; self-FK to
  `promo_events.event_id`)
- `supersedes_event_id TEXT` (nullable; self-FK to
  `promo_events.event_id`)
- `payload TEXT NOT NULL` (JSON-serialised; per-event-
  type shape enforced at Pydantic layer)
- `source TEXT NOT NULL CHECK (...)` (three values)
- `correlation_id TEXT` (nullable; not FK-constrained —
  free-form identifier shared across related events)
- `notes TEXT` (nullable; free text)

Plus all FK constraints declared via `FOREIGN KEY (...)
REFERENCES ...(...)` clauses at the bottom of the CREATE
TABLE statement. Mirrors `cash_flow_events` verbatim in
this shape.

#### §5.1.5 — `promo_template` DDL shape

Kind-level mechanics — the closed-set catalogue from
which specific promo instances are taken. Stable
reference data; ~10–30 rows once populated. Day-zero
seeding via operator-written SQL (W13 ships no seed
data; the table is empty after migration).

- `promo_template_id TEXT PRIMARY KEY NOT NULL`
- `name TEXT NOT NULL` (human-readable label, e.g.
  "Sportsbet money back if 2nd or 3rd")
- `kind TEXT NOT NULL CHECK (...)` (five values per
  §5.1.3)
- `mechanic_description TEXT NOT NULL` (free-text
  description of how the template's mechanic works)
- `default_terms TEXT` (nullable; JSON — default
  parametric variation for this template; specific
  observations carry their own `terms_at_observation`
  that may override)
- `notes TEXT` (nullable)
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

No FK constraints on this table. Truly self-contained.

#### §5.1.6 — `promo` DDL shape

Per-promo instance the operator takes a bet against. The
DR-032 `bets.promo_instance_id` field (when present) FKs
to this table's `promo_id` column. ~50–200 rows per year
(rough scale; operator adds an entry when running a specific
promo cycle). Day-zero seeding via operator-written SQL.

- `promo_id TEXT PRIMARY KEY NOT NULL`
- `promo_template_id TEXT NOT NULL` (FK to
  `promo_template.promo_template_id`)
- `book_id TEXT NOT NULL` (FK to W11 `books.book_id`)
- `instance_label TEXT NOT NULL` (operator-readable
  label, e.g. "Sportsbet 2nd/3rd Spring Carnival 2026")
- `status TEXT NOT NULL CHECK (...)` (three values per
  §5.1.3)
- `start_date TEXT NOT NULL` (Adelaide-local; ISO 8601
  with TZ offset)
- `end_date TEXT` (nullable; Adelaide-local)
- `notes TEXT` (nullable)
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Plus FK constraints on `promo_template_id` and `book_id`
at the bottom.

#### §5.1.7 — `warning_catalogue` DDL shape

Closed-schema-open-vocabulary AccountCare warning types.
~10–20 rows once populated. Day-zero seeding via
operator-written SQL.

- `warning_type_id TEXT PRIMARY KEY NOT NULL` (e.g.
  `'rapid_turnover'`, `'limit_increase_after_lift'`,
  `'kyc_followup_request'`)
- `label TEXT NOT NULL` (human-readable label, e.g.
  "Rapid turnover spike")
- `severity TEXT NOT NULL CHECK (...)` (three values per
  §5.1.3 — DR-015 tier baseline; specific raise events
  can override via payload)
- `description TEXT NOT NULL` (free-text description of
  the warning class)
- `default_clearance_criteria TEXT` (nullable; free-text
  description of typical clearance conditions)
- `notes TEXT` (nullable)
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

No FK constraints on this table. Truly self-contained.

#### §5.1.8 — Module structure of `store/schema/promos.py`

Mirrors `store/schema/cash_flow.py` structurally:

- Module docstring naming W13 substrate plus the four-
  table set and the §A.4 anchor.
- Imports: `from __future__ import annotations`,
  `import sqlite3`.
- DDL constants in dependency order:
  - `_WARNING_CATALOGUE_DDL`
  - `_PROMO_TEMPLATE_DDL`
  - `_PROMO_DDL`
  - `_PROMO_EVENTS_DDL`
- Index constants in order matching the §5.1.2 listing.
- `_add_column_if_missing` helper (lifted in shape from
  W14 and W11; same body).
- `apply_migrations(conn: sqlite3.Connection) -> None`
  function:
  1. `conn.execute("PRAGMA foreign_keys = ON;")`
  2. Create the four tables in dependency order via
     `conn.executescript(...)`.
  3. Create all 10 indexes.
  4. `conn.commit()`.
  - Idempotent across invocations (PRAGMA + CREATE IF
    NOT EXISTS).

No `_add_column_if_missing` calls in V1 (no additive
migrations on top of the initial DDL); helper exists for
future use.

---
### §5.2 — Domain layer (`domain/promos/__init__.py`)

Pydantic v2 models encoding §A.4 event types plus the
three reference data shapes. Module structure mirrors
`domain/cash_flow/__init__.py` (526 lines) — closed
enums, `_PayloadBase`, per-event-type `_Payload`
subclasses with `event_type_payload` discriminator,
Adelaide-local tz validator, FK-nullability-per-event-
type model validator, `PAYLOAD_BY_EVENT_TYPE` dispatch
table, reference data models.

Expected file size: ~600–800 lines (larger than W14's 526
because nine event types vs eight and three reference
data models vs one).

#### §5.2.1 — Closed enums (Pydantic side; CHECK
                              constraint side at schema)

**`PromoEventType(StrEnum)`** — nine values:

```python
class PromoEventType(StrEnum):
    PROMO_OBSERVED = "promo_observed"
    PROMO_JOURNEY_ANNOTATION = "promo_journey_annotation"
    FREE_BET_CREDITED = "free_bet_credited"
    FREE_BET_DEPLOYED = "free_bet_deployed"
    FREE_BET_REVOKED = "free_bet_revoked"
    FREE_BET_EXPIRED = "free_bet_expired"
    PROMO_CASH_CREDITED = "promo_cash_credited"
    ACCOUNTCARE_WARNING_RAISED = "accountcare_warning_raised"
    ACCOUNTCARE_WARNING_CLEARED = "accountcare_warning_cleared"
```

**`PromoEventSource(StrEnum)`** — three values
(`operator` / `system` / `integration`). Same as W14
`CashFlowEventSource`.

**`PromoTemplateKind(StrEnum)`** — five values
(`insurance` / `bonus_winnings` / `price_boost` /
`ew_cashback` / `other`).

**`PromoStatus(StrEnum)`** — three values (`active` /
`historical` / `discontinued`).

**`WarningSeverity(StrEnum)`** — three values per
DR-015 (`red` / `amber` / `yellow`).

**`PromoObservationScope(StrEnum)`** — four values per
§A.4 (`all_races` / `specific_race` / `specific_event` /
`specific_market`).

**`FreeBetCreditSource(StrEnum)`** — two values per
§A.4 (`triggered` / `freebie`).

**`CreditStatus(StrEnum)`** — three values per Slice 2 D
resolution (`provisional` / `finalised` / `rejected`).

**`RevocationReason(StrEnum)`** — three values
(`book_clawback` / `terms_violation` / `other`). Payload
of `free_bet_revoked`. Note: per S130 operator call,
expiry stays as its own event type (`free_bet_expired`),
not folded into revocation.

**`ExpiryReason(StrEnum)`** — two values
(`face_value_expiry_reached` / `other`). Payload of
`free_bet_expired`. Distinct enum from `RevocationReason`
to keep the two event types semantically clean.

**`CascadePath(StrEnum)`** — two values per §A.7
(`auto` / `operator_explicit`).

**`JourneyAnnotationConfidence(StrEnum)`** — three values
per Slice 4 Q1 (`hypothesis` / `confirmed` / `disproven`).

#### §5.2.2 — Adelaide-local tz validation

Lifted verbatim from
`domain/cash_flow/__init__.py:_ensure_adelaide_local`.
Same `_ACST_OFFSET`/`_ACDT_OFFSET` constants, same naive-
datetime rejection, same offset-equality check. Reused
across `recorded_at` / `occurred_at` on event header,
plus payload datetime fields (e.g.
`face_value_expiry` on credit events, `start_date` /
`end_date` on `Promo` reference data, etc.).

#### §5.2.3 — `_PayloadBase` and the
                  `event_type_payload` discriminator

Lifted verbatim from `domain/cash_flow/__init__.py` —
`extra='forbid'`, `frozen=True`, base class for the nine
per-event-type payload subclasses. Each subclass carries
`event_type_payload: Literal[...]` matching its parent
event's `event_type` value.

#### §5.2.4 — Per-event-type payload subclasses

Nine subclasses, each carrying its `event_type_payload`
literal discriminator and the per-event-type payload
fields. Detailed payload shape per event type:

**`PromoObservedPayload`** (`event_type_payload="promo_observed"`):

- `promo_template_id: UUID` — REQUIRED. FK reference to
  `promo_template.promo_template_id` (validated at
  adapter write time).
- `terms_at_observation: dict[str, object]` — REQUIRED.
  Free-form JSON-shaped dict carrying the parametric
  variation (max_stake, min_odds, qualifying odds bands,
  eligible codes, expiry rules). Pydantic stores as
  `dict`; the JSON envelope handles serialisation.
- `scope: PromoObservationScope` — REQUIRED.
- `active_window_start: datetime | None` — nullable.
  Adelaide-local if present.
- `active_window_end: datetime | None` — nullable.
  Adelaide-local if present.
- `terms_summary: str | None` — nullable. Operator-readable
  one-line summary of the observation (e.g. "Money back
  if 2nd, $50 cap, AU thoroughbred only").

**`PromoJourneyAnnotationPayload`** (`event_type_payload=
"promo_journey_annotation"`):

- `promo_template_id: UUID` — REQUIRED. The template whose
  journey this annotation belongs to. Validated at
  adapter write time.
- `tags: list[str]` — REQUIRED, non-empty.
  Closed-vocabulary-open-list (tag values are
  free-text but operationally settle into a small set —
  e.g. `"shrink"`, `"limit_increase"`, `"new_promo_kind"`,
  `"book_responsiveness_drop"`). The closed-schema-open-
  vocabulary pattern from Slice 4.
- `time_window_start: datetime | None` — nullable.
  Adelaide-local if present.
- `time_window_end: datetime | None` — nullable.
  Adelaide-local if present.
- `related_event_ids: list[UUID]` — defaults to empty
  list. Other `promo_events.event_id` values this
  annotation contextualises.
- `confidence: JourneyAnnotationConfidence` — REQUIRED.
- `commentary: str` — REQUIRED. Operator's interpretive
  text (≤2000 chars; soft cap, not enforced at SQL).

**`FreeBetCreditedPayload`** (`event_type_payload=
"free_bet_credited"`):

- `amount: Decimal` — REQUIRED, `gt=Decimal("0")`. Face
  value of the FB.
- `credit_source: FreeBetCreditSource` — REQUIRED
  (`triggered` or `freebie`).
- `status: CreditStatus` — REQUIRED. (Initial credits land
  as `provisional` or `finalised` per Slice 2 D
  resolution; supersession to `rejected` carries via
  later events.)
- `triggering_bet_id: UUID | None` — REQUIRED if
  `credit_source == triggered`; MUST be None if
  `credit_source == freebie`. (Cross-field validator
  enforces; see §5.2.5.)
- `triggering_promo_instance_id: UUID | None` — REQUIRED
  if `credit_source == triggered`; MUST be None if
  `credit_source == freebie`. References `promo.promo_id`.
  Validated at adapter write time when populated.
- `face_value_expiry: datetime | None` — nullable.
  Adelaide-local if present. Operator-supplied expiry
  date for FBs with a known lapse window.
- `confidence_payload: dict[str, object] | None` —
  nullable. Per Slice 2 D resolution; shape deferred
  pending the confidence model (Q2 from Session 8).
- `reference: str | None` — nullable. Operator's
  free-text reference / book-side label.
- **Cascade fields (all nullable, populated together
  when present)** per §A.7:
  - `cascaded_from_bet_id: UUID | None`
  - `cascaded_at_settlement_state: str | None` —
    closed-enum string from §A.6 settlement state
    (`SETTLED_WON` / `SETTLED_LOST` / `VOIDED` /
    `PROVISIONAL`). Stored as string in the payload (no
    enum import from `domain.settlement` — keeps
    `domain/promos` standalone per DR-030).
  - `cascade_path: CascadePath | None`

**`FreeBetDeployedPayload`** (`event_type_payload=
"free_bet_deployed"`):

- `deploying_bet_id: UUID` — REQUIRED. The bet record
  consuming the FB.
- `source_credit_event_ids: list[UUID]` — REQUIRED,
  non-empty. The credit events being drawn down (many-
  to-many junction).
- `draw_down_breakdown: list[dict[str, object]]` —
  REQUIRED, non-empty. Per Slice 4: array of
  `{credit_event_id: UUID, amount_drawn: Decimal}` shapes.
  Pydantic validates the list-of-dicts shape at the
  payload validator (custom validator; see §5.2.5).
- `total_deployed: Decimal` — REQUIRED, `gt=Decimal("0")`.
  Sum of `draw_down_breakdown` amounts. Pydantic
  validates the sum-matches invariant at the payload
  validator.

**`FreeBetRevokedPayload`** (`event_type_payload=
"free_bet_revoked"`):

- `revoked_credit_event_id: UUID` — REQUIRED. The credit
  event being revoked. Validated at adapter write time:
  the referenced event must exist in `promo_events`,
  must have `event_type == FREE_BET_CREDITED`, and the
  current event's `supersedes_event_id` (header field)
  SHOULD point at the same value (cross-check at
  adapter; soft-coupled — payload field is authoritative,
  header `supersedes_event_id` is the inventory-
  derivation hook).
- `reason: RevocationReason` — REQUIRED.
- `reason_context: str | None` — nullable. Operator
  context for the revocation (e.g. "PointsBet email
  citing terms breach").

**`FreeBetExpiredPayload`** (`event_type_payload=
"free_bet_expired"`):

- `expired_credit_event_id: UUID` — REQUIRED. The credit
  event being expired. Same adapter-side validation as
  `revoked_credit_event_id`.
- `reason: ExpiryReason` — REQUIRED.
- `reason_context: str | None` — nullable.

**`PromoCashCreditedPayload`** (`event_type_payload=
"promo_cash_credited"`):

Symmetric with `FreeBetCreditedPayload` per §A.4. Same
field set, same validators, same cascade fields.

- `amount: Decimal` — REQUIRED, `gt=Decimal("0")`.
- `credit_source: FreeBetCreditSource` — REQUIRED. (Same
  enum; cash credits can be `triggered` or `freebie` the
  same way FBs can.)
- `status: CreditStatus` — REQUIRED.
- `triggering_bet_id: UUID | None` — REQUIRED if
  `credit_source == triggered`.
- `triggering_promo_instance_id: UUID | None` — REQUIRED
  if `credit_source == triggered`.
- `reference: str | None` — nullable.
- **Cascade fields** (all nullable, populated together):
  - `cascaded_from_bet_id: UUID | None`
  - `cascaded_at_settlement_state: str | None`
  - `cascade_path: CascadePath | None`

**Note on cash credit revocation:** per S130 Cat 5
software call, there is no `promo_cash_revoked` event
type. Cash credit revocations are written as NEW
`promo_cash_credited` events with `status='rejected'` and
`supersedes_event_id` pointing at the prior credit event.
The asymmetry with FB pattern is acknowledged; future
architecture amendment can add a dedicated revocation
event type cleanly if it surfaces operationally.

**`AccountCareWarningRaisedPayload`** (`event_type_payload=
"accountcare_warning_raised"`):

- `warning_type_id: UUID` — REQUIRED. FK reference to
  `warning_catalogue.warning_type_id`. Validated at
  adapter write time.
- `severity_at_raise: WarningSeverity` — REQUIRED. The
  severity at the moment of raising. May differ from the
  catalogue's `severity` baseline (e.g. a specific
  instance escalating from amber to red).
- `signal_context: dict[str, object]` — REQUIRED.
  Free-form JSON-shaped dict carrying the signal that
  triggered the raise (e.g. `{"turnover_in_window":
  4523.50, "window_days": 7, "threshold": 3000.00}`).
- `commentary: str | None` — nullable. Operator's
  free-text annotation at raise time.

**`AccountCareWarningClearedPayload`** (`event_type_payload=
"accountcare_warning_cleared"`):

- `cleared_warning_event_id: UUID` — REQUIRED. The
  `accountcare_warning_raised` event being cleared.
  Validated at adapter write time: referenced event must
  exist, must have `event_type ==
  ACCOUNTCARE_WARNING_RAISED`, must share
  `account_at_book_id` with the current event (cross-
  check at adapter).
- `clearance_reason: str` — REQUIRED. Free text
  (≤500 chars; soft cap).
- `clearance_context: dict[str, object] | None` —
  nullable. Optional structured context (e.g. `{
  "follow_up_turnover": 1250.00, "weeks_since_raise":
  3}`).

#### §5.2.5 — `PromoEventBase` common event header

The base event model carrying the common header fields
plus the discriminated-union `payload` field. Mirrors
`CashFlowEventBase` exactly in structure:

```python
PromoEventPayload = Annotated[
    PromoObservedPayload
    | PromoJourneyAnnotationPayload
    | FreeBetCreditedPayload
    | FreeBetDeployedPayload
    | FreeBetRevokedPayload
    | FreeBetExpiredPayload
    | PromoCashCreditedPayload
    | AccountCareWarningRaisedPayload
    | AccountCareWarningClearedPayload,
    Field(discriminator="event_type_payload"),
]


class PromoEventBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID
    event_type: PromoEventType
    recorded_at: datetime
    occurred_at: datetime
    account_id: UUID | None = None
    book_id: UUID | None = None
    account_at_book_id: UUID | None = None
    parent_event_id: UUID | None = None
    supersedes_event_id: UUID | None = None
    payload: PromoEventPayload
    source: PromoEventSource
    correlation_id: UUID | None = None
    notes: str | None = None

    @field_validator("recorded_at", "occurred_at")
    @classmethod
    def _validate_adelaide_local(cls, value: datetime) -> datetime:
        return _ensure_adelaide_local(value)

    @model_validator(mode="after")
    def _validate_fk_nullability_per_event_type(self) -> Self:
        ...  # see §5.2.6
        return self
```

#### §5.2.6 — FK-nullability-per-event-type model validator

Following the W14 pattern (§5.1.4 of W14 brief). Each
event type has specific nullability requirements on the
three header FKs (`account_id`, `book_id`,
`account_at_book_id`). Rules per event type:

- **`promo_observed`**: `book_id` REQUIRED;
  `account_at_book_id` MAY be present (per-account
  scoped observation) or None (book-wide observation);
  `account_id` MUST be None (observations are book-side
  facts, not account-holder-side).
- **`promo_journey_annotation`**: `book_id` REQUIRED;
  `account_at_book_id` MAY be present or None per
  annotation scope; `account_id` MUST be None.
- **`free_bet_credited`**: all three FKs
  (`account_id`, `book_id`, `account_at_book_id`)
  REQUIRED. Credits are always scoped to a specific
  account-at-book.
- **`free_bet_deployed`**: all three FKs REQUIRED.
  Deployments are scoped to the deploying bet's
  account-at-book.
- **`free_bet_revoked`**: all three FKs REQUIRED.
  Revocations inherit scope from the credit they revoke.
- **`free_bet_expired`**: all three FKs REQUIRED.
  Expiries inherit scope from the credit they expire.
- **`promo_cash_credited`**: all three FKs REQUIRED.
- **`accountcare_warning_raised`**:
  `account_at_book_id` REQUIRED; `account_id` REQUIRED
  (denormalised for read-side scope filtering — same
  account-at-book → account FK pattern as W14's
  `account_at_book_deposit`); `book_id` REQUIRED
  (denormalised for read-side book-scoped reads).
- **`accountcare_warning_cleared`**: same as raised
  (all three REQUIRED).

The validator raises `ValueError` with a clear message
when rules are violated. Pydantic's
`@model_validator(mode='after')` runs once after all
field-level validators; pattern matches W14.

Additional cross-field validators on payloads (declared
on the payload subclass via `@model_validator`):

- **`FreeBetCreditedPayload._validate_triggered_fields`**:
  if `credit_source == triggered`, both `triggering_bet_id`
  and `triggering_promo_instance_id` MUST be non-None.
  If `credit_source == freebie`, both MUST be None.
- **`PromoCashCreditedPayload._validate_triggered_fields`**:
  same cross-field rule as above.
- **`FreeBetCreditedPayload._validate_cascade_fields`**: the
  three cascade fields (`cascaded_from_bet_id`,
  `cascaded_at_settlement_state`, `cascade_path`) must
  all be either all-None or all-populated. Mixed
  state raises `ValueError`. Same validator on
  `PromoCashCreditedPayload`.
- **`FreeBetDeployedPayload._validate_drawdown_breakdown`**:
  the `draw_down_breakdown` list must be non-empty; each
  entry must have `{credit_event_id, amount_drawn}` keys
  with `amount_drawn > 0`; the sum of `amount_drawn`
  across entries must equal `total_deployed` exactly
  (Decimal comparison, no tolerance — operator-supplied
  values should match by construction).

#### §5.2.7 — `PAYLOAD_BY_EVENT_TYPE` dispatch table

The nine-entry dispatch table mirroring
`domain/cash_flow/__init__.py`. Maps `PromoEventType`
values to payload subclasses. Used by the adapter's
`_row_to_event` helper to find the right payload class
when parsing JSON.

```python
PAYLOAD_BY_EVENT_TYPE: dict[
    PromoEventType, type[PromoEventPayload]
] = {
    PromoEventType.PROMO_OBSERVED: PromoObservedPayload,
    PromoEventType.PROMO_JOURNEY_ANNOTATION:
        PromoJourneyAnnotationPayload,
    PromoEventType.FREE_BET_CREDITED:
        FreeBetCreditedPayload,
    PromoEventType.FREE_BET_DEPLOYED:
        FreeBetDeployedPayload,
    PromoEventType.FREE_BET_REVOKED:
        FreeBetRevokedPayload,
    PromoEventType.FREE_BET_EXPIRED:
        FreeBetExpiredPayload,
    PromoEventType.PROMO_CASH_CREDITED:
        PromoCashCreditedPayload,
    PromoEventType.ACCOUNTCARE_WARNING_RAISED:
        AccountCareWarningRaisedPayload,
    PromoEventType.ACCOUNTCARE_WARNING_CLEARED:
        AccountCareWarningClearedPayload,
}
```

#### §5.2.8 — Reference data models

Three Pydantic v2 models for the reference tables.

**`PromoTemplate`**:

- `promo_template_id: UUID`
- `name: str`
- `kind: PromoTemplateKind`
- `mechanic_description: str`
- `default_terms: dict[str, object] | None` (parsed from
  JSON column at adapter level)
- `notes: str | None`
- `created_at: datetime`
- `updated_at: datetime`

Adelaide-tz validation on `created_at` / `updated_at`.

**`Promo`** (per-promo instance):

- `promo_id: UUID`
- `promo_template_id: UUID` (validated existence at
  adapter write time)
- `book_id: UUID` (validated existence at adapter write
  time against W11 `books` table; soft-coupled at the
  Python layer, hard-coupled at SQL via the
  `promo.book_id` FK)
- `instance_label: str`
- `status: PromoStatus`
- `start_date: datetime`
- `end_date: datetime | None`
- `notes: str | None`
- `created_at: datetime`
- `updated_at: datetime`

Adelaide-tz validation on the four datetime fields.

**`WarningCatalogueEntry`**:

- `warning_type_id: UUID`
- `label: str`
- `severity: WarningSeverity`
- `description: str`
- `default_clearance_criteria: str | None`
- `notes: str | None`
- `created_at: datetime`
- `updated_at: datetime`

Adelaide-tz validation on `created_at` / `updated_at`.

#### §5.2.9 — Imports

`domain/promos/__init__.py` imports stdlib + Pydantic
only per DR-030. Concretely:

```python
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
```

No project imports. DR-030 holds.

---
### §5.3 — Repository (`store/repositories/promos.py`)

Four row-only repository classes, all in one module per
the W14.1 precedent (`store/repositories/cash_flow.py`
holds both `CashFlowEventRepository` and
`PayeeRepository`). Mirrors W14.1's shape exactly: row
dataclasses, repository classes taking
`sqlite3.Connection`, row-level methods using `object`
for ID types, `_promo_event_type_value` helper for
enum-vs-string normalisation, supersession-aware LEFT
JOIN reads.

**Critical: NO `domain.promos` imports.** DR-030 holds
from session one. The repository uses `object` typing
plus the per-module helper for any enum-vs-string
normalisation; Pydantic types live exclusively at the
adapter layer.

Expected file size: ~700–900 lines (larger than W14.1's
601 because four repository classes vs two — plus the
event repository surface itself is bigger).

#### §5.3.1 — Row dataclasses

Four frozen `@dataclass` classes mirroring SQL columns
one-for-one. Pattern matches W14.1.

**`PromoEventRow`**: 13 fields matching `promo_events`
DDL (§5.1.4):

```python
@dataclass(frozen=True)
class PromoEventRow:
    event_id: str
    event_type: str
    recorded_at: str
    occurred_at: str
    account_id: str | None
    book_id: str | None
    account_at_book_id: str | None
    parent_event_id: str | None
    supersedes_event_id: str | None
    payload: str  # JSON-serialised
    source: str
    correlation_id: str | None
    notes: str | None
```

**`PromoTemplateRow`**: 8 fields matching
`promo_template` DDL:

```python
@dataclass(frozen=True)
class PromoTemplateRow:
    promo_template_id: str
    name: str
    kind: str
    mechanic_description: str
    default_terms: str | None  # JSON-serialised
    notes: str | None
    created_at: str
    updated_at: str
```

**`PromoRow`**: 10 fields matching `promo` DDL:

```python
@dataclass(frozen=True)
class PromoRow:
    promo_id: str
    promo_template_id: str
    book_id: str
    instance_label: str
    status: str
    start_date: str
    end_date: str | None
    notes: str | None
    created_at: str
    updated_at: str
```

**`WarningCatalogueRow`**: 8 fields matching
`warning_catalogue` DDL:

```python
@dataclass(frozen=True)
class WarningCatalogueRow:
    warning_type_id: str
    label: str
    severity: str
    description: str
    default_clearance_criteria: str | None
    notes: str | None
    created_at: str
    updated_at: str
```

#### §5.3.2 — Error classes

Module-level exceptions per the W14.1 precedent. Two
hierarchies — one for events, one for reference data
(since the reference data errors map to a different
operator-shape concern).

**Event errors:**

```python
class PromoEventError(Exception):
    """Base for promo event repository errors."""


class DuplicatePromoEventError(PromoEventError):
    """Event with this event_id already exists."""


class PromoEventNotFoundError(PromoEventError):
    """No event found for this event_id."""


class PromoSupersessionCycleError(PromoEventError):
    """Cycle detected in supersession chain."""


class PromoInvalidScopeError(PromoEventError):
    """At least one scope filter required for the
    requested read."""
```

**Reference data errors:**

```python
class PromoReferenceError(Exception):
    """Base for promo reference data repository errors."""


class DuplicateReferenceEntityError(PromoReferenceError):
    """Reference entity with this id already exists."""


class ReferenceEntityNotFoundError(PromoReferenceError):
    """No reference entity found for this id."""
```

Pattern matches W14.1 — separate hierarchies for distinct
operator-shape concerns. All shared error names use
`Promo*` prefix to avoid clash with W14's
`CashFlowEvent*` errors.

#### §5.3.3 — `_promo_event_type_value` helper

Per the W14.1 v3 convention (the loose-typing surface
finding (b) locked at S129). Module-level helper that
normalises enum-vs-string at the boundary:

```python
def _promo_event_type_value(value: object) -> str:
    """Normalise enum-or-string event_type values to string.

    Per W14.1 v3 convention (finding (b) locked S129):
    repository surface accepts `object` for ID types
    that live in `domain/`, with a per-repository helper
    for enum-vs-string normalisation. Repository remains
    DR-030 compliant (no `domain.promos` imports); the
    adapter handles all Pydantic translation.

    Accepts: PromoEventType enum (via `.value` duck-typing),
    raw string. Returns: raw string suitable for SQL
    parameters.
    """

    if hasattr(value, "value"):
        return str(value.value)
    return str(value)
```

Identical shape to W14.1's `_event_type_value` (in
`store/repositories/cash_flow.py`). Used by every
event-type-accepting method in `PromoEventRepository`.

#### §5.3.4 — `PromoEventRepository` class

Append-only row writes plus scoped / supersession-aware
row reads. Mirrors W14.1's `CashFlowEventRepository`
exactly in method shape; field names and FK targets
differ per the schema.

**Constructor:**

```python
def __init__(self, conn: sqlite3.Connection) -> None:
    self._conn = conn
    self._conn.row_factory = sqlite3.Row
    self._conn.execute("PRAGMA foreign_keys = ON;")
    apply_migrations(self._conn)
```

Same as W14.1's pattern; idempotent migration on init.

**Write surface:**

- `append_row(row: PromoEventRow) -> str` — INSERT into
  `promo_events`, returns `event_id`. Raises
  `DuplicatePromoEventError` on PK collision;
  `PromoEventError` wrapping the underlying message on
  other `sqlite3.IntegrityError` (FK violations against
  W11 tables; self-FK violations on
  `parent_event_id` / `supersedes_event_id`).

**Read surface — single events:**

- `get_row(event_id: object) -> PromoEventRow` —
  fetches by `event_id`. Raises
  `PromoEventNotFoundError`. `object` typing per W14.1
  convention.

**Read surface — list reads (row-level):**

Same shape as W14.1, four list-by-scope methods plus
correlation:

- `list_rows_by_account_at_book(account_at_book_id:
  object, event_type: object | None = None, limit: int
  = 1000, offset: int = 0) -> list[PromoEventRow]`
- `list_rows_by_account(...)` — same signature
- `list_rows_by_book(...)` — same signature
- `list_rows_by_event_type(event_type: object, limit:
  int = 1000, offset: int = 0) ->
  list[PromoEventRow]` — analytics scan
- `list_rows_by_correlation_id(correlation_id: object)
  -> list[PromoEventRow]` — all events sharing a
  correlation, no pagination

All reads order by `(recorded_at ASC, event_id ASC)`.
Internal `_list_scoped` helper shared across the
account-at-book / account / book reads, identical
pattern to W14.1.

**Read surface — supersession-aware:**

- `latest_non_superseded_rows_by_scope(
  account_at_book_id: object | None = None,
  account_id: object | None = None,
  book_id: object | None = None,
  event_type: object | None = None,
  ) -> list[PromoEventRow]` — LEFT JOIN
  `promo_events` self on `supersedes_event_id`, filter
  where the join is NULL. Raises
  `PromoInvalidScopeError` if all four scope filters
  are None.
- `walk_supersession_chain_rows(event_id: object) ->
  list[PromoEventRow]` — walks supersession pointers
  backwards; returns chain earliest-first. Raises
  `PromoSupersessionCycleError` on cycles,
  `PromoEventNotFoundError` if starting id is unknown.

Implementation logic is row-for-row identical to
W14.1's `CashFlowEventRepository` — same SQL shapes,
same LEFT JOIN structure, same cycle-detection loop.
Code reuses the W14.1 implementation pattern verbatim
with the table name swap.

#### §5.3.5 — `PromoTemplateRepository` class

Standard row-level CRUD against `promo_template`. No
delete method (a deleted template would orphan
historical `promo_observed` events; same defence as
W14.1's `PayeeRepository`).

**Constructor:** takes `sqlite3.Connection`, same pattern
as `PromoEventRepository`.

**Methods:**

- `create_row(row: PromoTemplateRow) -> str` — INSERT.
  Raises `DuplicateReferenceEntityError` on PK collision.
- `get_row(promo_template_id: object) ->
  PromoTemplateRow` — fetch. Raises
  `ReferenceEntityNotFoundError`.
- `update_row(promo_template_id: object, *, name: str |
  None = None, kind: object | None = None,
  mechanic_description: str | None = None,
  default_terms: str | None = None, notes: str | None
  = None, updated_at: str) -> PromoTemplateRow` —
  partial update; `None` keeps existing value;
  `updated_at` REQUIRED (adapter computes Adelaide-local).
- `list_rows(kind: object | None = None) ->
  list[PromoTemplateRow]` — all templates, optionally
  filtered by `kind`. Ordered by `name ASC`.

#### §5.3.6 — `PromoRepository` class

Standard row-level CRUD against `promo`.

**Constructor:** takes `sqlite3.Connection`.

**Methods:**

- `create_row(row: PromoRow) -> str` — INSERT. Raises
  `DuplicateReferenceEntityError` on PK collision; raises
  `PromoReferenceError` wrapping IntegrityError on FK
  violation against `promo_template` or `books`.
- `get_row(promo_id: object) -> PromoRow` — fetch.
- `update_row(promo_id: object, *, instance_label: str |
  None = None, status: object | None = None, end_date:
  str | None = None, notes: str | None = None,
  updated_at: str) -> PromoRow` — partial update.
  `promo_template_id`, `book_id`, and `start_date` are
  not updatable (changing them would break historical
  reference integrity). Operator can deactivate via
  `status='discontinued'` and create a fresh promo
  instance for the new mechanic.
- `list_rows(promo_template_id: object | None = None,
  book_id: object | None = None, status: object | None
  = None) -> list[PromoRow]` — all promos, optionally
  filtered. Ordered by `(start_date DESC, promo_id ASC)`
  (most recent first — operator's typical access
  pattern).

#### §5.3.7 — `WarningCatalogueRepository` class

Standard row-level CRUD against `warning_catalogue`. No
delete (same orphan-events defence).

**Constructor:** takes `sqlite3.Connection`.

**Methods:**

- `create_row(row: WarningCatalogueRow) -> str` —
  INSERT.
- `get_row(warning_type_id: object) ->
  WarningCatalogueRow` — fetch.
- `update_row(warning_type_id: object, *, label: str |
  None = None, severity: object | None = None,
  description: str | None = None,
  default_clearance_criteria: str | None = None,
  notes: str | None = None, updated_at: str) ->
  WarningCatalogueRow` — partial update.
- `list_rows(severity: object | None = None) ->
  list[WarningCatalogueRow]` — all entries, optionally
  filtered by severity. Ordered by `label ASC`.

#### §5.3.8 — Internal helpers

Module-level row-conversion helpers, one per row type
(four helpers total). Pattern matches W14.1's
`_row_to_cash_flow_event_row` /
`_row_to_payee_row`:

- `_row_to_promo_event_row(sqlite_row: sqlite3.Row) ->
  PromoEventRow`
- `_row_to_promo_template_row(sqlite_row: sqlite3.Row)
  -> PromoTemplateRow`
- `_row_to_promo_row(sqlite_row: sqlite3.Row) ->
  PromoRow`
- `_row_to_warning_catalogue_row(sqlite_row:
  sqlite3.Row) -> WarningCatalogueRow`

Plus the shared `_promo_event_type_value` helper from
§5.3.3.

#### §5.3.9 — Imports

Module-level imports stay strictly within Cat-3
boundaries:

```python
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from store.schema.promos import apply_migrations
```

No `domain.promos` imports. No other project imports.
DR-030 holds.

---
### §5.4 — Adapter (`workflows/promos/v1/promo_store_adapter.py`)

The new adapter owns all Pydantic ↔ row translation
plus the adapter-side payload-reference validation
(`promo_template_id` existence check on
`promo_observed`; `warning_type_id` existence check on
`accountcare_warning_*`; etc.). Mirrors W14.1's
`cash_flow_store_adapter.py` (396 lines) in shape;
larger because of more event types plus three reference
data CRUD surfaces.

Expected file size: ~500–700 lines.

#### §5.4.1 — Constructor and underlying repositories

```python
class PromoStoreAdapter:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._events = PromoEventRepository(conn)
        self._templates = PromoTemplateRepository(conn)
        self._promos = PromoRepository(conn)
        self._warning_catalogue = WarningCatalogueRepository(conn)
```

One connection, four underlying repositories. The shared
`apply_migrations` runs once at the first repository
construction (idempotent).

#### §5.4.2 — Event write surface

**`append_event(event: PromoEventBase) -> UUID`** —
takes a Pydantic event, runs adapter-side payload
reference validation (see §5.4.3), serialises the
payload via `event.payload.model_dump_json()`, converts
typed fields to row primitives, builds a
`PromoEventRow`, calls `self._events.append_row(row)`,
returns `event.event_id`.

Errors from the repository propagate unchanged.
`PromoReferenceValidationError` (defined at the adapter
layer; see §5.4.6) raises if a payload reference fails
existence check.

#### §5.4.3 — Adapter-side payload reference validation

Per the §1.3 Cat 5 software call (`promo_template_id` /
`warning_type_id` payload references validated at
adapter layer, not at SQL FK). The adapter checks
referenced rows exist before writing the event.

**Per event type:**

- `promo_observed`: payload's `promo_template_id` must
  exist in `promo_template`. Adapter calls
  `self._templates.get_row(payload.promo_template_id)`;
  catches `ReferenceEntityNotFoundError` and re-raises
  as `PromoReferenceValidationError` with clear message
  citing the missing reference.
- `promo_journey_annotation`: same as `promo_observed`
  for the payload's `promo_template_id`.
- `free_bet_credited` (triggered path):
  `triggering_promo_instance_id` must exist in
  `promo`. Adapter calls
  `self._promos.get_row(payload.triggering_promo_instance_id)`.
  `triggering_bet_id` is NOT validated at adapter (W13
  cannot see the `bets` table from
  `workflows/promos/v1/`; the bet-record reference is
  soft-coupled and validated at burst-review-time).
- `free_bet_revoked`: `revoked_credit_event_id` payload
  reference must exist in `promo_events` AND must have
  `event_type == FREE_BET_CREDITED`. Adapter calls
  `self._events.get_row(payload.revoked_credit_event_id)`
  and asserts the returned row's `event_type` matches.
- `free_bet_expired`: same as `free_bet_revoked` for
  `expired_credit_event_id`.
- `promo_cash_credited` (triggered path): same as
  `free_bet_credited` (triggered) for
  `triggering_promo_instance_id`.
- `accountcare_warning_raised`: `warning_type_id` must
  exist in `warning_catalogue`.
- `accountcare_warning_cleared`: `cleared_warning_event_id`
  must exist in `promo_events` AND have
  `event_type == ACCOUNTCARE_WARNING_RAISED` AND share
  `account_at_book_id` with the current event.

Helper:

```python
def _validate_payload_references(
    self, event: PromoEventBase
) -> None:
    """Adapter-side existence and type checks on payload
    reference IDs per §5.4.3 of W13 brief."""
    ...
```

Called from `append_event` before
`self._events.append_row(...)`. Raises
`PromoReferenceValidationError` (defined at the adapter
module level; see §5.4.6) on any missing or mistyped
reference.

#### §5.4.4 — Event read surface — single events and lists

Mirrors W14.1's adapter shape one-for-one with the
table name swap. Eight public read methods:

- `get_event(event_id: UUID) -> PromoEventBase`
- `list_by_account_at_book(account_at_book_id: UUID,
  event_type: PromoEventType | None = None, limit: int
  = 1000, offset: int = 0) -> list[PromoEventBase]`
- `list_by_account(account_id: UUID, ...) ->
  list[PromoEventBase]` — same signature shape
- `list_by_book(book_id: UUID, ...) ->
  list[PromoEventBase]` — same
- `list_by_event_type(event_type: PromoEventType,
  limit: int = 1000, offset: int = 0) ->
  list[PromoEventBase]`
- `list_by_correlation_id(correlation_id: UUID) ->
  list[PromoEventBase]`
- `latest_non_superseded_by_scope(
  account_at_book_id: UUID | None = None,
  account_id: UUID | None = None,
  book_id: UUID | None = None,
  event_type: PromoEventType | None = None,
  ) -> list[PromoEventBase]` — `PromoInvalidScopeError`
  propagates
- `walk_supersession_chain(event_id: UUID) ->
  list[PromoEventBase]` — `PromoSupersessionCycleError`
  and `PromoEventNotFoundError` propagate

All return Pydantic models via `_row_to_event` helper
(see §5.4.7).

#### §5.4.5 — Reference data CRUD at adapter

Three sub-surfaces — one for each reference table.
Pattern mirrors W14.1's `Payee` CRUD methods on
`CashFlowStoreAdapter`.

**Template surface:**

- `create_template(template: PromoTemplate) -> UUID` —
  Pydantic in, row translation, delegates to
  `self._templates.create_row(...)`.
- `get_template(promo_template_id: UUID) ->
  PromoTemplate` — `ReferenceEntityNotFoundError`
  propagates.
- `update_template(promo_template_id: UUID, *, name:
  str | None = None, kind: PromoTemplateKind | None =
  None, mechanic_description: str | None = None,
  default_terms: dict[str, object] | None = None,
  notes: str | None = None, updated_at: datetime | None
  = None) -> PromoTemplate` — adapter computes
  Adelaide-local `updated_at` if not supplied.
  `default_terms` accepted as dict; adapter serialises
  to JSON string for the row.
- `list_templates(kind: PromoTemplateKind | None = None)
  -> list[PromoTemplate]`

**Promo surface:**

- `create_promo(promo: Promo) -> UUID` — adapter checks
  `promo.promo_template_id` exists in `promo_template`
  before delegating (avoid the deeper IntegrityError
  with a clearer adapter-side error). `book_id`
  existence check happens at SQL FK enforcement (W11
  `books` table; the IntegrityError surfaces as
  `PromoReferenceError`).
- `get_promo(promo_id: UUID) -> Promo`
- `update_promo(promo_id: UUID, *, instance_label: str |
  None = None, status: PromoStatus | None = None,
  end_date: datetime | None = None, notes: str | None
  = None, updated_at: datetime | None = None) -> Promo`
- `list_promos(promo_template_id: UUID | None = None,
  book_id: UUID | None = None, status: PromoStatus |
  None = None) -> list[Promo]`

**Warning catalogue surface:**

- `create_warning_type(entry: WarningCatalogueEntry) ->
  UUID`
- `get_warning_type(warning_type_id: UUID) ->
  WarningCatalogueEntry`
- `update_warning_type(warning_type_id: UUID, *, label:
  str | None = None, severity: WarningSeverity | None
  = None, description: str | None = None,
  default_clearance_criteria: str | None = None,
  notes: str | None = None, updated_at: datetime |
  None = None) -> WarningCatalogueEntry`
- `list_warning_types(severity: WarningSeverity | None
  = None) -> list[WarningCatalogueEntry]`

All reads return Pydantic models via per-row helpers
(see §5.4.7).

#### §5.4.6 — Adapter-level error class

Only one error defined at the adapter layer; the rest
propagate from the repository.

```python
class PromoReferenceValidationError(Exception):
    """Adapter-side payload reference validation failure.

    Raised when an event's payload references a row that
    must exist in a reference table (per §5.4.3) but
    doesn't. Distinct from repository-layer
    `PromoReferenceError` (FK violation against W11
    tables) and `ReferenceEntityNotFoundError` (CRUD
    miss on a reference table itself).
    """
```

#### §5.4.7 — Module-level helpers

Row ↔ Pydantic translation helpers. Pattern mirrors
W14.1's adapter helpers:

- `_row_to_event(row: PromoEventRow) -> PromoEventBase`
  — uses `PAYLOAD_BY_EVENT_TYPE[PromoEventType(
  row.event_type)]` to find the right payload subclass,
  parses JSON via `model_validate_json`, constructs the
  `PromoEventBase`. Same `typing.cast` workaround as W14
  (mypy can't narrow through the dispatch table; runtime
  type IS the right subclass).
- `_event_to_row(event: PromoEventBase) ->
  PromoEventRow` — inverse direction. Serialises payload
  via `event.payload.model_dump_json()`, formats UUIDs
  and datetimes to strings.
- `_row_to_promo_template(row: PromoTemplateRow) ->
  PromoTemplate` — straight field translation. JSON
  parse on `default_terms` if present.
- `_template_to_row(template: PromoTemplate) ->
  PromoTemplateRow` — inverse. JSON serialise on
  `default_terms` if present.
- `_row_to_promo(row: PromoRow) -> Promo` — straight
  translation.
- `_promo_to_row(promo: Promo) -> PromoRow` — inverse.
- `_row_to_warning_catalogue(row: WarningCatalogueRow)
  -> WarningCatalogueEntry` — straight.
- `_warning_catalogue_to_row(entry:
  WarningCatalogueEntry) -> WarningCatalogueRow` —
  inverse.

#### §5.4.8 — Imports

```python
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import cast
from uuid import UUID
from zoneinfo import ZoneInfo

from domain.promos import (
    PAYLOAD_BY_EVENT_TYPE,
    PromoEventBase,
    PromoEventPayload,
    PromoEventSource,
    PromoEventType,
    PromoTemplate,
    PromoTemplateKind,
    Promo,
    PromoStatus,
    WarningCatalogueEntry,
    WarningSeverity,
)
from store.repositories.promos import (
    DuplicatePromoEventError,
    DuplicateReferenceEntityError,
    PromoEventNotFoundError,
    PromoEventRepository,
    PromoEventRow,
    PromoRepository,
    PromoRow,
    PromoTemplateRepository,
    PromoTemplateRow,
    ReferenceEntityNotFoundError,
    WarningCatalogueRepository,
    WarningCatalogueRow,
    # error class re-exports as the adapter needs them
)
```

DR-030: workflows can import from domain and store;
direction respected.

---
### §5.5 — Reference data shape (rationale and operator-side
                                   implications)

This sub-section captures the reference-table design
choices in one place for operator review.

#### §5.5.1 — Why three reference tables, not one

The three tables (`promo_template`, `promo`,
`warning_catalogue`) serve three distinct purposes:

- **`promo_template`** is the closed-set catalogue of
  promo kinds — the mechanic. "Money-back-if-2nd",
  "100%-bonus-winnings-on-win", "best-tote-or-SP",
  "EW-cashback-on-3rd". Stable; new entries added when
  a new mechanic surfaces operationally. ~10–30 rows
  forever.
- **`promo`** is the per-instance running of a template
  at a specific book in a specific window. "Sportsbet's
  money-back-if-2nd-or-3rd Spring Carnival 2026" is one
  promo instance referencing the "Money-back-if-2nd-or-3rd"
  template. Operator adds rows as cycles run; ~50–200
  per year. The DR-032 bet record's `promo_instance_id`
  FKs here.
- **`warning_catalogue`** is the closed-vocab AccountCare
  warning types per DR-015 (three-tier severity).
  "Rapid turnover spike", "Limit increase request after
  lift", "KYC follow-up". Stable; ~10–20 rows once
  populated. New warning types added when a new pattern
  surfaces.

Collapsing them would require either: (a) a generic
"reference data" table with a `type` discriminator
column (loses CHECK constraint defence per type and
makes FK targeting awkward), or (b) embedding template
data in promo rows (duplicates the mechanic across
every cycle's instance). Three-table split is the
clean shape.

#### §5.5.2 — Day-zero seeding approach

W13 ships the schema and the CRUD adapter surface. It
ships NO seed data — the tables are empty after
migration. Operator seeds three ways:

- **Operator-side SQL seed scripts** (most likely
  path): operator writes ~10–30 INSERT statements per
  table to populate the closed-set catalogues. One-time
  effort; commits the seed script under
  `bethub-v3/scripts/seed/` (folder doesn't exist yet —
  out of W13 scope, lands as a follow-up operator
  action between W13 close and W12 brief drafting).
- **Operator-side via adapter** (alternative): operator
  uses the W13 adapter's `create_template` /
  `create_warning_type` methods via a Python script
  (`scripts/seed_promos.py` style). Equivalent outcome;
  uses the Pydantic surface for validation as a sanity
  check.

Either way, W13's brief specifies the SHAPE — operator
seeds afterwards. Seeding is operator-driven, not Code's
job at W13.

#### §5.5.3 — Reference-table mutability

`promo_template` and `warning_catalogue` are
operationally append-only-plus-update; rows are added
and existing rows can have their non-key fields
updated, but rows are not deleted (delete would orphan
historical events). `promo` is also append-only-plus-
update; status transitions to `historical` or
`discontinued` replace deletion.

No `delete_*` methods on any reference repository. If a
template was created by mistake (operator typo), the
remediation is `update_row` to fix the fields or
`status='discontinued'` on `promo` instances. The
adapter exposes update surfaces accordingly.

#### §5.5.4 — Cross-domain FK chain visualised

```
warning_catalogue
        ↑
        │ FK (payload-side, adapter-validated)
        │
promo_events  ←──── account_at_book, account, book (W11)
        ↑
        │ FK (header self-FK; supersession + parent
        │  chains)
        │
promo_events (self)

promo_template
        ↑
        │ FK (SQL-enforced via promo.promo_template_id)
        │
promo  ←─────────── book (W11)
        ↑
        │ FK (payload-side, adapter-validated, on
        │  free_bet_credited.triggering_promo_instance_id
        │  and promo_cash_credited.triggering_promo_instance_id)
        │
promo_events
```

Two SQL-enforced FKs (`promo.promo_template_id` and
`promo.book_id`). Three SQL-enforced FKs on
`promo_events` header (`account_id`, `book_id`,
`account_at_book_id`). All other reference linkages
flow through payload JSON and are validated at the
adapter layer per §5.4.3.

---
### §5.6 — Tests (three-way split per W14.1 convention)

W13 ships three test files at the W14.1-locked layout:

- `tests/store/repositories/test_promos_schema.py` —
  DDL, migration, CHECK constraint, FK constraint tests
  across all four tables.
- `tests/store/repositories/test_promos_repository.py` —
  row-level repository tests across all four
  repositories (events + 3 reference tables).
- `tests/workflows/promos/v1/test_promo_store_adapter.py`
  — adapter-level Pydantic tests.

Estimated total: ~90–115 tests across the three files,
~2x W14.1's net 75 cash-flow tests (since W13 has more
event types and three reference tables).

#### §5.6.1 — `test_promos_schema.py`

Estimated ~20–25 tests. Pattern mirrors
`test_cash_flow_schema.py`:

- `test_apply_migrations_creates_all_four_tables` —
  asserts the four CREATE TABLE statements landed
  cleanly. Reads `sqlite_master` for table presence.
- `test_apply_migrations_creates_indexes` — asserts all
  10 indexes present.
- `test_apply_migrations_idempotent` — calls
  `apply_migrations` twice; second is no-op (no errors,
  no duplicates).
- `test_event_type_check_constraint` — asserts the nine
  closed-vocab values are accepted and an invalid value
  raises `IntegrityError`.
- `test_source_check_constraint` — three closed-vocab
  values accepted; invalid rejected.
- `test_promo_template_kind_check_constraint` — five
  values accepted; invalid rejected.
- `test_promo_status_check_constraint` — three values
  accepted; invalid rejected.
- `test_warning_catalogue_severity_check_constraint` —
  three values accepted; invalid rejected.
- `test_promo_events_fk_constraints_to_w11_tables` —
  inserting a row with `account_id` / `book_id` /
  `account_at_book_id` not present in W11 raises
  `IntegrityError`.
- `test_promo_events_self_referential_fk_parent_event`
  — `parent_event_id` must reference an existing
  `promo_events.event_id`.
- `test_promo_events_self_referential_fk_supersedes_event`
  — same shape for `supersedes_event_id`.
- `test_promo_fk_to_promo_template` — invalid
  `promo_template_id` on `promo` raises `IntegrityError`.
- `test_promo_fk_to_w11_book` — invalid `book_id` on
  `promo` raises `IntegrityError`.
- `test_warning_catalogue_no_fk` — `warning_type_id`
  values referenced in payloads have no SQL FK
  constraint; documented behaviour.

#### §5.6.2 — `test_promos_repository.py`

Estimated ~35–45 tests. Pattern mirrors
`test_cash_flow_repository.py` with W13's extra
repository classes. Test fixtures use `tmp_path`-backed
SQLite with W11 + W13 migrations applied; per-test
seed of W11 accounts / books / accounts_at_book as
needed.

**`PromoEventRepository` tests (~20–25 tests):**

- `test_append_row_returns_event_id` — basic append.
- `test_append_duplicate_event_id_raises_duplicate_event`
  — `DuplicatePromoEventError`.
- `test_append_each_event_type_row_round_trips`
  (parametrised, nine cases) — constructs a row with
  appropriate payload JSON for each event type,
  appends, fetches the row back, asserts row equality.
  Mirrors W14's parametrised round-trip test.
- `test_get_row_not_found_raises` —
  `PromoEventNotFoundError`.
- `test_list_rows_by_account_at_book_paginates`,
  `test_list_rows_by_account_at_book_filters_by_event_type`,
  `test_list_rows_by_correlation_id_returns_full_cycle`,
  `test_list_rows_by_event_type_scans_table`,
  `test_list_rows_by_book`,
  `test_list_rows_by_account`.
- `test_latest_non_superseded_rows_excludes_superseded`,
  `test_walk_supersession_chain_rows`,
  `test_supersession_cycle_detected_at_row_level`,
  `test_latest_non_superseded_requires_scope`
  (`PromoInvalidScopeError`).
- `test_fk_violation_account_id_raises` /
  `test_fk_violation_book_id_raises` /
  `test_fk_violation_account_at_book_id_raises` —
  ghost FK targets wrap to `PromoEventError`.

**`PromoTemplateRepository` tests (~5–8 tests):**

- `test_create_row_returns_id`,
  `test_create_duplicate_raises_duplicate_reference`,
  `test_get_row_returns_template`,
  `test_get_row_not_found_raises`,
  `test_update_row_partial_fields`,
  `test_list_rows_filters_by_kind`,
  `test_list_rows_ordered_by_name_asc`.

**`PromoRepository` tests (~5–8 tests):**

- `test_create_row_returns_id`,
  `test_create_with_missing_template_raises_reference_error`
  (FK to `promo_template` invalid),
  `test_create_with_missing_book_raises_reference_error`
  (FK to W11 `books` invalid),
  `test_get_row_returns_promo`,
  `test_update_row_partial_fields`,
  `test_list_rows_filters_by_template_book_status`,
  `test_list_rows_ordered_by_start_date_desc`.

**`WarningCatalogueRepository` tests (~5–8 tests):**

- `test_create_row_returns_id`,
  `test_create_duplicate_raises`,
  `test_get_row_returns_entry`,
  `test_update_row_partial_fields`,
  `test_list_rows_filters_by_severity`,
  `test_list_rows_ordered_by_label_asc`.

#### §5.6.3 — `test_promo_store_adapter.py`

Estimated ~35–45 tests. Pattern mirrors
`test_cash_flow_store_adapter.py`. Tests exercise the
Pydantic-side: discriminated-union round-trip per event
type, FK-nullability validation, Adelaide tz validation,
adapter-side payload reference validation, supersession-
aware reads returning Pydantic types, reference data
CRUD round-trips.

**Event-level tests (~25–30):**

- `test_append_event_via_adapter_round_trips`
  (parametrised, nine cases) — for each event type,
  construct a valid `PromoEventBase` with the
  appropriate payload subclass, append, fetch via
  `get_event`, assert `type(fetched.payload) is
  type(event.payload)` and field equality.
- FK-nullability tests per event type (nine tests) —
  each constructs an event with the wrong combination
  of header FKs (account_id / book_id /
  account_at_book_id), asserts `ValidationError` on
  Pydantic construction.
- Cross-field validator tests on payloads:
  `test_free_bet_credited_triggered_requires_both_fks`
  (both `triggering_bet_id` and
  `triggering_promo_instance_id` must be non-None or
  both None per credit_source),
  `test_free_bet_credited_freebie_forbids_both_fks`,
  `test_promo_cash_credited_triggered_requires_both_fks`,
  `test_cascade_fields_all_or_nothing` (on both credit
  payload types).
- `test_free_bet_deployed_drawdown_sum_must_match`,
  `test_free_bet_deployed_drawdown_breakdown_non_empty`,
  `test_free_bet_deployed_amount_positive`.
- Adelaide tz tests: `test_naive_datetime_rejected`,
  `test_non_adelaide_tz_rejected`,
  `test_acdt_daylight_saving_accepted`.
- Read-path Pydantic tests:
  `test_get_event_returns_pydantic_model`,
  `test_list_by_account_at_book_returns_pydantic_models`,
  `test_list_by_account`, `test_list_by_book`,
  `test_list_by_event_type`,
  `test_list_by_correlation_id_returns_full_cycle_in_pydantic`.
- Supersession-aware Pydantic tests:
  `test_latest_non_superseded_via_adapter_excludes_superseded`,
  `test_walk_supersession_chain_returns_pydantic_models`,
  `test_invalid_scope_raises_via_adapter`.
- Adapter-side payload reference validation tests
  (one per event type with payload reference):
  `test_promo_observed_missing_template_raises_reference_validation`,
  `test_free_bet_credited_triggered_missing_promo_raises`,
  `test_free_bet_revoked_missing_credit_event_raises`,
  `test_free_bet_revoked_wrong_event_type_raises`,
  `test_free_bet_expired_missing_credit_event_raises`,
  `test_accountcare_warning_raised_missing_warning_type_raises`,
  `test_accountcare_warning_cleared_missing_raise_event_raises`,
  `test_accountcare_warning_cleared_account_at_book_mismatch_raises`.

**Reference data CRUD tests at adapter (~10–15):**

- Template surface: `test_create_template_round_trips`,
  `test_get_template_returns_pydantic`,
  `test_update_template_advances_updated_at`,
  `test_update_template_partial_field_semantics`,
  `test_list_templates_filters_by_kind`.
- Promo surface: `test_create_promo_round_trips`,
  `test_create_promo_with_missing_template_raises_reference_validation`,
  `test_get_promo_returns_pydantic`,
  `test_update_promo_advances_updated_at`,
  `test_list_promos_filters_by_template_book_status`.
- Warning catalogue: `test_create_warning_type_round_trips`,
  `test_get_warning_type_returns_pydantic`,
  `test_update_warning_type_advances_updated_at`,
  `test_list_warning_types_filters_by_severity`.

#### §5.6.4 — Shared test fixtures

Same pattern as W14.1's adapter tests:

- `tmp_path`-backed SQLite via `tmp_path / "test.db"`
  fixtures.
- Helper functions per-test-file (private; not in
  `tests/conftest.py`):
  - `_seed_w11_accounts(conn)` — creates one account,
    book, account-at-book for FK targets.
  - `_seed_promo_reference_data(conn)` — creates one
    `promo_template`, one `promo`, one
    `warning_catalogue` entry as default reference
    targets for adapter tests.
  - `_build_event(event_type, **overrides)` —
    parametrised event constructor for round-trip
    tests.
  - `_common(event_type, payload, **overrides)` —
    common-header field builder with sensible defaults.

`tests/conftest.py` stays untouched (per W14.1
convention — keep shared fixtures per-file rather than
global).

#### §5.6.5 — Test count target

Net new tests: ~90–115 across the three files. Code
adds or drops where the surface warrants and surfaces
the actual count in the report. Total test count in
`tests/store/repositories/` plus
`tests/workflows/promos/v1/` post-W13: ≥ 90 new (no
regression on W14.1's 75 cash-flow tests; small
expansion expected as fixtures shake out).

---
## §6 — Sequencing within session

### §6.1 — Pre-build codebase alignment check (operator-
                requested)

Before any substantive edits land, Code runs a
**codebase alignment pass** against the shipped W14.1
substrate. Pattern lifted from W14.1 brief §6.1; this
brief explicitly carries it per operator request at
S130 pre-draft.

The goal: catch any divergence between brief
assumptions and shipped substrate BEFORE editing
anything. Cheap insurance — ~10 minutes of session
budget — against expensive rework if a brief assumption
turns out stale.

Six checks, in order:

1. **W14.1 adapter shape matches brief reference.**
   Read `bethub-v3/workflows/cash_flow/v1/cash_flow_store_adapter.py`
   end-to-end. Confirm the structural shape W13's
   adapter inherits is what the brief describes:
   class taking `sqlite3.Connection`, public methods
   returning Pydantic, module-level `_row_to_*` /
   `_*_to_row` helpers, `typing.cast` workaround on
   the dispatch parse.
   - Pass condition: file present at the expected path
     with the shape `§5.4` describes. Brief assumption
     holds.
   - Surface as ALIGNMENT-FINDING-A if absent or
     structurally different.

2. **W14.1 row-only repository shape matches brief
   reference.** Read
   `bethub-v3/store/repositories/cash_flow.py`
   end-to-end. Confirm `CashFlowEventRepository` and
   `PayeeRepository` ship row-only with `object` type
   hints and the `_event_type_value` helper.
   - Pass condition: row dataclasses present, no
     `domain.cash_flow` imports in the module, helper
     pattern matches.
   - Surface as ALIGNMENT-FINDING-B if domain imports
     present or helper missing.

3. **W14 domain layer shape matches brief reference.**
   Read `bethub-v3/domain/cash_flow/__init__.py`
   end-to-end. Confirm closed-enum + `_PayloadBase` +
   per-event-type `_Payload` subclass +
   `event_type_payload` literal discriminator +
   FK-nullability `@model_validator` +
   `PAYLOAD_BY_EVENT_TYPE` dispatch all present.
   - Pass condition: module structure matches the
     pattern W13 inherits.
   - Surface as ALIGNMENT-FINDING-C if structural
     drift.

4. **W14 schema module shape matches brief reference.**
   Read `bethub-v3/store/schema/cash_flow.py`
   end-to-end. Confirm DDL constants, indexes,
   `_add_column_if_missing` helper, `apply_migrations`
   function pattern.
   - Pass condition: module structure matches.
   - Surface as ALIGNMENT-FINDING-D if drift.

5. **W11 tables present and FK-ready.** Read
   `bethub-v3/store/schema/accounts.py` (W11 schema).
   Confirm `accounts`, `books`, `accounts_at_book`
   tables defined with PK columns matching what W13's
   `promo_events` FK targets require
   (`accounts.account_id`, `books.book_id`,
   `accounts_at_book.account_at_book_id`).
   - Pass condition: PK column names match.
   - Surface as ALIGNMENT-FINDING-E if mismatch.

6. **`workflows/burst_review/` is empty.** Read
   `bethub-v3/workflows/burst_review/` directory
   listing. Confirm only `__init__.py` present (W13's
   non-scope claim that cascade-triggering logic is
   future work depends on burst_review being unbuilt).
   - Pass condition: empty package marker only.
   - Surface as ALIGNMENT-FINDING-F if burst_review
     surface unexpectedly exists — W13 still ships the
     write surface, but a non-empty burst_review may
     surface unexpected coupling worth triaging.

7. **Schema CHECK constraint pattern matches brief
   reference.** Spot-check
   `bethub-v3/store/schema/cash_flow.py`'s CHECK
   constraint syntax (per W14 line 56–66 area).
   Confirm the multi-line `CHECK (event_type IN ('...',
   '...', ...))` pattern W13 follows.
   - Pass condition: pattern matches.
   - Surface as ALIGNMENT-FINDING-G if drift.

**Halt protocol:**

Any ALIGNMENT-FINDING-A through G is logged in the
report under "Pre-build alignment findings" and **halts
substantive edits** until operator-Claude next session
triages. The brief explicitly invokes the §9.1
partial-ship discipline here — if alignment surfaces
divergence, the right move is halt and surface, not
attempt to bridge unilaterally.

If all seven checks pass, Code proceeds to §6.2 build
order. Single combined alignment statement in the
report's pre-amble: "Pre-build alignment check: 7/7
passed; brief assumptions hold against shipped
substrate."

### §6.2 — Build order

Order matters because the test suite is the verification
surface and each step needs to leave the suite in a
runnable state. Recommended sequence:

1. **Pre-build alignment check** (§6.1). 5–10 min.
2. **Add the four package marker `__init__.py` files
   first.** `workflows/promos/__init__.py`,
   `workflows/promos/v1/__init__.py`,
   `tests/workflows/promos/__init__.py`,
   `tests/workflows/promos/v1/__init__.py`. Empty or
   one-line docstring. Prepares package structure
   before module writes.
3. **Write `store/schema/promos.py`** with DDL +
   indexes + `apply_migrations` (§5.1). Smoke-test the
   migration in isolation: open a `tmp_path` SQLite,
   call `apply_migrations`, confirm all four tables
   and 10 indexes present.
4. **Write `domain/promos/__init__.py`** with enums,
   payload subclasses, `PromoEventBase`,
   FK-nullability validator, `PAYLOAD_BY_EVENT_TYPE`
   dispatch, reference data models (§5.2). Confirms
   imports work.
5. **Write `store/repositories/promos.py`** with all
   four repositories (§5.3). Row-only from session
   one; no Pydantic imports. Run `lint-imports`
   immediately after this write — DR-030 must pass
   here.
6. **Write `workflows/promos/v1/promo_store_adapter.py`**
   with adapter class + helpers + reference data CRUD
   (§5.4). Includes the §5.4.3 adapter-side payload
   reference validation logic.
7. **Update `store/__init__.py`** to add the new
   repositories and error classes at alphabetical
   positions (§5.4 of W14 brief precedent).
8. **Write `tests/store/repositories/test_promos_schema.py`**
   (§5.6.1). Run immediately:
   `uv run pytest tests/store/repositories/test_promos_schema.py
   -v`. Should pass.
9. **Write `tests/store/repositories/test_promos_repository.py`**
   (§5.6.2). Run:
   `uv run pytest tests/store/repositories/test_promos_repository.py
   -v`. Should pass.
10. **Write `tests/workflows/promos/v1/test_promo_store_adapter.py`**
    (§5.6.3). Run:
    `uv run pytest tests/workflows/promos/v1/ -v`.
    Should pass.
11. **Full regression run** —
    `uv run pytest tests/ -q`. Confirm no W11 / W10 /
    W4 / W6 / W14 / clients suites broke.
12. **Run gate suite** — `lint-imports`, mypy, ruff
    on the new and edited files. All five DR-030
    contracts pass; type and lint clean.

Code is free to deviate when a different order is
operationally cleaner (e.g., write the adapter and
repository together to keep both in mind). The broad
order (schema → domain → repository → adapter → tests
→ regression → gate check) is the discipline.

**Test-as-you-go preferred over tests-at-end.** Each
phase ends with a pytest run for the surface that
phase touched. Catches integration issues cheaply.

---
## §7 — Empirical verification

Code captures pre- and post-baselines so the report
shows what moved.

### §7.1 — Pre-baselines (capture at session open,
                          BEFORE pre-build alignment)

- `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"`
  — session-start Adelaide-local anchor.
- `git -C /Users/tim/Desktop/Projects/bethub-v3 status
  --short` — full working-tree snapshot. **The §9.7
  dirty-tree discipline baseline.**
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/workflows/`
  — confirm `promos/` does NOT exist yet.
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/tests/workflows/`
  — confirm `promos/` does NOT exist yet.
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/domain/`
  — confirm `promos/` does NOT exist yet.
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/store/schema/`
  — confirm `promos.py` does NOT exist yet (but
  `cash_flow.py`, `accounts.py`, `bets.py` do).
- `ls -la /Users/tim/Desktop/Projects/bethub-v3/store/repositories/`
  — confirm `promos.py` does NOT exist yet.
- `wc -l /Users/tim/Desktop/Projects/bethub-v3/store/__init__.py`
  — line count baseline (W13's additive edit will
  modify this file).
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/ -q 2>&1 | tail -20` — full test suite
  passes on the dirty tree. Records the regression
  baseline (W14.1 close had 624 passing).
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  lint-imports 2>&1 | tail -20` — confirm all five
  DR-030 contracts kept (W14.1 close had 5/5 clean).
  W13 must preserve this.

### §7.2 — Post-baselines (capture at session close)

After all edits land:

- `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %z"`
  — session-close Adelaide-local anchor.
- `git -C /Users/tim/Desktop/Projects/bethub-v3 status
  --short` — post-edit snapshot. Confirm: every entry
  from §7.1's snapshot still present; new entries for
  `domain/promos/`, `store/schema/promos.py`,
  `store/repositories/promos.py`,
  `workflows/promos/`, `tests/store/repositories/test_promos_*.py`,
  `tests/workflows/promos/` as `??`;
  `store/__init__.py` modified.
- `wc -l` on every new file — record line counts.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/store/repositories/test_promos_*.py
  -v 2>&1` — schema + repository tests pass.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/workflows/promos/v1/ -v 2>&1` — adapter
  tests pass.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  pytest tests/ -q 2>&1 | tail -20` — full suite
  regression. Test count: should be ≥ 624 (the W14.1
  close baseline) + ~90–115 new W13 tests. No test
  count regression.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  lint-imports 2>&1` — **the gate W13 must preserve.**
  All five contracts pass (5 kept, 0 broken). If any
  contract fails, that is the load-bearing finding.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  mypy domain/promos store/schema/promos.py
  store/repositories/promos.py workflows/promos
  2>&1 | tail -20` — type-check the new code.
- `cd /Users/tim/Desktop/Projects/bethub-v3 && uv run
  ruff check domain/promos store/schema/promos.py
  store/repositories/promos.py workflows/promos
  tests/store/repositories/test_promos_*.py
  tests/workflows/promos/v1/ 2>&1` — lint the new
  code.

### §7.3 — File-existence and content checks

For each named anchor:

- **New files exist** at expected paths:
  - `domain/promos/__init__.py`
  - `store/schema/promos.py`
  - `store/repositories/promos.py`
  - `workflows/promos/__init__.py`
  - `workflows/promos/v1/__init__.py`
  - `workflows/promos/v1/promo_store_adapter.py`
  - `tests/store/repositories/test_promos_schema.py`
  - `tests/store/repositories/test_promos_repository.py`
  - `tests/workflows/promos/__init__.py`
  - `tests/workflows/promos/v1/__init__.py`
  - `tests/workflows/promos/v1/test_promo_store_adapter.py`
- **Edited file at expected path:**
  `store/__init__.py` — additive edit only, no
  restructuring. Pre-baseline line count + 5–15 lines
  expected.
- **Line counts within ballpark** (rough sanity guides,
  not hard limits — per S120 standing rule):
  - `domain/promos/__init__.py`: ~600–900 lines.
  - `store/schema/promos.py`: ~300–450 lines.
  - `store/repositories/promos.py`: ~700–1000 lines.
  - `workflows/promos/v1/promo_store_adapter.py`:
    ~500–800 lines.
  - `tests/store/repositories/test_promos_schema.py`:
    ~500–700 lines.
  - `tests/store/repositories/test_promos_repository.py`:
    ~600–900 lines.
  - `tests/workflows/promos/v1/test_promo_store_adapter.py`:
    ~700–1100 lines.
- **`grep "from domain" store/repositories/promos.py`**
  returns no matches — DR-030 compliance check.
- **`grep "from store.repositories.promos"
  workflows/promos/v1/promo_store_adapter.py`**
  returns at least one match — adapter reaches the
  repository correctly.
- **`grep "PromoEventRepository\|PromoRepository\|
  PromoTemplateRepository\|WarningCatalogueRepository"
  store/__init__.py`** returns four matches — the
  store-level re-exports landed.

### §7.4 — Spot-check: end-to-end round-trip via adapter

After all writes land, run a one-shot Python script via
`start_process` (write to `/tmp/w13_smoke.py`, not
interactive REPL — per Cat 3 REPL discipline) that
exercises the public adapter surface end-to-end:

1. Opens a `tempfile.NamedTemporaryFile`-backed SQLite
   connection.
2. Applies W11 + W13 migrations.
3. Seeds W11 account, book, account_at_book.
4. Constructs a `PromoStoreAdapter`.
5. Calls `adapter.create_template(...)` once for a test
   template; `adapter.create_promo(...)` for an instance;
   `adapter.create_warning_type(...)` for a warning.
6. Calls `adapter.append_event(...)` once for each of
   the nine event types, constructing valid payloads
   per FK rules per event type.
7. Calls `adapter.list_by_account_at_book(...)` and
   `adapter.list_by_account(...)`; asserts correct
   subset returns per FK-nullability rules.
8. Writes a `free_bet_credited` then a
   `free_bet_revoked` with `supersedes_event_id`
   pointing at the credit; calls
   `adapter.latest_non_superseded_by_scope(
   account_at_book_id=...)`; asserts the original
   credit is excluded.
9. Calls `adapter.walk_supersession_chain(revoke_event_id)`;
   asserts chain shape (Pydantic models,
   earliest-first).
10. Tests adapter-side payload reference validation:
    attempts to append a `promo_observed` event with a
    non-existent `promo_template_id`; asserts
    `PromoReferenceValidationError`.
11. Closes the adapter, deletes the temp DB, prints
    `"W13 adapter: 9/9 event types round-trip OK;
    supersession-chain walk OK; latest-non-superseded
    read OK; payload reference validation OK."` or
    surfaces the failure.

Belt-and-braces alongside the pytest suite — exercises
the full integration shape end-to-end through the
public adapter surface, fast.

---
## §8 — Output spec

Code produces **one report** at the end of the session,
at:

`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w13_promos/w13_promos_report.md`

The report is operator-facing — written to be read in
one sitting by Tim (Claude Chat triages it in the next
operator session). Plain language, no Code-internal
jargon.

**Required sections:**

1. **Pre-amble** — Adelaide-local session-start and
   session-close timestamps; one-line summary
   ("W13 shipped clean" or "W13 shipped with N
   findings" or "W13 halted at alignment check
   ALIGNMENT-FINDING-X").
2. **Pre-build alignment findings** (§6.1) — one of:
   - "7/7 passed; brief assumptions hold against
     shipped substrate."
   - One paragraph per ALIGNMENT-FINDING-A through G
     surfaced, with the divergence described concretely
     and Code's halt position.
3. **What Code did** — narrative description of the
   sequence executed (which files written in which
   order, which test runs landed when, any deviations
   from §6.2 with reasoning).
4. **What landed where** — flat list of paths created
   and edited, with line counts:
   - 11 new files (5 substantive + 4 package markers +
     ... actually 6 substantive code + 3 test files + 4
     package markers = 13 — see §1.1 for exact)
   - 1 edited file (`store/__init__.py`)
5. **Test results** — three runs:
   - `tests/store/repositories/test_promos_*.py`
     pass count + total runtime.
   - `tests/workflows/promos/v1/` pass count + total
     runtime.
   - Full suite `tests/` pass count + total runtime
     (baseline 624 + ~90–115 new).
6. **Gate results** — lint-imports (5/5 expected),
   mypy (clean), ruff (clean).
7. **Spot-check result** — output of the §7.4
   end-to-end smoke script.
8. **Findings** — one of:
   - "No findings; W13 ships clean."
   - One paragraph per finding (e.g. payload validator
     edge case Code discovered; test-fixture friction;
     file size overrun; etc.).
9. **What was deliberately not done** — short list
   mirroring §1.2 of THIS brief, anything Code
   considered but skipped per scope.
10. **Open questions for triage** — anything Code wants
    operator-Claude to decide in S131 triage
    (e.g. "the W14 cascaded_at_settlement_state string
    representation might want to align with the future
    settlement-state enum — should the type annotation
    be tightened?").
11. **What Code thinks should land next** — short note
    on whether W15 (ops_events), seed scripts for
    reference data, or W12 (balances) is the right
    forward step. Code's suggestion only; final
    routing call is operator-Claude's.

Expected length: ~350–550 lines. The W14.1 report ran
923 lines; W13 should be similar (larger code surface
shipped means more landed-where descriptions, but the
narrative shape is the same).

**Hard rule:** the report contains no recommendations
about Anthropic products, no broader architectural
re-evaluations, no scope-creep suggestions outside what
W13 named. If Code thinks something material to W12 or
W15 surfaced, that's an "open questions for triage"
entry, not a recommendation in the report body.

---
## §9 — Hard limits

### §9.1 — Operating principle

W13 is a **single bounded session**. If the work doesn't
fit in one session, that is a finding — not a
continuation. Partial-but-coherent ship beats
complete-but-lost-coherence.

Partial-ship discipline:

- If Code reaches the session-budget wall mid-build,
  **stop at the next coherent boundary** (end of a
  section per §6.2; not mid-file). Write the report
  through to "what landed where" + "test results so
  far" + an explicit "Stopped at section X of §6.2
  build order; remaining: …" entry.
- The next operator-Claude session triages the partial
  ship and decides forward routing (continue W13 in a
  follow-up Code session; pre-split W13 into a/b/c
  retroactively; re-scope).
- **Do not** "rush to fit." Code's job is to ship the
  named surface to spec, not to ship everything no
  matter what.

§9.1 is the safety net the §1.3 Cat 5 software call on
"three reference tables in one workstream (option (i))"
explicitly invokes. Operator confirmed the partial-ship
catch handles the doesn't-fit risk.

### §9.2 — Behaviour preservation

Code does NOT:

- Change any W11 / W14 / W14.1 behaviour. Every read /
  write / error class shipped before W13 keeps current
  semantics.
- "Improve" anything outside the named surface. No
  drive-by refactors to other modules, no cleanup of
  pre-existing comments, no formatting fixes to files
  W13 doesn't edit.
- Remove any deprecated path, comment, docstring, or
  artefact left from earlier sessions. Anything not in
  W13's named scope stays as-is.

### §9.3 — No adjacent workstreams

Out of scope (per §1.2; restating as hard limits):

- W4 / W4.1 / W6 bet records — DR-032 schema is the
  substrate W13's payload references target, but no
  edits to bet entry / bet records.
- W8 (burst review) — empty in the current codebase;
  cascade-triggering logic lands there in a future
  workstream. W13 ships the WRITE surface for cascade-
  induced credit events; the trigger is not W13's job.
- W11 (accounts) — read-only for FK targets.
- W12 (balances / read-side derivation) — blocked on
  W13. W13 doesn't ship any derivation logic.
- W14 (cash flow) / W14.1 (adapter refactor) —
  pattern reference only; all four W14/W14.1 files are
  read-only for W13.
- W15 (ops_events) — sequenced after W13; W13 doesn't
  touch it.
- All `clients/`, `contracts/`, `ui/`, `ops/`
  modules — unchanged.

### §9.4 — No Alembic, no SQLAlchemy Core migration

W13 uses the existing pre-Alembic `apply_migrations`
pattern per W11/W14. DR-031 locked SQLAlchemy
Core + Alembic for v3, but the migration tooling
transition is deferred to a later workstream
(governance.md DR-029 close-out item 3). W13 does NOT
introduce Alembic or SQLAlchemy Core into the
operational store.

### §9.5 — No `domain/` cross-domain imports

DR-030 carries forward. `domain/promos/__init__.py`
imports only stdlib + Pydantic. No
`from domain.cash_flow import ...` even if structurally
tempting (e.g., the `CashFlowEventSource` enum is
identical to `PromoEventSource`; Code defines a fresh
`PromoEventSource` rather than re-using). Pure modules
stay pure.

### §9.6 — Operational guardrails

Hard guardrails throughout the session:

- **No `create_file` Desktop Commander tool calls.** Use
  `write_file` exclusively. Per Cat 3 ban.
- **Verify every write** — read-back via `read_file` or
  exercise via test invocation. No "wrote it, moving
  on" without confirmation.
- **No Python REPL via interactive process** for
  smoke-checking adapter behaviour. Write scripts to
  `/tmp/w13_*.py` and execute via `start_process`. Per
  S105 / S108 lessons (interactive REPL hangs in
  Desktop Commander).
- **Adelaide-local timestamps** via `TZ="Australia/Adelaide"
  date` for every session anchor in the report.
- **No `analysis` tool / browser tool / Imagine tool /
  any non-Desktop-Commander filesystem path.** All
  filesystem work goes through Desktop Commander or the
  CLI native filesystem tools.

### §9.7 — Dirty-tree handling (carries forward verbatim
                                from W14.1 brief)

The `bethub-v3` working tree has carried a substantial
set of untracked files since the early v3 sessions
(per S78 onwards). The pattern is operator-driven —
generated artefacts, scratch scripts, exploratory data
dumps — and operator intends to triage them post-build
rather than during build sessions.

Discipline for W13:

- **Capture the pre-baseline `git status --short`**
  output at session open (§7.1). Treat that as the
  W13 entry-state contract.
- **At session close, the diff between pre and post
  `git status` MUST show only:**
  - New W13 files (`domain/promos/`,
    `store/schema/promos.py`, etc.) as `??`.
  - `store/__init__.py` as `M` (modified).
  - Nothing else changed compared to pre-baseline.
- **Any other file changes are a finding.** If Code
  accidentally edits or removes a file outside the
  named anchors, that is a §9.2 behaviour-preservation
  violation worth halting on. Re-baseline carefully,
  surface in the report.
- **Tracked untracked files** (those Tim left dirty
  pre-W14) remain untracked at W13 close. Code does
  not add, stage, or commit any of them. Code does not
  edit any of them.
- **Code does not run `git add` / `git commit` / `git
  stash` / `git reset` / any other state-mutating git
  command.** Read-only git inspection only
  (`status --short`, `diff`, `log`).

The dirty-tree spirit: W13 is additive to a known
operator-driven working state, not a clean-build
exercise. Code preserves operator state; Code does not
clean.

---
## §10 — What happens after Code's session

Code does NOT close the W13 workstream or produce the
next brief. The next operator-Claude session triages
Code's report and drives forward routing.

**Triage shape (next operator-Claude session, S131):**

1. **Open** per the bethub-session-open skill — read
   `current_state.md`, `standing_instructions.md`,
   `project_context.md`, `sessions/SESSION_130.md`,
   plus this W13 brief AND Code's W13 report. Verify
   timestamps line up against the §7.1/§7.2 anchors.
2. **Pre-build alignment review.** Did Code's
   alignment check pass 7/7? If not, triage each
   ALIGNMENT-FINDING before reading the build-result
   body.
3. **Verification review.** Confirm every §7 expected
   outcome landed:
   - 11 new files at expected paths
   - 1 edited file with sensible additive diff
   - All three test runs green
   - lint-imports 5/5 clean
   - mypy + ruff clean on new code
   - §7.4 smoke script reported success
4. **Findings triage.** Each finding in Code's report
   classified as:
   - **(a) Brief-spec deviation:** Code did the work
     but landed something different from spec. Triage
     against §1.3 Cat 5 software calls — is the
     deviation operationally better, neutral, or
     worse? Operator confirms or asks for revert.
   - **(b) Spec-implied substrate concern:** something
     about §A.4 / DR-027 / DR-030 / DR-032 etc. that
     was uncovered during build. Routes to a
     follow-on workstream (architecture amendment;
     governance entry; future workstream brief).
   - **(c) Pre-existing codebase shape worth knowing
     about:** something in W11 / W14 / W14.1 that
     surfaced during W13 build. Logged as a future
     trim/cleanup candidate; not addressed in S131.
5. **Forward-routing call.** Three plausible paths
   from a clean W13 ship:
   - **Path A:** Operator seeds reference data
     (`promo_template`, `promo`, `warning_catalogue`)
     via a one-off `scripts/seed_promos.py` script,
     then we proceed to W15 (`ops_events`) brief
     drafting.
   - **Path B:** Skip W15, go directly to W12
     (read-side balances / FB inventory / AccountCare
     warning derivation). W12 has W11 + W14 + W13 all
     present now; it can ship cleanly.
   - **Path C:** Build the W8 burst-review surface
     next so cascade triggering logic lands and
     `free_bet_credited` cascade fields move from
     "write surface only" to "fully exercisable
     end-to-end." Higher operator value; bigger
     workstream.
   - Operator picks at S131; brief drafts at
     S132/S133.

**S131 does NOT:**

- Re-execute any of Code's work.
- Edit any of the 12 W13 anchors.
- Produce a fresh W13 brief or W13.1 surgical fix
  unless a §A.4 / DR-030 / DR-032 violation actually
  surfaced and demands one.

**S131 closes** with `current_state.md` updated (W13
status `in flight` → `done` if clean; `surgical-fix
needed` if a W13.1 brief is the right next step;
`partial` if §9.1 partial-ship invoked), the
`v3_build_picture.md` rebuilt against the new state,
and the next operator-Claude session opening prompt
in place.

---
## §11 — Cross-references

### Architecture

- `architecture.md` §A.1 — entity reference layer.
  Defines `promo_template`, `promo`, `warning_catalogue`
  as stable identifier shapes that W13 implements.
- `architecture.md` §A.2 — per-domain event log spine
  and common event header pattern. W13's
  `promo_events` is the second instance after W14's
  `cash_flow_events`.
- `architecture.md` §A.4 — the substantive substrate.
  Nine event types, three reference tables, promo
  observation / journey / FB lifecycle / cash credit /
  AccountCare warning event-type semantics.
- `architecture.md` §A.5 — cash flow event model (W14
  precedent; pattern reference only — W13 doesn't
  touch §A.5 substrate).
- `architecture.md` §A.6 — settlement state enum;
  cascade fields carry settlement state string values
  per §5.2.4 (`cascaded_at_settlement_state`).
- `architecture.md` §A.7 — cascade chains (the
  settlement-state-change-propagates-to-credit-events
  rules). W13 ships the WRITE surface for cascade
  events; trigger logic deferred.
- `architecture.md` §A.9 — derived state catalogue.
  Promo journey, FB inventory, AccountCare warning
  state all read-derived from `promo_events`;
  derivations themselves are out of W13 scope.

### Decisions

- DR-019 + Session 124 amendment — derived state on
  read. Critical asymmetry: applies to bet records but
  NOT to event tables. W13's `promo_events` is pure
  event-log writes.
- DR-021 — Adelaide local timestamps. Validator pattern
  identical to W14.
- DR-022 — book / account / account-at-book vocabulary.
  W13's FKs use this vocabulary.
- DR-027 + Session 124 amendment — two-database
  architecture + per-domain event-table internal
  shape. W13's `promo_events` is the second instance
  of the per-domain event-table pattern.
- DR-028 — integration boundary discipline (no caching,
  no denormalisation). W13 stays clean — payload
  references to bet records are JSON values, not
  cached/denormalised columns.
- DR-030 + Session 124 amendment — V3 repo layout and
  module-boundary discipline. W13 ships compliant from
  session one.
- DR-031 — V3 tech stack. W13 uses Python 3.12+,
  Pydantic v2, sqlite3 stdlib. No Alembic, no
  SQLAlchemy Core (per §9.4).
- DR-032 — canonical-reference-layer / two-table bet
  record schema. W13's payload references
  (`triggering_bet_id`, `deploying_bet_id`,
  `cascaded_from_bet_id`) target `bets.bet_id`.

### Prior briefs and reports

- `dr029/w11_accounts/w11_accounts_brief.md` (967
  lines) — W11 row-only repository precedent.
- `dr029/w14_cash_flow/w14_cash_flow_brief.md` (1,665
  lines) — substantive template W13 mirrors.
- `dr029/w14_cash_flow/w14_cash_flow_report.md` (864
  lines) — W14 execution report; the loose-typing
  finding (b) that drove the W14.1 v3 convention lock.
- `dr029/w14_cash_flow/w14_1_adapter_brief.md` (1,586
  lines) — v3 row-only-repository + workflow-side-
  adapter convention W13 inherits.
- `dr029/w14_cash_flow/w14_1_adapter_report.md` (923
  lines) — W14.1 execution report.

### Standing instructions

- `standing_instructions.md` Cat 1 — section-by-section
  walkthrough cadence; brevity defaults.
- `standing_instructions.md` Cat 3 — filesystem and
  tooling discipline. Specific rules W13 honours:
  `create_file` ban, verify-every-write, REPL
  discipline (no interactive Python REPL — script-to-
  /tmp and execute), Adelaide-local timestamps,
  Desktop Commander as primary filesystem tool.
- `standing_instructions.md` Cat 5 — operator/Claude
  division of labour. W13's six Cat 5 software calls
  named in §1.3 follow this discipline; operator can
  override any before lock.

### Parking-lot items NOT addressed in W13

- Promo journey derivation function — read-side; W12
  or post-W17 work.
- FB inventory derivation — W12 work.
- AccountCare warning derivation (active per
  account-at-book) — W12 work.
- Cascade-triggering logic — W8 (burst review) work.
- Reference data seeding scripts — operator-driven
  one-off between W13 close and W12 brief drafting.
- Alembic / SQLAlchemy Core migration tooling
  transition — deferred per DR-029 close-out item 3.
- `domain/cash_flow` and `domain/promos` shared
  helpers refactor (e.g. shared
  `_ensure_adelaide_local`) — explicitly NOT done per
  §9.5 (DR-030 spirit: each domain module is
  standalone).

### Build picture context

`v3_build_picture.md` shows W13 transitioning:

- `blocked-on-W14` (pre-W14.1) → `in flight` (S130
  brief lock — this brief) → `done` (S131 triage if
  clean) or `surgical-fix needed` (S131 triage if
  divergence) or `partial` (S131 triage if §9.1
  partial-ship invoked).

W13 unblocks W12 (read-side balances / FB inventory /
warning derivation) and W15 (`ops_events`). W12 needs
W11 + W14 + W13 all present; clean post-W13 close, W12
can ship cleanly.

---

**End of brief.**
