# Brief — Bet-mutation audit log (v3 build)

**Status:** LOCKED (Session 176) — operator-signed, ready for
Code hand-off. Coverage locked S176: **Option A — operator
hand-touches only** (create via Log Past Bet; edit / delete via
BetLog). System / auto mutations excluded (nameable future event
type).
**Type:** build brief — single bounded Claude Code session.
**Serves:** the bet-mutation audit-log item in the post-Brief-2
pre-cutover sequence (`current_state.md`). Closes the gap where a
BetLog edit/delete or a Log Past Bet create leaves **no durable
trail** — today a hand-edit or hand-delete just happens and nothing
remembers it did.
**Builds on:** S171 (BetLog edit/delete endpoints), S176 / Brief 2
(manual create endpoint), W14 cash-flow event log (the authoritative
spine template), W15 ops log (DR-025), architecture.md §A.2
(per-domain event-log spine). See `audit_landscape.md` for the full
audit picture.
**Output report:** `interface_triage/bet_mutation_audit_log_report.md`.

---

## §1 — What this brief is and is not

This is a BUILD brief. Code builds a durable, append-only
**bet-mutation audit log** into v3 end-to-end, as a fourth instance
of the existing per-domain event-log spine (architecture.md §A.2),
against the named anchors in §5, in a single bounded session.

What it builds (detail in §5):
  - bet-mutation domain event types (new `domain/bet_mutations/`);
  - the `bet_mutation_events` table + schema (new
    `store/schema/bet_mutations.py`);
  - the append-only repository (new
    `store/repositories/bet_mutations.py`);
  - the domain<->row store adapter (new
    `workflows/bet_mutations/v1/`);
  - decoupled, after-commit hooks on the three hand-touch endpoints
    (create / edit / delete) so each mutation writes one event;
  - a write-path spot-check (round-trip + decoupling + delete-
    survives-deletion proofs).

Single bounded Code session. If the work does not fit one session,
that is a finding — Code stops and reports it, rather than
continuing past budget. Partial-but-coherent beats
complete-but-lost-coherence.

Surprises become findings in the report, not mid-session
escalations and not scope chases. Code does not ping for direction
mid-flight; it records the surprise and carries on with what it can.
Remediation of anything surfaced routes to the next operator-Claude
triage session — not into Code's report.

What this brief is NOT:
  - not a frontend viewer — v1 captures the trail durably and
    exposes repository reads; a screen to *display* the audit log is
    a later interface brief (§9 hard limit, §10);
  - not the F8 place-time audit sink work — the memory-only
    `MemoryAuditLogSink` (bet-placement, hot path) stays exactly as
    is; its durability gap is parked separately (§9);
  - not a settlement-transition audit — Option A is hand-touches
    only; auto-settle / reconciliation state changes are not logged
    here (a possible future event type, not this brief);
  - not the free-bet credit-in build (brief 3) and not any change
    to the bet-write transaction, settlement, placement, or the
    reconciliation worker.

---

## §2 — Why this work exists

BetLog (S171) lets the operator edit and delete bet records by
hand; Log Past Bet (Brief 2) lets the operator create them by hand.
None of these three hand-touches leaves any durable record. If the
operator edits a stake or deletes a bet — by intent or by accident —
nothing remembers the change happened, what the bet looked like
before, or when. For an operation moving real money across many
accounts that the operator reconciles by hand, that missing trail is
a real integrity gap.

This brief closes that gap the way v3 already does audit elsewhere:
an append-only event log on the shared §A.2 spine. v3 has three such
logs today (promos, cash flow, operations); this is the fourth. It
captures a permanent entry every time a bet record is created,
edited, or deleted by hand — what changed, when, and from where —
and the entry **survives even the deletion of the bet**. Capturing
it now matters: any hand-edit or delete done before this ships
leaves no trail and never can. A screen to *view* the log is a
separate, later concern; the gap is the missing capture, and that is
what this brief fills.

---

