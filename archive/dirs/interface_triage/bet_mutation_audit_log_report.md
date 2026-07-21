# Report — Bet-mutation audit log (v3 build)

**Session:** single bounded Code session, per
`interface_triage/bet_mutation_audit_log_brief.md`.
**Outcome:** complete — all six §5 pieces built, the §5.6 spot-check
green, zero regressions in the existing suite, the live seams proven
byte-identical, DR-030 layering clean. No recommendations / no
next-brief here (that is the next operator-Claude session's job, §10).
**Timestamps:** Adelaide local (ACST, +09:30) per DR-021.

---

## §1 — What was built (per §5 piece, with final anchors)

All four new modules are net-new files; the two endpoint anchors
(`bets.py`) sit in the already-untracked in-flight v3 tree. The
bet-mutation audit log is the fourth instance of the per-domain
event-log spine, copied in shape from the W14 cash-flow log (template)
with the bet-axis scope from the W15 ops log.

### §5.1 — Bet-mutation domain types
`domain/bet_mutations/__init__.py` (new, 378 lines).
- Closed `BetMutationEventType` enum — `BET_CREATED`, `BET_EDITED`,
  `BET_DELETED` (the three hand-touches).
- `BetMutationSource` mirroring `operator`/`system`/`integration`; v1
  writes `operator` for all three.
- A shared `BetSnapshot` (the forensic core) + three payload
  subclasses over a discriminated union keyed on `event_type_payload`:
  - `BetCreatedPayload(snapshot)` — the created bet's key fields.
  - `BetEditedPayload(before, after)` — before/after snapshots over the
    editable field set (Finding F3).
  - `BetDeletedPayload(snapshot)` — the last-known snapshot at delete
    time.
- Common frozen header `BetMutationEventBase` with bet-axis scope
  (`bet_id` + `cycle_id`, both `str`, both REQUIRED for all three
  types), `supersedes_event_id` correction pointer, Adelaide-timestamp
  validation, and event_type↔payload-discriminator cross-check.
- `PAYLOAD_BY_EVENT_TYPE` dispatch table for rehydration.
- DR-030 honoured: imports stdlib + pydantic only (lint-imports KEPT).

### §5.2 — Schema + table
`store/schema/bet_mutations.py` (new, 174 lines).
- `bet_mutation_events` mirroring the `cash_flow_events` column shape on
  the bet axis: `event_id` (PK), `event_type`, `recorded_at`,
  `occurred_at`, `bet_id`, `cycle_id`, `supersedes_event_id`, `payload`
  (JSON TEXT), `source`, `correlation_id`, `notes`.
- CHECK constraints on `event_type` (closed three-value enum) and
  `source` (defence-in-depth alongside the Pydantic enums).
- Four indexes (by bet, by cycle, by event_type, by supersedes).
- Idempotent `apply_migrations` + `PRAGMA foreign_keys = ON`, the
  sibling init pattern. `_add_column_if_missing` helper carried for
  future additive migrations (unused in v1, per the sibling shape).
- **No hard FK to `bets` (load-bearing).** Unlike W15's `ops_events`
  (which declares `FOREIGN KEY (bet_id) REFERENCES bets(bet_id)`), this
  table declares NO outward FK. `bet_id` is stored as a plain TEXT
  value — the way `cash_flow_events` stores `account_id`. The only FK is
  the self-referential `supersedes_event_id`. This is what lets a
  deleted bet's trail survive (proven §5.6). The table has zero outward
  FK dependency, so it migrates standalone on a fresh connection.

### §5.3 — Repository (append-only)
`store/repositories/bet_mutations.py` (new, 418 lines).
- `BetMutationEventRow` dataclass mirroring the columns one-for-one.
- `BetMutationEventRepository` — row-only (no `domain.*` import, DR-030):
  - **`append_row` is the ONLY write method.** There is no UPDATE and
    no DELETE method, and no UPDATE/DELETE SQL anywhere in the module
    (proven by source scan, §5.6).
  - reads: `list_rows_by_bet`, `list_rows_by_cycle`,
    `list_rows_by_event_type`, `get_row`.
  - supersession-aware `latest_non_superseded_rows_by_scope` (LEFT JOIN
    self on `supersedes_event_id`, NULL-successor filter — the cash_flow
    read shape; requires ≥1 scope filter or raises `InvalidScopeError`)
    and `walk_supersession_chain_rows` (with cycle detection).
  - constructor takes a `sqlite3.Connection`; `apply_migrations` +
    `PRAGMA foreign_keys = ON` on init (sibling pattern).

### §5.4 — Store adapter (domain ↔ row)
`workflows/bet_mutations/v1/bet_mutations_store_adapter.py` (new, 259
lines) + package `__init__.py` files.
- `BetMutationStoreAdapter` — Pydantic-typed surface over the row-only
  repo. `append_event` (write), `get_event`, `list_by_bet` /
  `list_by_cycle` / `list_by_event_type`,
  `latest_non_superseded_by_scope`, `walk_supersession_chain`.
- Module-level `_event_to_row` / `_row_to_event` own the JSON
  serialise + `PAYLOAD_BY_EVENT_TYPE` dispatch (the W14.1 / W15 adapter
  split — translation lives here, not in the repository, per DR-030).

### §5.5 — Decoupled after-commit hooks
`ui/api/routers/bets.py` (edited; final anchors):
- audit seam + helpers: `get_bet_mutation_audit_conn` (L139),
  `_snapshot_from_record` (L165), `_new_audit_event` (L195),
  `_emit_bet_mutation_event` (L223).
- `edit_bet_endpoint` (L738) → emits `BET_EDITED` (before/after) at
  L792, after the edit commits.
- `delete_bet_endpoint` (L829) → emits `BET_DELETED` at L857, after the
  delete commits, from a snapshot captured *before* the delete.
- `create_manual_bet_endpoint` (L996) → emits `BET_CREATED` at L1105,
  after the bet write commits.
- Source = `operator` for all three. The live-placement orchestrator
  create path is NOT hooked (a system create, excluded under Option A).

The decoupling discipline is realised three ways at once (see §3):
the emit runs **after** the bet write commits; on its **own
connection** (its own transaction, never inside the bet-write
transaction); and **caught-and-logged** — any failure is swallowed with
`logger.exception(bet_id, event_type)` and the endpoint still returns
success.

### §5.6 — Write-path spot-check
`tests/ui/api/test_bet_mutation_audit.py` (6 tests) — the load-bearing
end-to-end proofs — plus per-layer unit tests
(`tests/store/repositories/test_bet_mutations_repository.py`,
`tests/workflows/bet_mutations/v1/test_bet_mutations_store_adapter.py`).
30 new tests total, all green. Details in §4.

---

## §2 — The editable-field-set finding (§8 required)

**What `edit_bet_endpoint` actually mutates** (confirmed against the
live `BetEditRequest` + the endpoint body, `bets.py`):

| Field | Editable when |
|-------|---------------|
| `strategy_tag` | always (an explicit `null` clears it) |
| `requested_stake` | PENDING only (fenced server-side in the store) |
| `matched_stake` | PENDING only (fenced server-side) |
| `matched_price` | PENDING only (fenced server-side) |

Every settlement-driving field (`settlement_state`, `match_status`,
`commission`, `side`, the leg ids, `cycle_id`) is structurally
un-editable — `BetEditRequest` uses `extra="forbid"`, so they cannot
even be named.

**Therefore `BetEditedPayload` captures** a full `BetSnapshot` on each
of `before` and `after`. The editable set above is the part that can
differ between the two; the remaining snapshot fields are identical on
both sides and serve as context. Capturing full before/after snapshots
(rather than only the changed keys) means the diff is derivable on read
and the audited "after" is a complete record of the bet's post-edit
state, not a sparse delta. The §5.6 test asserts the editable fields
(`strategy_tag`, `requested_stake`) carry the correct before/after.

---

## §3 — Decoupling proof (§5.6 / §7)

The load-bearing rule — an audit-write failure must never roll back,
block, or alter a bet write — is proven by three tests that inject a
connection factory which **raises** on use
(`get_bet_mutation_audit_conn` overridden to a `_boom_factory`):

- `test_edit_succeeds_when_audit_write_fails` — the PATCH still returns
  200, the response carries the new `strategy_tag`, and a follow-up GET
  confirms the edit **persisted** (not rolled back). No audit row is
  written.
- `test_delete_succeeds_when_audit_write_fails` — the DELETE returns
  200 and the bet row is genuinely gone from the `bets` table (asserted
  by raw SQL), despite the audit write failing.
- `test_create_succeeds_when_audit_write_fails` — the POST returns 201
  and the bet renders in the feed.

Why the decoupling holds structurally, not just by test:
1. **After-commit.** Each emit is placed after the bet write's
   `WriteResult` is confirmed successful (after `edit_bet` /
   `delete_bet` / `write_bet_record` have committed — the bet storage
   runs each write in its own autocommit transaction under a lock).
2. **Own transaction.** The emit opens a *separate* `sqlite3.Connection`
   to the operational DB; the audit write is therefore physically
   incapable of being inside the bet-write transaction.
3. **Caught-and-logged.** `_emit_bet_mutation_event` wraps everything
   (including opening the connection and running the migration) in a
   single `try/except Exception` that logs and returns. Nothing it does
   can propagate into the bet path.

---

## §4 — Delete-survives-deletion proof (§5.6 / §7)

Proven at two layers:

- **Store layer** (`test_row_survives_with_no_bets_table`): a
  `bet_deleted` row is appended for a `bet_id` on a connection whose
  database has **no `bets` table at all**, then read back via
  `list_rows_by_bet`. With an FK to `bets`, this insert would fail; with
  no FK it succeeds — the trail does not depend on the bet existing.
- **Endpoint layer** (`test_delete_emits_bet_deleted_and_trail_survives`):
  a standalone pending bet is deleted via the endpoint; the bet
  disappears from the feed and from the `bets` table (raw-SQL count =
  0), yet `BetMutationStoreAdapter(op_db).list_by_bet("bet-del")`
  returns the `BET_DELETED` event with the last-known snapshot
  (`settlement_state="pending"`, `matched_price=3.0`) captured before
  the delete.

A related structural confirmation: the store's `delete_bet` pre-checks
reference `ops_events` / `promo_events` for blocking referents but
**not** `bet_mutation_events`. Combined with the no-FK design, this
means the audit trail neither blocks a delete (an FK-without-cascade
would) nor is erased by one (an FK-with-cascade would).

---

## §5 — Append-only proof (§5.6 / §7)

Two tests in the store suite:
- `test_repository_source_has_no_update_or_delete_sql` — scans the
  module source: no `update bet_mutation_events` and no
  `delete from bet_mutation_events` substring exists.
- `test_repository_exposes_no_mutating_methods` — reflects over the
  repository's public surface: no `update*` / `delete*` method.

Corrections are modelled as a new event with `supersedes_event_id`
pointing at the prior event; the supersession-aware read +
chain-walk + cycle detection are exercised at both the repository and
adapter layers.

---

## §6 — Test baselines (before / after)

| | Result |
|---|---|
| **Before** (`uv run pytest`) | **1128 passed**, 0 failed, 4 warnings |
| **After** (`uv run pytest`) | **1158 passed**, 0 failed, 4 warnings |

- **+30 new tests**, all green; **zero regressions** in the existing
  1128.
- New tests: store schema/repo round-trip + append-only +
  delete-survives + supersession (store suite); adapter round-trip for
  all three event types + all domain validators (adapter suite); the 6
  endpoint spot-checks (3 happy-path hooks + 3 decoupling proofs).
- The 4 warnings are the pre-existing `HTTP_422_UNPROCESSABLE_ENTITY`
  deprecation warnings — unchanged in count and origin from baseline.
- Frontend untouched (no frontend work in this brief); no `tsc` /
  vitest run was needed or performed.
- `uv run lint-imports` — **5 contracts kept, 0 broken** (DR-030 layered
  architecture, domain-pure, store-pure, contracts-leaf,
  workflows-independent). The new `workflows.bet_mutations` is correctly
  NOT added to the `workflows-independent` contract — like
  `workflows.cash_flow` / `workflows.promos`, it is an event-log
  workflow, not one of the mutually-independent orchestration packages.

---

## §7 — Live seams unchanged (§7 proof)

SHA-256, session start → session close (byte-identical):

| File | Baseline | Close |
|------|----------|-------|
| `clients/betfair_client/v1/settlement.py` | `73f0561b…` | `73f0561b…` |
| `workflows/bet_entry/v1/settlement.py` | `9e07a75d…` | `9e07a75d…` |
| `clients/betfair_client/v1/placement.py` | `fad6c280…` | `fad6c280…` |

- The reconciliation worker (`workflows/bet_entry/v1/reconciliation.py`)
  was not opened or edited.
- The bet-write transaction itself is unchanged — the audit emit is
  after-commit and additive; the happy-path bet write behaviour is
  byte-identical (the only additions to the endpoints are the
  read-only pre-snapshot read and the post-commit emit, both guarded).

Note: `placement.py` shows as `M` in `git status` because it was
**already modified in the dirty baseline** (the coherent in-flight v3
build); its hash is unchanged across *this session*, satisfying the
byte-identical-before/after bar for the work done here.

---

## §8 — Findings / surprises

**F1 — Reference pre-read docs absent from the repo.**
`audit_landscape.md`, `architecture.md`, and `decisions.md` (named as
pre-reads / references in §3) do not exist anywhere in the
`bethub-v3` tree. The build proceeded using the **code** as the
authoritative template — which is exactly what the brief privileges
("the W14 cash-flow log is the authoritative shipped template"). No
blocker; the DR/architecture intent was fully recoverable from the
cash_flow / ops modules and their docstrings.

**F2 — Composition-root wiring of the audit connection was the wrong
seam; derive-from-storage is correct (deviation from §5.5 literal
instruction).** §5.5 directs wiring the adapter "via the existing
dependency-injection seam (composition.py), following how the
cash_flow / ops repositories are composed." Two facts surfaced during
the build:
  1. The cash_flow / ops adapters are **not** composed in
     `composition.py` at all (grep-confirmed) — they are constructed
     ad-hoc from a passed connection inside `workflows.balances`. So
     there is no existing composition pattern to follow for them.
  2. More importantly, a composition-fixed audit DB path **diverges**
     from the bet storage. The bet storage is itself a per-request
     injected dependency that every test overrides to a temp DB; a
     composition-wired audit factory (bound to the resolved production
     path) would therefore write audit rows to the **production**
     `data/bethub.db` during test runs that exercise edit/delete/create
     — both polluting the operator's real store and making the trail
     un-assertable against the test DB. (This was observed directly:
     with the composition override in place, the §5.6 happy-path tests
     read zero rows because the writes went to the production path.)

  Resolution: the audit connection is **derived from the injected bet
  storage's own path** when no explicit factory is wired
  (`get_bet_mutation_audit_conn` returns `None` by default). This
  co-locates the trail with the bets it shadows in *every* context —
  production and tests — exactly as §4 mandates ("the same DB the bets
  repository writes to"), with no path to drift. The DI seam still
  exists and is overridable (the §5.6 decoupling proof overrides it
  with a raising factory); the composition.py override was written,
  observed to be harmful, and reverted (composition.py is byte-identical
  to its session-start state — no net edit). This is a deliberate
  deviation from the brief's literal instruction, surfaced here per §1
  rather than escalated mid-flight.

**F3 — Editable field set confirmed** = `{strategy_tag,
requested_stake, matched_stake, matched_price}` (the last three
PENDING-only). See §2.

**F4 — Snapshot fields are primitive-typed by design.** `BetSnapshot`
stores ids/tags/states as `str`, stakes as `Decimal`, price as `float`,
`placed_at` as `datetime` — it does **not** import the `domain.bets`
enums (`StrategyTag` / `SettlementState` / `BetSideTag`). An audit log
is a forensic record of what the bet *was*; it must round-trip whatever
value the bet carried without re-validating against the *current*
bet-domain vocabulary (which may drift), and a deleted bet's snapshot
must survive even if an enum the bet relied on is later changed. This
keeps the trail decoupled from `domain.bets` evolution. (DR-030 would
in fact permit a `domain.bet_mutations → domain.bets` import — both are
in the `domain` layer — so this is a design choice, not a layering
constraint.)

**F5 — Multi-leg bets capture only the primary leg's Betfair ids.** The
snapshot's `betfair_market_id` / `betfair_selection_id` come from
`legs[0]`, mirroring how the BetLog feed derives `selection_name`. The
named §5.1 field set is scalar ("Betfair market + selection ids"), so a
multi-leg bet records only its primary leg's ids in the snapshot.
Manual-create bets are single-leg racing bets, so create is unaffected;
an edit/delete of a (rare) multi-leg bet would capture leg 0 only.
Flagged as a v1 scope edge, not a defect.

**F6 — Header carries no `parent_event_id`.** The cash_flow and ops
headers carry both `parent_event_id` and `supersedes_event_id`; the
§5.2 column list for `bet_mutation_events` names only
`supersedes_event_id`. The build followed the brief's column list — the
correction chain (supersession) is the one relationship this log needs;
no parent-chaining use case exists for hand-touch mutations. Noted as
an intentional, brief-directed narrowing of the spine shape.

**F7 — Edit and delete gain one read-only pre-read.** To capture the
`before` (edit) / last-known (delete) snapshot, each endpoint performs
one extra `read_bet_record` *before* the write. It is wrapped in its own
guard so a failure there can never affect the write, and it touches only
the read path — the bet-write transaction is unchanged. If the pre-read
yields `None` (only possible on a transient read error or a
non-existent bet, which 404s anyway), the emit is skipped.

**F8 — `occurred_at == recorded_at` for hand-touches.** A hand-touch
mutation happens at the moment the operator performs it, so both header
timestamps are Adelaide-local "now". The bet's own `placed_at` (which
may be days earlier for a Log Past Bet create) is captured separately
inside the snapshot. No information is lost.

---

## §9 — Dirty-tree status at close (§9 discipline)

- **Start:** `git status` captured; tree dirty (coherent in-flight v3
  build) — 17 tracked-modified files + a set of untracked files/dirs.
- **No** `git add` / `commit` / `stash` / `restore` / `checkout` /
  `reset` was run at any point.
- **No §5 anchor intersected a dirty region** requiring a stop: the four
  new modules are net-new files; the two endpoint anchors
  (`bets.py`) and `composition.py` live under the already-untracked
  `ui/api/` tree (part of the in-flight build, not a conflicting dirty
  edit).
- **Close:** the 17-file tracked-modified set is **byte-for-byte
  identical** to baseline (verified by diff) — this session touched **no
  tracked file**. The untracked set differs from baseline by exactly
  four intended additions:
  - `domain/bet_mutations/`
  - `store/schema/bet_mutations.py`
  - `store/repositories/bet_mutations.py`
  - `workflows/bet_mutations/`
  plus the in-place edits to the already-untracked
  `ui/api/routers/bets.py` and the new test files under the
  already-untracked `tests/` trees (`tests/store/repositories/`,
  `tests/workflows/bet_mutations/`, `tests/ui/api/`). `composition.py`
  is unchanged from its session-start state (the override was added,
  found harmful per F2, and fully reverted).

The dirty-file list at close is unchanged bar the intended edits.

---

## §10 — Scope conformance (§9 hard limits)

- **Append-only** — no UPDATE/DELETE on `bet_mutation_events`; proven
  (§5).
- **Decoupled** — after-commit, own transaction, caught-and-logged;
  proven (§3).
- **No hard FK to `bets`** — `bet_id` stored as a value; trail survives
  deletion; proven (§4).
- **Option A coverage only** — only the three operator hand-touch
  endpoints hooked; the live-placement orchestrator create is not
  touched; no settlement/reconciliation events.
- **No F8 work** — `MemoryAuditLogSink` untouched.
- **No frontend viewer / display endpoint** — v1 captures + exposes
  repository reads only.
- **No change to** settlement.py / placement.py / reconciliation worker
  / the bet-write transaction — proven (§7).
- **Named anchors only** — no drift into adjacent code.
- **Idempotent `apply_migrations`** pattern followed; no
  migration-framework change.
- **No mid-session operator escalation** — surprises recorded as
  findings (§8), session ran end-to-end.