## §3 — Pre-reads

Required (read before starting):

  - `audit_landscape.md` — the v3 audit picture: the shared
    event-log spine, the three existing instances, and where this
    fourth one fits.
  - `domain/cash_flow/__init__.py` + `store/schema/cash_flow.py` +
    `store/repositories/cash_flow.py` +
    `workflows/cash_flow/v1/cash_flow_store_adapter.py` — the **W14
    cash-flow log is the authoritative shipped template** for a new
    spine instance. Copy its shape (common header, discriminated
    payload, CHECK-constrained closed enum, row-only repository,
    DR-030 adapter split).
  - `domain/ops/__init__.py` — the W15 ops log: the closest
    precedent for a **bet-axis** event log (`bet_id` + `cycle_id`
    scope, DR-032), including the Adelaide-timestamp validators.
  - `ui/api/routers/bets.py` — the three hand-touch endpoints to
    hook: `create_manual_bet_endpoint`, `edit_bet_endpoint`,
    `delete_bet_endpoint`.
  - This brief, in full.

Reference-only (consult as needed):

  - `architecture.md` §A.2 (per-domain event-log spine + common
    header pattern).
  - `decisions.md` DR-030 (module layering), DR-032 (Betfair
    canonical / bet-axis ids), DR-021 (Adelaide timestamps), DR-019
    (derive-on-read), DR-025 (ops classification — precedent only).

---

## §4 — System access

  - **v3 repo (Mac, read-write):**
    `/Users/tim/Desktop/Projects/bethub-v3`. Code edits only the
    anchors named in §5. The working tree is dirty (coherent
    in-flight v3 build) — see dirty-tree discipline in §9.
  - **Operational store (the v3 SQLite DB):** the new
    `bet_mutation_events` table lives in the operational store
    alongside `bets`, `cash_flow_events`, `ops_events` — the same
    DB the bets repository writes to. New table, additive migration
    (idempotent `apply_migrations`, the sibling pattern). No edit to
    existing tables.
  - **No `capture.db` access.** This brief does not touch the VPS
    capture store at all.
  - **Tests:** `uv run pytest` (the repo is a `uv` project on
    Python 3.12; bare `python3` is 3.11 and fails collection). No
    frontend work in this brief — confirm the frontend is untouched.
  - **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for every
    time-of-day reference in the report and every event timestamp.

---

## §5 — The build

Six pieces, built in the order in §6. Each names its anchors.
"Anchor" = the existing file/region Code reads or extends; line
numbers are as-found at draft time and may have shifted — Code
confirms against the live file. The first four pieces stand the
durable log up bottom-up; the fifth hooks it to the hand-touches;
the sixth proves the round-trip.

### §5.1 — Bet-mutation domain types

**Build.** New `domain/bet_mutations/__init__.py`, following the
`domain/cash_flow` template (common frozen event header + a
discriminated-union `payload` over per-event-type subclasses).
Carries:

  - a closed `BetMutationEventType` enum — `BET_CREATED`,
    `BET_EDITED`, `BET_DELETED` (the three hand-touches). Closed
    enum + DB CHECK mirror the sibling pattern; future types extend
    via migration.
  - a `BetMutationSource` mirroring the existing
    `operator`/`system`/`integration` vocabulary. v1 writes
    `operator` for all three hand-touches.

  - three payload subclasses:
    - `BetCreatedPayload` — a snapshot of the created bet's key
      fields (Betfair market + selection ids, side, stake(s), price,
      settlement_state, strategy_tag, book_or_exchange, placed_at).
    - `BetEditedPayload` — **before + after** for the fields the
      edit endpoint can change. Code confirms the editable field set
      from `edit_bet_endpoint` and captures exactly those (report
      §3 names the set).
    - `BetDeletedPayload` — the **last-known snapshot** of the bet
      at delete time, so the deleted bet's state is preserved.
  - bet-axis scope on the header: `bet_id` (required) + `cycle_id`
    (required), per DR-032 and the ops-log precedent.
  - Adelaide-timestamp validation copied from the cash_flow / ops
    validators (naive or non-Adelaide datetimes rejected at
    construction). DR-030: `domain/` imports stdlib + pydantic only.

### §5.2 — Schema + table

**Build.** New `store/schema/bet_mutations.py`, following
`store/schema/cash_flow.py`. A `bet_mutation_events` table mirroring
the `cash_flow_events` column shape, with the bet-axis scope keys:

  - `event_id` (PK, TEXT), `event_type`, `recorded_at` (when
    logged), `occurred_at` (when the mutation happened), `bet_id`,
    `cycle_id`, `supersedes_event_id` (correction chain), `payload`
    (JSON TEXT), `source`, `correlation_id` (nullable), `notes`
    (nullable).
  - a `CHECK` constraint on `event_type` over the closed enum
    (defence-in-depth, the sibling pattern).
  - idempotent `apply_migrations` + `PRAGMA foreign_keys = ON`, the
    sibling init pattern.

**No foreign key to `bets` (load-bearing).** `bet_id` is stored as a
plain TEXT value, **not** an enforced FK. A deleted bet's audit row
must survive the bet's deletion — an FK with cascade would erase the
trail; an FK without cascade would *block* the delete. Storing the
id as a value (the way `cash_flow_events` stores `account_id`)
decouples the trail from the bet's lifecycle. This is the whole
point of the log.

### §5.3 — Repository (append-only)

**Build.** New `store/repositories/bet_mutations.py`, following
`store/repositories/cash_flow.py` (row-only per DR-030). A
`BetMutationEventRow` dataclass mirroring the columns one-for-one,
and a `BetMutationEventRepository` carrying:

  - **append-only writes** against `bet_mutation_events` — insert
    one event row. **No UPDATE, no DELETE methods on this table,
    ever** (§9 hard limit). A correction is a new event that
    supersedes via `supersedes_event_id`.
  - reads: by `bet_id`, by `cycle_id`, and a supersession-aware read
    (LEFT JOIN against the table on `supersedes_event_id` to filter
    replaced events) — the cash_flow read shape.
  - constructor takes a `sqlite3.Connection` directly (sibling
    pattern); `apply_migrations` invoked on init.

### §5.4 — Store adapter (domain <-> row)

**Build.** New `workflows/bet_mutations/v1/bet_mutations_store_adapter.py`
(+ package `__init__.py`), following
`workflows/cash_flow/v1/cash_flow_store_adapter.py`. Translates the
§5.1 domain events to/from the §5.3 row shape (JSON-serialise the
payload, map header fields). DR-030: the domain<->row translation
lives here, not in the repository.

### §5.5 — Decoupled after-commit hooks on the three hand-touches

**Anchors.** `ui/api/routers/bets.py`:
  - `create_manual_bet_endpoint` (~L742) → emit `BET_CREATED`.
  - `edit_bet_endpoint` (~L556) → emit `BET_EDITED` (before/after).
  - `delete_bet_endpoint` (~L610) → emit `BET_DELETED` (capture the
    bet's snapshot **before** the delete; persist the event so it
    survives the delete).

**Decoupling discipline (non-negotiable — the load-bearing rule).**
The audit write happens **outside the bet-write transaction**, after
the bet write has committed. If the audit write raises, it is
caught and logged (`logger.exception` with the `bet_id`) and the
endpoint **still returns success**. A logging failure must never
roll back, block, or alter a real bet write. The bet path's existing
behaviour on the happy path is unchanged; the audit emit is strictly
additive and strictly after-the-fact.

**Composition.** The repository / adapter is provided to the router
via the existing dependency-injection seam (`composition.py`),
following how the cash_flow / ops repositories are composed. Code
confirms the seam against the live file and wires it the same way.

**Source = `operator`** for all three (these are hand-touches). The
live-placement create path (the orchestrator) is **not** hooked —
that is a system create, excluded under Option A (§9).

### §5.6 — Write-path spot-check (round-trip + proofs)

**Build.** Tests that exercise the whole chain end-to-end over a
real on-disk SQLite store:

  - **edit** a bet via the endpoint → a `BET_EDITED` event is
    written with the correct before/after for the changed field(s).
  - **delete** a bet via the endpoint → a `BET_DELETED` event is
    written, AND querying `bet_mutation_events` *after* the bet row
    is gone returns the event with the right `bet_id` + last
    snapshot (the delete-survives-deletion proof).
  - **create** via the manual endpoint → a `BET_CREATED` event is
    written.
  - **decoupling proof** — induce an audit-write failure (e.g. a
    repository that raises) and confirm the bet edit / delete /
    create still succeeds, the endpoint returns success, and the
    failure is logged. The bet write is not rolled back.
  - **append-only proof** — the repository source contains no
    UPDATE / DELETE SQL against `bet_mutation_events`.

---

## §6 — Sequencing within the session

Dependency order:

1. **§5.1 domain types** — the vocabulary everything else encodes.
2. **§5.2 schema** + **§5.3 repository** + **§5.4 adapter** — the
   durable log, bottom-up. Build + unit-test in isolation before
   wiring to any endpoint.
3. **§5.5 endpoint hooks** — consume §5.1–§5.4; decoupled after
   each existing commit.
4. **§5.6 spot-check** last — exercises the whole chain end-to-end.

If a cleaner order emerges, Code may deviate and say so in the
report.

---

## §7 — Empirical verification

  - **Test baseline.** Capture `uv run pytest` counts (pass/fail)
    before and after. Zero regressions in the existing suites is the
    bar. New tests for the domain types, the schema/repository
    round-trip, the adapter, the three endpoint hooks, and the §5.6
    proofs. Confirm the frontend suite (`tsc -b` / vitest) is
    untouched (no frontend work here).
  - **Live seams untouched — prove it.** `settlement.py` and
    `clients/betfair_client/v1/placement.py` must be byte-identical
    before/after (SHA-256 or diff). The reconciliation worker is
    untouched. The bet-write transaction itself is unchanged — the
    audit emit is after-commit, additive.
  - **Decoupling proof (§5.6)** — audit-write failure does not roll
    back or block the bet write.
  - **Delete-survives-deletion proof (§5.6)** — the audit row
    persists after the bet row is deleted.
  - **Append-only proof** — no UPDATE/DELETE SQL against
    `bet_mutation_events` in the module source.
  - **Architecture** — `uv run lint-imports` clean (DR-030 layering
    holds for the new domain/store/workflow modules).

---

## §8 — Output report spec

Single file: `interface_triage/bet_mutation_audit_log_report.md`.

Structure:
  - what was built, per §5 piece, with final file/line anchors;
  - the **editable-field-set finding** — what `edit_bet_endpoint`
    actually mutates, and therefore what `BetEditedPayload`
    captures;
  - test baselines before/after; the settlement + placement
    seam-unchanged proof;
  - the decoupling proof + the delete-survives-deletion proof;
  - any findings / surprises (incl. anything that did not fit);
  - dirty-tree status at close (§9).

Rough length 300–450 lines. Not a hard cap — overshoot if detail is
load-bearing, flag if so. The report contains NO recommendations and
NO next-brief — that is the next operator-Claude session's job (§10).

---

## §9 — Hard limits (non-negotiable)

  - **Append-only.** No UPDATE and no DELETE against
    `bet_mutation_events`, ever. Corrections supersede via
    `supersedes_event_id`. The repository exposes no such methods.
  - **Decoupled.** The audit write is never inside the bet-write
    transaction; its failure never rolls back, blocks, or alters a
    bet write. After-commit, caught-and-logged.
  - **No hard FK to `bets`.** A deleted bet's audit row survives.
    `bet_id` is stored as a value, not an enforced FK.
  - **Option A coverage only.** Operator hand-touches: create via
    Log Past Bet, edit / delete via BetLog. NO system / auto
    mutations, NO live-placement creates, NO settlement-transition
    or reconciliation events.
  - **No F8 work.** The memory-only place-time `AuditLogSink` /
    `MemoryAuditLogSink` stays exactly as is. Its durability gap is
    a separate parked item.
  - **No frontend viewer / display endpoint.** v1 captures the trail
    + exposes repository reads. A screen or GET endpoint to view the
    log is a later interface brief.
  - **No change to** `settlement.py`, `placement.py`, the
    reconciliation worker, or the bet-write transaction itself —
    prove the seams unchanged (§7).
  - **Named anchors only.** Edit only the regions in §5. No drift
    into adjacent code "while we're here."
  - **Follow the existing idempotent `apply_migrations` pattern.**
    No migration-framework change.
  - **Dirty-tree discipline (the v3 tree is dirty):** read
    `git status` at start; no `git add/commit/stash/restore/
    checkout/reset`; after each edit `git diff <file>` to confirm
    only intended changes; at close `git status` to confirm the
    dirty-file list is unchanged bar the intended edits. If a dirty
    region intersects a §5 anchor, stop and surface it as a finding
    before editing. (Same posture as the Brief 2 build ran.)
  - **No mid-session operator escalation.** Findings go in the
    report; Code runs end-to-end.

---

## §10 — What happens after Code's session

The next operator-Claude (Chat) session reads
`bet_mutation_audit_log_report.md`, triages findings in plain
operational language, surfaces any operator calls, and routes
forward. Code does not write the next brief.

Expected forward sequence after this lands clean:
  - **brief 3 — free-bet credit-in** (the S168 design; surface lands
    inside BetLog). Carry-forward (LOCKED S175): brief 3 must wire
    its promo-trigger / free-bet-credit question to BOTH the live
    "Placed?" hook AND the Log Past Bet manual settle-at-entry
    screen — one settlement-time question, both entry paths.
  - **launcher brief** (F9 in-memory back-off → disk, F10 port
    override, rebuild-if-source-newer) — independent.
  - then **W16 cutover** scoping.

Noted, not scheduled:
  - **bet-mutation-log viewer** — a frontend surface (and/or GET
    endpoint) to read the trail this brief captures. A later
    interface item; the data will be there waiting when it ships.
  - **hedge-link on manual entry** (parked S176) — let a late-logged
    soft-book leg join its already-recorded Betfair offset's cycle
    (the builder supports cycle-join; it is not wired to the
    screen). Burst-review linking covers it meanwhile.

Separately on the roster (not this brief, not blocking cutover): the
Racing-API placings backfill + nightly results-sync fix — its own
Code brief, carrying the DR-027/028 re-read trigger (VPS-side write).

---

## §11 — Cross-references

  - **Audit picture:** `audit_landscape.md` (the spine + all
    instances); `architecture.md` §A.2 (per-domain event-log spine).
  - **Template / precedent:** W14 cash-flow log (authoritative
    template — `domain/cash_flow`, `store/schema/cash_flow.py`,
    `store/repositories/cash_flow.py`,
    `workflows/cash_flow/v1/cash_flow_store_adapter.py`); W15 ops log
    (bet-axis precedent, `domain/ops`); W13 promos log.
  - **DRs:** DR-030 (module layering), DR-032 (Betfair canonical /
    bet-axis ids), DR-021 (Adelaide timestamps), DR-019 (derive-on-
    read), DR-025 (ops classification — precedent only).
  - **Mutation endpoints:** `ui/api/routers/bets.py` — create (Brief
    2, S176), edit / delete (S171 BetLog).
  - **Excluded (parking-lot / other briefs):** F8 place-time sink
    durability; settlement-transition audit; the viewer; system /
    auto mutations; brief 3 (free-bet credit-in); launcher; placings
    backfill + nightly-fix.
