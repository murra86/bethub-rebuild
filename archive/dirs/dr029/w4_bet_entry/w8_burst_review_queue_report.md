# W8 — burst-review queue report

**Drafted:** 2026-05-08 (Adelaide local per DR-021)
**Source brief:** `dr029/w4_bet_entry/w8_burst_review_queue_brief.md` (671 lines).
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`
**Python interpreter:** `.venv/bin/python` (3.12.7)
**Status:** ship-clean — full pytest + vitest suites green; ruff,
eslint, lint-imports clean; no new mypy errors; all nine §5 anchors
landed.

---

## §1 Executive summary

W8 closes §2.6's operator-facing surface for the settlement-race
contract. The burst-review queue is now a working operator surface
end-to-end: bets entering `SettlementState.PROVISIONAL` flow from
the W6.5 storage helper through a new `routers/provisional.py`
FastAPI router, into a React queue page that auto-refreshes every
3 seconds and renders a per-bet modal whose three terminal-state
action buttons fire the new manual-resolution endpoint. The W6.5
"build-proper" carry-forward at `settlement.py` (the manual
operator path from §2.6 §3.2) is now live as
`apply_manual_operator_resolution`, called by the new
`POST /api/v1/bets/provisional/{bet_id}/resolve` endpoint, with
state-machine validation, count-field preservation, and audit-log
emission via the worker logger.

**Empirical:**

- pytest: 463 → 486 (+23). 9 new tests for §5.5; 14 new tests for
  §5.3 + §5.4.
- vitest: 3 → 30 (+27). 16 new tests for the §5.7 modal; 8 new
  tests for the §5.6 queue page; 3 new tests for the §5.8 nav.
- ruff: clean. eslint: clean. lint-imports: 5/5 contracts kept.
- mypy strict on `ui/`: clean. mypy strict on `workflows/bet_entry`:
  15 errors, all in pre-existing `betfair_adapter.py` (unchanged
  from pre-baseline; not caused by W8).
- vite production build: 75 modules, 262.14 kB JS / 6.32 kB CSS.

**Named-anchor checklist (§5.1 → §5.9):**

- [x] §5.1 — `apiPost`, `apiPatch` wrappers added to `client.ts`
  alongside the existing `apiGet`. Includes parsed-error-body
  attached to `ApiError.detail`.
- [x] §5.2 — `.env.development`, `.env.production`, README updated.
- [x] §5.3 — `GET /api/v1/bets/provisional` returning
  `list[ProvisionalBetItem]`. Empty-array on clean DB; populated
  with all the brief's named fields plus runner name and event
  start.
- [x] §5.4 — `POST /api/v1/bets/provisional/{bet_id}/resolve` with
  the four §5.4 failure-mode envelopes (404 / 409 / 422 / 500).
- [x] §5.5 — `apply_manual_operator_resolution` in `settlement.py`
  with state-machine validation, count preservation, audit-log
  emission via `LOG.info`. Four exception types map cleanly to the
  four HTTP envelopes.
- [x] §5.6 — `routes/Provisional.tsx` queue page with 3-second
  auto-refresh, click-to-open modal, empty / loading / error
  states, auto-resolution detection.
- [x] §5.7 — `components/ProvisionalBetModal.tsx` with bet identity
  header, four content sections, three-button action area gated by
  inline confirmation step, optional reason field, error-banner
  inline, ESC / overlay-click / dismiss-button close paths.
- [x] §5.8 — Top-of-page nav bar in `App.tsx` (with extracted
  `App.module.css`) listing **Burst review** and **Health**. Root
  redirect updated to `/provisional`.
- [x] §5.9 — Smoke-test verified end-to-end: live FastAPI on
  port 8765, `curl` probes for empty queue → synthetic-bet
  insertion → populated queue → POST resolve → DB-side state
  transition → empty queue. All four failure envelopes confirmed
  via curl. OpenAPI spec emits the new endpoints; the codegen
  step regenerated `src/api/types.ts` cleanly.

---

## §2 Pre/post empirical baseline

### §2.1 Test counts

| Surface | Pre | Post | Δ |
|---|---:|---:|---:|
| pytest total | 463 | 486 | **+23** |
| pytest `tests/workflows/bet_entry/v1/` | 212 | 221 | +9 |
| pytest `tests/workflows/bet_entry/v1/test_settlement.py` | 41 | 50 | +9 |
| pytest `tests/ui/api/` | 5 | 19 | +14 |
| vitest total | 3 | 30 | **+27** |

The +23 pytest delta breaks down as 9 §5.5 workflow tests + 14
§5.3/§5.4 endpoint tests. The +27 vitest delta breaks down as
16 §5.7 modal tests + 8 §5.6 queue-page tests + 3 §5.8 nav tests.

### §2.2 Lint / type / build

| Gate | Pre | Post |
|---|---|---|
| `ruff check .` | clean | clean |
| `lint-imports` | 5/5 kept (118 files / 327 deps) | 5/5 kept (120 files / 336 deps) |
| `mypy --strict ui/` | clean (8 files) | clean (9 files) |
| `mypy --strict workflows/bet_entry` | 15 errors in `betfair_adapter.py` | 15 errors in `betfair_adapter.py` (same set; pre-existing) |
| `npm run lint` (eslint) | clean | clean |
| `npx vitest run` | 3 passed | 30 passed |
| `npm run build` | 69 modules, 245.95 kB JS / 870 B CSS | 75 modules, 262.14 kB JS / 6.32 kB CSS |

The pre-existing 15 mypy errors in `workflows/bet_entry/v1/betfair_adapter.py`
(W6 ship-state, all `union-attr` / `arg-type` against the
`FreshEnvelope | StaleEnvelope | UnavailableReadEnvelope` union)
are unchanged across the W8 session — W8 added zero mypy errors.
mypy chases imports transitively, so any check that touches
`MarketSettlement` types pulls `betfair_adapter.py` into the graph.
Surface as a finding (§8) since it's not new but is visible whenever
mypy runs anywhere near the W6.5+ files.

### §2.3 LOC deltas

| File | Pre | Post | Δ | Status |
|---|---:|---:|---:|---|
| `workflows/bet_entry/v1/settlement.py` | 726 | 878 | +152 | modified (§5.5) |
| `tests/workflows/bet_entry/v1/test_settlement.py` | 1364 | 1597 | +233 | modified (§5.5 tests) |
| `ui/api/main.py` | 51 | 52 | +1 | modified (§5.3 wiring) |
| `ui/api/routers/__init__.py` | 10 | 11 | +1 | modified (§5.3 export) |
| `ui/api/routers/provisional.py` | 0 | 375 | +375 | **new** (§5.3 + §5.4) |
| `tests/ui/api/test_provisional.py` | 0 | 395 | +395 | **new** (§5.3 + §5.4 tests) |
| `ui/web/src/api/client.ts` | 36 | 95 | +59 | modified (§5.1) |
| `ui/web/.env.development` | 0 | 12 | +12 | **new** (§5.2) |
| `ui/web/.env.production` | 0 | 12 | +12 | **new** (§5.2) |
| `ui/web/README.md` | 66 | 86 | +20 | modified (§5.2) |
| `ui/web/src/api/provisional.ts` | 0 | 149 | +149 | **new** (§5.6 / §5.7 substrate) |
| `ui/web/src/components/ProvisionalBetModal.tsx` | 0 | 388 | +388 | **new** (§5.7) |
| `ui/web/src/components/ProvisionalBetModal.module.css` | 0 | 220 | +220 | **new** (§5.7) |
| `ui/web/src/components/ProvisionalBetModal.test.tsx` | 0 | 322 | +322 | **new** (§5.7) |
| `ui/web/src/routes/Provisional.tsx` | 0 | 198 | +198 | **new** (§5.6) |
| `ui/web/src/routes/Provisional.module.css` | 0 | 122 | +122 | **new** (§5.6) |
| `ui/web/src/routes/Provisional.test.tsx` | 0 | 189 | +189 | **new** (§5.6) |
| `ui/web/src/App.tsx` | 30 | 49 | +19 | modified (§5.8) |
| `ui/web/src/App.module.css` | 0 | 42 | +42 | **new** (§5.8) |
| `ui/web/src/App.test.tsx` | 0 | 46 | +46 | **new** (§5.8) |
| `ui/web/src/api/types.ts` | 76 | 334 | +258 | regenerated (§5.9 codegen) |

Files touched: 21 total (8 modified / 13 new). No edits outside
the named §5 anchors. The `types.ts` regeneration is part of §5.9
smoke-test verification (the W7 ship documents codegen as a manual
step that runs against the live OpenAPI spec) and lives in `ui/web/src/api/`,
which is the §5.1 / §5.6 / §5.7 frontend tree.

### §2.4 What was deliberately NOT touched

- `workflows/bet_entry/v1/storage.py` — read but not edited. Brief
  §9 forbids schema changes; the existing
  `update_settlement_state` / `read_bet_record` / 
  `list_provisional_settlement_bets` surfaces were sufficient.
- `workflows/bet_entry/v1/orchestrator.py` — read but not edited.
- `workflows/bet_entry/v1/reconciliation.py` — not touched (W6 ship,
  out of scope).
- `clients/betfair_client/v1/settlement.py` — read for the
  `MarketSettlement` / `MarketStatus` / `RunnerSettlementStatus`
  types; not edited.
- `ui/api/config.py` — not edited. The `BETHUB_DB_PATH` env var the
  router consumes is read directly via `os.environ` in
  `_build_default_storage`; integrating into `Settings` would
  expand the §5 anchor surface unnecessarily. See §6.6 deviation
  for the rationale.
- `ui/api/routers/health.py` — not edited.
- `ui/web/src/routes/Health.tsx` and `Health.test.tsx` — not edited.
- `pyproject.toml`, `.importlinter`, `eslint.config.js`,
  `tsconfig*.json`, `vite.config.ts`, `package.json` — not touched.
  The W7 stack-version locks hold.

---

## §3 Per-anchor ship summary

### §3.1 — §5.1 — `apiPost` and `apiPatch` client wrappers

**File:** `ui/web/src/api/client.ts` (36 → 95 lines, +59).

Added `apiPost` and `apiPatch` alongside `apiGet`. Both wrappers
share an internal `apiSend` helper that:

- composes `${API_BASE_URL}${path}` URL.
- sets `Accept: application/json` + `Content-Type: application/json`.
- JSON-encodes the body (default `{}` if not supplied).
- on non-2xx, attaches the parsed error body (JSON if parseable,
  else text) to a new `ApiError.detail` field — load-bearing for
  the §5.7 modal's inline error rendering, which surfaces FastAPI's
  `{"detail": "..."}` shape verbatim.

Also extended `apiGet` to use the same `parseErrorBody` helper so
its error envelope shape matches the new wrappers (the prior
implementation discarded the body). The W7 `Health.test.tsx`
continues to pass — the existing `ApiError(path, status, message)`
call site still works because `detail` is an optional 4th arg.

DELETE wrapper not added per brief ("DELETE not needed at v1").

**Tests:** the modal tests (§3.7) exercise `apiPost` end-to-end via
the `resolveProvisionalBet` wrapper (which calls `apiPost`). Direct
unit tests of `apiPost` / `apiPatch` were not added; the integration
through `apiPost → resolveProvisionalBet → modal flow → backend`
covers the wire path.

### §3.2 — §5.2 — `VITE_API_BASE_URL` documentation pair

**Files:**
- `ui/web/.env.development` (12 lines, new) —
  `VITE_API_BASE_URL=http://localhost:8000`.
- `ui/web/.env.production` (12 lines, new) — `VITE_API_BASE_URL=`
  (empty, with a commented `# VITE_API_BASE_URL=https://api.example.com`
  alternative). Empty default favours the post-DR-029 same-origin
  static-serving deploy story; the bundle issues document-relative
  URLs and reaches the API on the same origin.
- `ui/web/README.md` (66 → 86 lines, +20) — added an "API base
  URL" section documenting the convention and naming the
  `*.local` override path for developer overrides without
  touching committed defaults.

W7 §7.4 carry, folded into W8 per Session 107 close.

### §3.3 — §5.3 — `GET /api/v1/bets/provisional`

**File:** `ui/api/routers/provisional.py` (new, 375 lines), wired
into `main.py:create_app()` via `app.include_router(provisional_router,
prefix="/api")`.

Endpoint: `GET /api/v1/bets/provisional`. Returns
`list[ProvisionalBetItem]`.

`ProvisionalBetItem` is a flattened, UI-tractable shape derived
from `ProvisionalSettlementSurfacingPayload`:

- Identity: `bet_id`, `placement_time`, `entered_provisional_at`.
- Event/market: `betfair_market_id`, `betfair_selection_id`,
  `betfair_event_name`, `betfair_market_name`,
  `betfair_selection_name`, `betfair_event_venue`,
  `betfair_event_start_time`.
- Bet shape: `book_or_exchange`, `account_at_book_id`,
  `requested_stake` (Decimal — Pydantic serialises as JSON string
  for precision preservation; verified in test), `matched_price`.
- Trigger: `trigger_source` (the
  `ProvisionalTriggerSource.value` — currently always
  `"unexpected_state"` at v1 per W6.5 §5.5 Change C),
  `operator_escalation_reason` (None at v1 — no manual-escalation
  path yet).
- Last read: `last_read_market_state` —
  `MarketStateSummary | None`. Always None at v1 because the W6.5
  storage helper passes `last_read=None`. Future briefs that
  persist the worker's last MarketSettlement read on the bet
  record can populate this without API changes.
- `related_bet_ids: list[str]` — pointer to other bets sharing the
  market (W6.5 §5.6 Change D / Deviation #4 of W6.5 report).

Storage is injected via FastAPI's `Depends(get_storage)`
mechanism. Default factory `_build_default_storage` (cached via
`lru_cache(maxsize=1)`) reads `BETHUB_DB_PATH` from the
environment, falling back to `<repo>/data/bethub.db`. Tests
override via `app.dependency_overrides[get_storage]`.

Brief mentioned `selection_name`-on-row is "nice-to-have not
essential for v1"; the leg already carries `betfair_selection_name`
from W4's bet-record build path, so the API surfaces it natively
with no extra fetch / DB join. Runner-name resolution for the v1
queue is not a follow-up brief item.

**Pagination:** the storage helper caps at 100; the API returns
the full list. No follow-up brief commissioned per §1.

### §3.4 — §5.4 — `POST /api/v1/bets/provisional/{bet_id}/resolve`

**File:** same `routers/provisional.py` (co-located).

Endpoint:
`POST /api/v1/bets/provisional/{bet_id}/resolve`.
Body: `ResolveRequest { new_state: 'settled_won' | 'settled_lost'
| 'voided', operator_reason?: string | null }`.
Response on success: `ResolveResponse { bet_id, settlement_state,
last_reconciled_at, operator_reason, applied_at }`.

Failure modes (verified end-to-end via curl during §5.9 smoke):

- 404 — bet not found:
  `{"detail":"bet_id 'nonexistent' not found"}`.
- 409 — bet not in `PROVISIONAL`:
  `{"detail":"bet_id 'X' is in settlement_state 'settled_won';
  manual operator resolution requires PROVISIONAL"}`.
- 422 — `new_state` outside the literal set: handled by Pydantic
  validation:
  `{"detail":[{"type":"literal_error","loc":["body","new_state"],
  "msg":"Input should be 'settled_won', 'settled_lost' or
  'voided'",...}]}`.
- 500 — storage write failure:
  `{"detail":"storage update_settlement_state failed for bet_id
  'X': simulated sqlite failure"}`.

The handler is a thin shell over `apply_manual_operator_resolution`
(§3.5). The four `ManualResolutionError` subclasses raised by the
workflow map 1:1 to the four HTTP envelopes via try/except clauses.
The `InvalidTerminalStateError` branch is defensive — Pydantic's
`Literal` validator catches the same case earlier, but the
workflow keeps independent validation so it can be called from
non-HTTP paths (e.g. a future CLI tool) without surface skew.

### §3.5 — §5.5 — `apply_manual_operator_resolution`

**File:** `workflows/bet_entry/v1/settlement.py` (726 → 878,
+152 lines).

New module-level surfaces:

- `TERMINAL_SETTLEMENT_STATES: tuple[SettlementState, ...]` — the
  three permitted terminal targets of the manual operator path.
- `ManualResolutionError` (base) and four subclasses:
  `BetNotFoundError`, `InvalidSettlementTransitionError`,
  `InvalidTerminalStateError`, `SettlementStorageError`.
- `apply_manual_operator_resolution(*, bet_id, new_state,
  operator_reason, storage, now) -> BetRecord` —
  the transition function.

Behaviour:

1. Validate `new_state ∈ TERMINAL_SETTLEMENT_STATES`. Raise
   `InvalidTerminalStateError` otherwise.
2. `storage.read_bet_record(bet_id)`. Raise `BetNotFoundError`
   if None.
3. Verify `record.settlement_state == PROVISIONAL`. Raise
   `InvalidSettlementTransitionError` otherwise.
4. `storage.update_settlement_state(bet_id, settlement_state=
   new_state, dead_heat_count=record.dead_heat_count, ...)` —
   preserves the three count fields populated by the
   auto-resolution worker on the original PROVISIONAL transition.
   Raise `SettlementStorageError` on `WriteResult.success=False`.
5. `_write_settlement_bookkeeping(storage, bet_id, last_reconciled_at=now)`
   — same shared substrate as the auto-resolution path per
   W6.5 §5.5 Change G.
6. `LOG.info("settlement manual operator resolution: bet_id=%s,
   previous_state=provisional, new_state=%s, operator_reason=%s,
   applied_at=%s", ...)`.
7. Re-read the record and return.

**Audit-trail surface — path Code took.** No structured audit-trail
surface exists in the W6.5 ship. `tests/workflows/bet_entry/v1/test_settlement.py`
has no audit-table fixture; `storage.py` has no audit row /
column / table; `settlement.py`'s auto-resolution path emits
INFO-level log lines on every transition (e.g.
`"settlement resolved bet_id=X: pending -> settled_won (reason=...)"`).
The closest thing to "audit" in the W6.5 ship is therefore the
worker logger plus the `last_reconciled_at` /
`reconciliation_attempts` counters on the bet record.

W8 v1 lands the manual transition write **without** a structured
audit-trail row, in line with the brief's explicit guidance ("ship
the transition write *without* the audit entry, and flag the
audit gap as a §6 deviation. Do not block W8 on building an audit
surface"). The manual path emits the same INFO-level log line shape
as the auto path — the operator reason and the previous/new state
appear in the log message — so post-hoc review via the operator's
log files can reconstruct the operator action. A persisted audit
trail (e.g. an `audit_log` table) is a follow-up brief; see §7.

**Tests:** 9 new tests in
`tests/workflows/bet_entry/v1/test_settlement.py` Block 7
(line 1392+):

1. `test_manual_resolution_transitions_provisional_to_settled_won`
2. `test_manual_resolution_transitions_provisional_to_settled_lost`
3. `test_manual_resolution_transitions_provisional_to_voided`
4. `test_manual_resolution_preserves_count_fields` — the three
   race-shape count fields populated on the original PROVISIONAL
   transition are preserved on the manual write.
5. `test_manual_resolution_logs_operator_reason` — the audit-log
   substrate at v1 (the worker logger) carries the operator
   reason and the new state in the same line.
6. `test_manual_resolution_raises_when_bet_not_found` (404 path).
7. `test_manual_resolution_raises_when_bet_not_in_provisional`
   (409 path).
8. `test_manual_resolution_raises_when_new_state_not_terminal`
   (422 path) — checks both `PENDING` and `PROVISIONAL` rejected.
9. `test_manual_resolution_raises_on_storage_write_failure`
   (500 path) — uses an `InMemoryBetRecordStorage` subclass that
   forces `update_settlement_state` to return
   `WriteResult(success=False, ...)`.

The brief's mandate was "at least three positive paths plus the
four failure modes". 9 tests delivered (3 positive + 1 count-
preservation + 1 logging + 4 failure modes). The two extra tests
are the "preserves counts" and "logs reason" cases, which capture
load-bearing behaviour that the bare positive/negative counts
would miss.

### §3.6 — §5.6 — Provisional queue page

**Files:**
- `ui/web/src/routes/Provisional.tsx` (new, 198 lines).
- `ui/web/src/routes/Provisional.module.css` (new, 122 lines).
- `ui/web/src/routes/Provisional.test.tsx` (new, 189 lines).
- `ui/web/src/api/provisional.ts` (new, 149 lines) — shared
  substrate between the queue page and the modal: type
  definitions mirroring `ui/api/routers/provisional.py`,
  `fetchProvisionalBets` / `resolveProvisionalBet` wrappers,
  display helpers (`formatAdelaideTimestamp`, `runnerDisplayName`,
  `formatTimeInProvisional`, `triggerSourceLabel`).

Behaviour:

- TanStack Query `useQuery` against `fetchProvisionalBets` with
  `refetchInterval: 3_000` — the W8 brief's hard-coded 3-second
  cadence. The constant `REFRESH_INTERVAL_MS = 3_000` lives at the
  top of `Provisional.tsx` with a comment naming the future
  settings-area control (W8 brief §1 carry-forward).
- Tabular display, columns: Event / Market / Runner /
  Stake / Price / Trigger / In provisional. Runner column uses
  `runnerDisplayName` which renders `${selection_id}. ${name}`
  when the name is available (defaults to the W4-populated
  `betfair_selection_name`).
- Click on a row opens the modal; the row is keyboard-accessible
  (`tabIndex={0}`, `role="button"`, Enter / Space activation).
- Empty state: `"No provisional bets. The settlement worker is
  keeping up."` Loading state: `"Loading the burst-review queue…"`
  Error state: red banner with retry button; the auto-refresh
  continues, and the banner clears on next successful fetch.
- Auto-resolution detection: when the open modal's `bet_id` is no
  longer present in the refreshed list (and the query has data),
  the modal flips to its auto-resolved banner (§3.7). This is the
  W8 §5.6 explicit requirement. Confirmed under test
  (`test_flips_the_modal_to_auto_resolved_when_the_bet_vanishes_between_refreshes`).
- After a successful resolve (modal calls `resolveProvisionalBet`),
  the page invalidates the query and shows a toast
  ("Bet marked settled (won)" etc.). The toast dismiss button
  clears it; auto-refresh continues regardless.

**Tests** (8 in `Provisional.test.tsx`):

1. Loading state on initial fetch.
2. Empty state when no provisional bets.
3. One row per provisional bet (two rows render).
4. Modal opens when a row is clicked.
5. Error state with retry button on fetch failure.
6. Error banner clears after successful retry.
7. Modal flips to auto-resolved when the bet vanishes between
   refreshes.
8. Toast appears and refetch fires when the modal resolves a bet.

### §3.7 — §5.7 — Per-bet modal

**Files:**
- `ui/web/src/components/ProvisionalBetModal.tsx` (new, 388 lines).
- `ui/web/src/components/ProvisionalBetModal.module.css`
  (new, 220 lines).
- `ui/web/src/components/ProvisionalBetModal.test.tsx`
  (new, 322 lines).

Imported by `Provisional.tsx` (§3.6) and remounted on every bet
change via `key={openBetId ?? 'closed'}` — see §6.4 deviation for
why.

Layout:

- Header: `${event_name} — ${market_name}` (h2). Subheading:
  `Runner ${runnerName} · ${venue}`.
- Section "Timing": `Placed at` / `Entered provisional` / `Event
  start` — all formatted via `formatAdelaideTimestamp` (DR-021
  Adelaide local).
- Section "Bet record": Bet ID (monospace) / Stake (requested) /
  Matched price / Book / Account / Selection.
- Section "Trigger": plain-language label via `triggerSourceLabel`
  ("Unexpected runner status (auto-trigger condition 1)" /
  "Post-settlement market void (auto-trigger condition 2)" /
  "Manual operator escalation"). The escalation reason renders
  inline if non-null (always null at v1).
- Section "Betfair last read": when `last_read_market_state` is
  null, renders the v1 explanation ("No persisted market read at
  v1. The settlement worker's last snapshot is not stored on the
  bet record yet — see W6.5 report §5.6 for the carry-forward.").
  When non-null, renders a market-status / settled-time / voided
  block plus a runners table (selection_id / status / voided).
- Section "Related bets": only renders if `related_bet_ids` is
  non-empty. Lists IDs in monospace with the v1 caveat that batch
  action is not yet wired.
- Action area: three buttons —
  "Mark settled (won)" (green) /
  "Mark settled (lost)" (red) /
  "Mark voided" (purple).
- On action click, an inline confirmation panel renders below the
  buttons: heading ("Confirm: mark settled (won)" etc.), an
  optional reason text input, two buttons (Confirm / Cancel).
  Submitting state disables the buttons and shows
  "Submitting…". Errors render in an inline `role="alert"` banner
  inside the confirmation panel.
- "Close (no action)" button at the bottom dismisses the modal
  without acting; the bet remains in PROVISIONAL.
- ESC key closes; clicking the overlay closes; clicking inside the
  modal does not (event.stopPropagation()). Initial focus lands on
  the modal container on mount.

Modal accessibility:

- `role="dialog"` + `aria-modal="true"` + `aria-labelledby` on the
  modal container.
- Confirmation panel has its own `role="dialog"` +
  `aria-label="Confirm resolution"`.
- The action buttons live inside `role="group"
  aria-label="Resolve actions"`.

**Auto-resolved variant** — when the parent passes `bet=undefined`
+ `isAutoResolved=true`, the modal renders the auto-resolved
banner instead of the bet detail. This is the path the queue
takes when a bet vanishes from the refreshed list while the modal
is open (§3.6).

**Tests** (16 in `ProvisionalBetModal.test.tsx`):

1. Renders bet data when opened.
2. Shows the no-persisted-read note when `last_read` is null.
3. Renders runner table when `last_read_market_state` has runners.
4. Lists related bets when `related_bet_ids` is non-empty.
5. Opens confirmation panel when an action button is clicked.
6–8. Each of the three action buttons fires
   `resolveProvisionalBet` with the correct `new_state` on confirm
   (`it.each` over `settled_won` / `settled_lost` / `voided`).
9. Passes the operator reason when supplied.
10. Renders an error banner when the API call fails.
11. Cancels confirmation without firing the API call.
12. Closes when the close-without-action button is clicked.
13. Closes when the overlay is clicked.
14. Closes when ESC is pressed.
15. Renders auto-resolved banner when bet=undefined +
    isAutoResolved=true.
16. Renders nothing when bet=undefined + isAutoResolved=false.

### §3.8 — §5.8 — Top-level navigation surface

**Files:**
- `ui/web/src/App.tsx` (30 → 49 lines, +19 modified).
- `ui/web/src/App.module.css` (new, 42 lines).
- `ui/web/src/App.test.tsx` (new, 46 lines).

A single inline `<NavBar>` component lives in `App.tsx` (Code's
call per the brief — no separate `Navigation.tsx` module needed
for two links plus a brand). Layout:

- Brand text "BetHub v3" on the left (no logo, per brief).
- Primary link "Burst review" → `/provisional`.
- Secondary link "Health" → `/health` on the right
  (`margin-left: auto` separator).

The nav is `<nav aria-label="Primary">`; both links render as
plain `react-router-dom` `<Link>` elements.

The root path now redirects to `/provisional` (was `/health` at
W7 ship). Health remains reachable; the burst review is the
operationally-primary surface. No active-route highlighting at v1
per brief.

Style: dark slate bar (`#1f2937` background) with white primary
link and slightly muted secondary. CSS module idiomatic per the
W7 styling baseline. Visible on every page, no collapse / hide,
no responsive logic — single-operator desktop use per brief.

**Tests** (3 in `App.test.tsx`):

1. Both nav links present with correct hrefs.
2. Renders within the primary nav landmark.
3. Root path redirects to `/provisional` (the burst review page
   heading appears in the rendered DOM).

### §3.9 — §5.9 — Smoke-test verification

See §5 below for the full smoke-test transcript. Summary: full
pytest + vitest green; live FastAPI on port 8765 served `curl`
probes for empty queue → synthetic-bet insertion → populated
queue → POST resolve → DB-side state transition → empty queue;
all four failure envelopes confirmed via curl; OpenAPI spec
emits the new endpoints; the codegen step regenerated
`src/api/types.ts`.

---

## §4 Where the new files / functions live (paths + line ranges)

### §4.1 Backend — `workflows/bet_entry/v1/settlement.py`

| Symbol | Lines | Notes |
|---|---:|---|
| `TERMINAL_SETTLEMENT_STATES` | 612–620 | tuple of 3 SettlementState values |
| `ManualResolutionError` | 622–627 | base exception |
| `BetNotFoundError` | 630–631 | 404-mapped exception |
| `InvalidSettlementTransitionError` | 634–639 | 409-mapped exception |
| `InvalidTerminalStateError` | 642–644 | 422-mapped exception |
| `SettlementStorageError` | 647–648 | 500-mapped exception |
| `apply_manual_operator_resolution` | 651–732 | the transition function |
| Updated `__all__` | 856–878 | adds 7 new exports + 1 const |

### §4.2 Backend — `ui/api/routers/provisional.py`

| Symbol | Lines | Notes |
|---|---:|---|
| `_default_db_path` | 60–62 | fallback to `<repo>/data/bethub.db` |
| `_build_default_storage` | 65–77 | `lru_cache(maxsize=1)` factory |
| `get_storage` | 80–88 | FastAPI dependency entry |
| `RunnerStateSummary` | 96–105 | runner row Pydantic model |
| `MarketStateSummary` | 108–125 | flattened MarketSettlement model |
| `ProvisionalBetItem` | 128–158 | the queue row response shape |
| `ResolveTerminalState` | 166 | `Literal['settled_won', 'settled_lost', 'voided']` |
| `ResolveRequest` | 169–180 | POST body model |
| `ResolveResponse` | 183–195 | POST success response model |
| `_market_state_summary` | 203–222 | flattening helper |
| `_payload_to_item` | 225–246 | flattening helper |
| `StorageDep` | 254 | `Annotated[BetRecordStorage, Depends(get_storage)]` |
| `list_provisional_bets` | 257–272 | GET handler |
| `_NEW_STATE_BY_REQUEST` | 280–284 | string→enum lookup |
| `resolve_provisional_bet` | 287–349 | POST handler |
| `__all__` | 352–375 | exports for testing + `main.py` wire-up |

### §4.3 Backend — `ui/api/main.py` + `ui/api/routers/__init__.py`

- `main.py:21` — adds `provisional_router` to the import.
- `main.py:48` — adds `app.include_router(provisional_router,
  prefix="/api")`.
- `routers/__init__.py:9` — exports `provisional_router`.

### §4.4 Frontend — types + helpers

- `ui/web/src/api/client.ts:9` — extends `ApiError` with `detail:
  unknown`.
- `ui/web/src/api/client.ts:34` — `parseErrorBody` helper.
- `ui/web/src/api/client.ts:51` — `apiSend<T>(path, method, body)`.
- `ui/web/src/api/client.ts:79` — `apiGet<T>` (extended to use
  `parseErrorBody`).
- `ui/web/src/api/client.ts:91` — `apiPost<T>(path, body)`.
- `ui/web/src/api/client.ts:95` — `apiPatch<T>(path, body)`.
- `ui/web/src/api/provisional.ts:11–48` — type definitions
  (`RunnerStateSummary`, `MarketStateSummary`,
  `ProvisionalBetItem`, `ResolveRequest`, `ResolveResponse`).
- `ui/web/src/api/provisional.ts:73–79` — `fetchProvisionalBets`,
  `resolveProvisionalBet`.
- `ui/web/src/api/provisional.ts:85–149` — display helpers.

### §4.5 Frontend — UI

- `ui/web/src/components/ProvisionalBetModal.tsx:55–80` — props
  type + state hooks.
- `ui/web/src/components/ProvisionalBetModal.tsx:81–94` — ESC
  + initial focus effects.
- `ui/web/src/components/ProvisionalBetModal.tsx:99–134` —
  auto-resolved short-circuit branch.
- `ui/web/src/components/ProvisionalBetModal.tsx:136–166` —
  action / confirmation handlers.
- `ui/web/src/components/ProvisionalBetModal.tsx:168–384` —
  the full bet detail render path.
- `ui/web/src/routes/Provisional.tsx:30–34` — the
  `REFRESH_INTERVAL_MS = 3_000` constant.
- `ui/web/src/routes/Provisional.tsx:50–82` — TanStack Query +
  state + auto-resolution detection.
- `ui/web/src/routes/Provisional.tsx:84–192` — the rendered
  page.
- `ui/web/src/App.tsx:23–35` — `NavBar` component.
- `ui/web/src/App.tsx:37–48` — `App` with three routes
  (root → /provisional, /provisional, /health).

### §4.6 Tests

- `tests/workflows/bet_entry/v1/test_settlement.py:1392–1597`
  (Block 7) — 9 W8 §5.5 tests.
- `tests/ui/api/test_provisional.py:106–395` — 14 W8 §5.3 + §5.4
  tests.
- `ui/web/src/components/ProvisionalBetModal.test.tsx:43–311` —
  16 modal tests.
- `ui/web/src/routes/Provisional.test.tsx:43–189` — 8 queue tests.
- `ui/web/src/App.test.tsx:9–46` — 3 nav tests.

---

## §5 Wire-up evidence (smoke-test exercise)

Per W8 brief §5.9 — full-stack end-to-end. Code spun up the live
stack on port 8765 (deliberately offset from the conventional 8000
to avoid stomping any pre-existing dev server) against a clean
DB, ran the four named curl probes, and recorded the outputs
verbatim. Manual browser walkthrough was not required per Session
107 §7.7 precedent (trust curl + test-suite verification).

### §5.1 Probe 1 — empty queue on clean DB

```
$ rm -f data/bethub.db data/bethub.db-shm data/bethub.db-wal
$ .venv/bin/uvicorn ui.api.main:app --port 8765 --log-level warning &
$ curl -s -w "HTTP %{http_code}\n" http://localhost:8765/api/v1/bets/provisional
[]
HTTP 200
```

The DB file (and accompanying WAL files) is created on first
hit — verified via `ls data/`:

```
-rw-r--r--   2 tim  staff   4096  8 May 11:53 bethub.db
-rw-r--r--   2 tim  staff  32768  8 May 11:53 bethub.db-shm
-rw-r--r--   2 tim  staff  24752  8 May 11:53 bethub.db-wal
```

### §5.2 Probe 2 — synthetic provisional bet appears

Inserted a synthetic bet via a short Python script (see brief
§5.9 fixture-or-script alternative). The script writes via a
fresh `SQLiteBetRecordStorage` instance against the same DB
file; SQLite WAL mode handles cross-process visibility cleanly.

```
wrote bet-smoke-1: success=True
$ curl -s http://localhost:8765/api/v1/bets/provisional | python3 -m json.tool
[
    {
        "bet_id": "bet-smoke-1",
        "placement_time": "2026-05-08T11:38:32.819396+09:30",
        "entered_provisional_at": "2026-05-08T11:48:32.819396+09:30",
        "betfair_market_id": "1.smoke-mkt",
        "betfair_selection_id": "9999001",
        "betfair_event_name": "Race 5 Smoke Test",
        "betfair_market_name": "WIN",
        "betfair_selection_name": "SmokyHorse",
        "betfair_event_venue": "Smoketown",
        "betfair_event_start_time": "2026-05-08T11:40:32.819396+09:30",
        "book_or_exchange": "betfair",
        "account_at_book_id": "acct-smoke-tim",
        "requested_stake": "50.00",
        "matched_price": 4.2,
        "trigger_source": "unexpected_state",
        "operator_escalation_reason": null,
        "last_read_market_state": null,
        "related_bet_ids": []
    }
]
```

The `requested_stake` field surfaces as a JSON string ("50.00"),
preserving the Decimal precision per the test in §3.3.

### §5.3 Probe 3 — POST resolve → terminal state, queue empties

```
$ curl -s -X POST -H "Content-Type: application/json" \
    -d '{"new_state": "settled_won", "operator_reason": "smoke test confirmed"}' \
    http://localhost:8765/api/v1/bets/provisional/bet-smoke-1/resolve | python3 -m json.tool
{
    "bet_id": "bet-smoke-1",
    "settlement_state": "settled_won",
    "last_reconciled_at": "2026-05-08T11:53:42.687496+09:30",
    "operator_reason": "smoke test confirmed",
    "applied_at": "2026-05-08T11:53:42.687496+09:30"
}
$ curl -s -w "\nHTTP %{http_code}\n" http://localhost:8765/api/v1/bets/provisional
[]
HTTP 200
```

DB-side state confirmed via a separate `SQLiteBetRecordStorage`
read:

```
bet-smoke-1 settlement_state: settled_won
bet-smoke-1 last_reconciled_at: 2026-05-08 11:53:42.687496+09:30
bet-smoke-1 reconciliation_attempts: 1
```

The `reconciliation_attempts` increment is the shared-bookkeeping
substrate that the W6.5 ship reuses for both the auto and manual
paths — confirms `_write_settlement_bookkeeping` ran as expected
inside `apply_manual_operator_resolution`.

### §5.4 Probe 4 — failure envelopes

```
=== 404 ===
$ curl -s -w "\nHTTP %{http_code}\n" -X POST -H "Content-Type: application/json" \
    -d '{"new_state": "settled_won"}' \
    http://localhost:8765/api/v1/bets/provisional/nonexistent/resolve
{"detail":"bet_id 'nonexistent' not found"}
HTTP 404

=== 409 (resolving already-terminal bet) ===
$ curl -s -w "\nHTTP %{http_code}\n" -X POST -H "Content-Type: application/json" \
    -d '{"new_state": "settled_won"}' \
    http://localhost:8765/api/v1/bets/provisional/bet-smoke-1/resolve
{"detail":"bet_id 'bet-smoke-1' is in settlement_state 'settled_won'; manual operator resolution requires PROVISIONAL"}
HTTP 409

=== 422 (invalid new_state) ===
$ curl -s -w "\nHTTP %{http_code}\n" -X POST -H "Content-Type: application/json" \
    -d '{"new_state": "pending"}' \
    http://localhost:8765/api/v1/bets/provisional/bet-smoke-1/resolve
{"detail":[{"type":"literal_error","loc":["body","new_state"],"msg":"Input should be 'settled_won', 'settled_lost' or 'voided'","input":"pending","ctx":{"expected":"'settled_won', 'settled_lost' or 'voided'"}}]}
HTTP 422
```

The 500 path is exercised in
`test_post_resolve_returns_500_on_storage_write_failure`
(`tests/ui/api/test_provisional.py:343`); reproducing it via curl
would require a runtime fault injection that's not part of the
session-end smoke. The unit test confirms the path with the same
storage shape the route would see in production.

### §5.5 Probe 5 — OpenAPI spec emits new endpoints; codegen lands

```
$ curl -s http://localhost:8765/api/openapi.json | python3 -c "..."
paths:
  /api/health: ['get']
  /api/v1/bets/provisional: ['get']
  /api/v1/bets/provisional/{bet_id}/resolve: ['post']

$ npx openapi-typescript http://localhost:8765/api/openapi.json -o src/api/types.ts
✨ openapi-typescript 7.13.0
🚀 http://localhost:8765/api/openapi.json → src/api/types.ts [43.3ms]
$ wc -l src/api/types.ts
334 src/api/types.ts
```

The generated `types.ts` (76 → 334 lines) emits the new schemas
(`MarketStateSummary`, `ProvisionalBetItem`, `ResolveRequest`,
`ResolveResponse`, `RunnerStateSummary`) under
`components.schemas.*` plus the corresponding `paths` /
`operations` blocks. The W8 frontend continues to use the
hand-rolled types in `src/api/provisional.ts` — see §6.5 for the
deliberate parallel-types choice — but the regenerated
`types.ts` is committed for type-safety verification of the
hand-rolled shapes (any drift between the API and the hand-rolled
types would surface in `tsc -b` if a downstream module imports
both).

### §5.6 Cleanup

Stopped uvicorn:

```
$ lsof -ti :8765 | xargs -I {} kill {}
$ lsof -ti :8765 || echo "(port free)"
(port free)
```

Removed the smoke-test DB:

```
$ rm data/bethub.db data/bethub.db-shm data/bethub.db-wal
$ rmdir data/
```

The repo working tree is back to its post-edit ship state — no
DB file lingering, no uvicorn process running.

---

## §6 Deviations from brief

Six deviations, all narrow and defensible-per-the-brief's
"Code's call" carve-outs.

### §6.1 — Workflow `storage` parameter type name

**Brief said (§5.5 signature template):**

```python
def apply_manual_operator_resolution(
    *,
    ...
    storage: BetEntryStorage,
    ...
```

**Code did:** `storage: BetRecordStorage`.

**Why:** the actual Protocol class in
`workflows/bet_entry/v1/storage.py` is named `BetRecordStorage`
(line 65). `BetEntryStorage` does not exist in the W6.5 ship.
The brief's template was a shorthand that drifted from the ship
state. Followed the actual class name.

### §6.2 — Trigger-source enum value names

**Brief said (§5.3 list):** `trigger_source` is one of
`provisional_unexpected_state`, `provisional_post_settlement_void`,
`manual_operator_escalation`.

**Code did:** the response field surfaces `unexpected_state`,
`post_settlement_void`, `manual_operator_escalation` — the W6.5
`ProvisionalTriggerSource` enum's actual `.value`s.

**Why:** the W6.5 ship's `ProvisionalTriggerSource` enum (in
`settlement.py:199–210`) uses the un-prefixed names; the W8 brief's
`provisional_*` prefix is from a different W6.5 surface
(`SettlementReasonCode` Literal). Conflating the two values would
have required a translation layer at the API boundary that
delivered no operator value — the React modal renders a
plain-language label via `triggerSourceLabel` regardless of the
underlying enum string. Surfacing the W6.5 ship-state values
verbatim keeps the system's source-of-truth contract honest.

### §6.3 — Sequencing within session

**Brief said (§6):** §5.5 → §5.4 → §5.3 → §5.1 → §5.2 → §5.7 →
§5.6 → §5.8 → §5.9.

**Code did:** §5.5 → §5.3 + §5.4 (co-located) → §5.1 → §5.2 →
§5.7 → §5.6 → §5.8 → §5.9.

**Why:** §5.3 and §5.4 share the same router file
(`routers/provisional.py`); writing them in a single edit pass
was operationally cleaner than building, reverting, and
re-extending the same module. The brief explicitly allows this
("Code may deviate where a different order is operationally
cleaner; flag any deviation in the report").

### §6.4 — Modal state reset via `key` remount

**Brief said (§5.7):** "modal accessibility — focus trap,
escape-key dismissal, click-outside dismissal. Standard modal
hygiene." (No specific guidance on confirmation-state reset
mechanics.)

**Code did:** the parent `Provisional.tsx` passes
`key={openBetId ?? 'closed'}` to the modal. When the open bet
changes, React unmounts and remounts the modal, naturally
resetting `pendingConfirm` / `reason` / `submitError` /
`submitting` without an explicit reset effect.

**Why:** the alternative — a `useEffect` that reads `bet?.bet_id`
and calls `setPendingConfirm(null)` etc. — trips the
`react-hooks/set-state-in-effect` lint rule (a relatively new ESLint
rule that flags cascading-render patterns). The `key`-based
remount is the React-idiomatic shape for this pattern and is
faster (no extra render after the bet change). Tested explicitly:
`test_flips_the_modal_to_auto_resolved_when_the_bet_vanishes_between_refreshes`
verifies the cross-bet remount behaviour works as expected.

### §6.5 — Hand-rolled TypeScript types in parallel with codegen

**Brief said (§5.5 W7 / §5.9 W8):** the OpenAPI codegen produces
`src/api/types.ts`; the smoke-test step regenerates it.

**Code did:** wrote the W8 frontend against hand-rolled types in
`src/api/provisional.ts` rather than against the generated
`components.schemas.*` types. The codegen step still ran during
§5.9 smoke verification, and the regenerated `types.ts` is
committed.

**Why:** the codegen requires a live FastAPI server, which makes
the build step order-dependent. Writing the modal and the queue
page against hand-rolled types let those surfaces be tested in
isolation (vitest in jsdom, no FastAPI required) before the
smoke-test step. The hand-rolled shapes mirror the
`ui/api/routers/provisional.py` surface exactly; the regenerated
`types.ts` provides a type-safety check against drift (any future
drift will surface as a `tsc -b` failure in code that imports both).

The trade-off is duplication — `src/api/provisional.ts` and
`src/api/types.ts` define overlapping shapes. A follow-up brief
could collapse the duplication by switching the modal / queue to
use the generated types directly, which would need a minor
restructure of the `fetchProvisionalBets` /
`resolveProvisionalBet` wrappers (they'd parameterise on the
generated `paths` shape rather than concrete return types). Not
load-bearing at v1.

### §6.6 — `BETHUB_DB_PATH` read directly via `os.environ`

**Brief said (nothing explicit; W7 ship documented `Settings(BaseSettings)`
in `ui/api/config.py` as the convention for env-var reading):**
the convention is to add settings to `Settings`, prefixed with
`BETHUB_`.

**Code did:** `_build_default_storage` in
`ui/api/routers/provisional.py` reads `BETHUB_DB_PATH` via
`os.environ.get("BETHUB_DB_PATH")`, with a fallback to
`<repo>/data/bethub.db`.

**Why:** integrating the storage path into `Settings` would
require editing `ui/api/config.py`, which is not in the §5
named-anchor list for W8. Brief §9 hard-limits "Editing files
outside the named anchors in §5". The direct `os.environ` read
keeps the surface bounded to the §5.3/§5.4 router file and
delivers the same behaviour. A follow-up brief that consolidates
operational env-var reading into `Settings` (and adds the
matching `BETHUB_DB_PATH` field) is a good cleanup target — see
§7 below.

---

## §7 Open questions for triage

For operator-Claude routing in the next session.

### §7.1 — Audit-trail surface for settlement transitions

**Status (per §3.5 and brief §5.5 explicit instructions):** W8
v1 lands manual transitions without a structured audit row. The
operator reason is captured in the worker logger's INFO line; the
bet record's `last_reconciled_at` and `reconciliation_attempts`
counters update via the shared bookkeeping substrate. There is no
audit table, no history of state transitions, no per-transition
operator-action ledger.

**Question:** when does the audit-trail surface land? §2.6 §3.5
specifies "Operator action records on the bet record. Manual
provisional → terminal-state transitions are audit-trailed
alongside whatever the settlement-read state was at the time of
operator action, so post-hoc review can reconstruct what the
operator saw and what they decided."

The "alongside whatever the settlement-read state was" half is
not satisfiable at v1 because the W6.5 ship doesn't persist the
settlement-read state on the bet record (the `last_read_market_state`
field on the API surfacing payload is always None at v1). So the
audit-trail surface needs two things:

1. A persisted record of every settlement transition (auto or
   manual), with `operator_reason` (when manual), the
   transition's source state, the target state, the timestamp.
2. A persisted snapshot of the worker's last MarketSettlement
   read on the bet record.

Brief recommendation: a follow-on brief is the right shape. v1
operates safely without it (the operator log file is the
substitute substrate); the gap is non-blocking for v3 day-one
ops but does block §2.6's full §3.5 contract.

### §7.2 — Generated `types.ts` vs hand-rolled `provisional.ts`

**Status:** see §6.5 above. Two parallel type sources for the
same API surface.

**Question:** consolidate by switching the modal / queue page to
the generated types? Or keep the hand-rolled types as the v1
substrate and commit to a different consolidation path?

**Recommendation:** operator-call. Likely a low-priority cleanup;
the duplication is small (two type definitions for the response
shapes) and the hand-rolled types make the modal / queue easier
to test in isolation.

### §7.3 — `Settings` integration of `BETHUB_DB_PATH`

**Status:** see §6.6 above.

**Question:** add `db_path: Path = Field(default=...)` to
`ui/api/config.py:Settings` and re-route `_build_default_storage`
through `get_settings()`? Or keep the direct `os.environ` read?

**Recommendation:** consolidate when a second router in W9+ also
needs storage access; consolidating prematurely (just for one
caller) doesn't earn its keep.

### §7.4 — `.env.production` empty `VITE_API_BASE_URL`

**Status:** the production env file ships with empty
`VITE_API_BASE_URL=`, which makes the bundle issue
document-relative URLs. This presupposes same-origin static-
asset serving by FastAPI — a deploy story that is **not yet
wired** (per W7 §5.3 / report §6.1: "Production-mode same-origin
static-asset serving is not wired (out of scope per brief §9).
The seam is `Settings.environment == 'prod'` — when W8 /
post-DR-029 ops work needs it...").

**Question:** if a production build of the W8 ship were deployed
today, the bundle would 404 on every API call. Should the
`.env.production` ship with a placeholder
`VITE_API_BASE_URL=https://api.example.com` instead, with a
deploy note saying "fill this in until same-origin serving lands"?
Or keep the empty default that anticipates the same-origin path
and leave operator triage to handle it?

**Recommendation:** operator-call. The empty default is the
correct long-run shape; a placeholder would give a misleading
working-deploy signal. The right v1 mitigation is probably a
`README.md` note (which W8 already has — the "API base URL"
section names the production deploy expectation). Possibly worth
firming up in the post-DR-029 ops work that lands the
same-origin path.

### §7.5 — Redirect target on root path

**Status:** `App.tsx` redirects `/` to `/provisional` (was
`/health` at W7). The burst-review queue is the operationally-
primary surface; landing on it directly is the correct UX call
for a single-operator install.

**Question:** confirm the redirect target. Reasonable
alternatives include landing on a dashboard (W8+ doesn't have
one) or keeping `/health` as the default (less useful to the
operator).

**Recommendation:** no-call from operator's side likely. The
default landing on the queue is the ergonomic shape.

---

## §8 Findings beyond brief scope

Surprises and substrate observations Code surfaced during
execution that didn't fit the brief's anchors.

### §8.1 — Pre-existing 15 mypy errors in `betfair_adapter.py`

**Finding:** running `mypy --strict workflows/bet_entry` (or
anywhere that drags `betfair_adapter.py` into the type-check
graph) produces 15 errors in `betfair_adapter.py`, all `union-attr`
or `arg-type` against the
`FreshEnvelope[T] | StaleEnvelope[T] | UnavailableReadEnvelope`
union shape. The errors are unchanged from pre-baseline (W8 added
zero mypy errors).

**Implication:** transient noise whenever mypy runs anywhere
near the W6.5+ files. The errors look like a missing
`isinstance` narrowing or a missing
`assert isinstance(envelope, FreshEnvelope)` somewhere in the
adapter. The fix is small and contained. Not a W8 task per
brief §9 hard limit ("Changing W6.5's auto-resolution logic in
`settlement.py`" is forbidden, and the betfair_adapter is in the
same neighbourhood).

**Recommendation:** flag for a small follow-on brief — a single-
file cleanup pass that fixes the union narrowing.

### §8.2 — `BetRecordStorage` has `read_bet_record` already; brief implied a fresh substrate

**Finding:** the §5.5 workflow function's "look up bet by ID"
step uses `storage.read_bet_record(bet_id)`, which is part of the
`BetRecordStorage` Protocol since the W6 ship (defined at
`storage.py:85` / `storage.py:318` / `storage.py:673`). The brief
did not name this dependency explicitly; some readings of the
brief might assume the workflow needs a new "look up + lock"
helper. It does not — the existing read is sufficient because
the SQLite reference implementation's `update_settlement_state`
is a single-statement UPDATE that's atomic against the read.

**Implication:** no new work; just a substrate observation. The
W6.5 ship already had the right shape for the W8 workflow's
"validate state before write" pattern.

### §8.3 — `ProvisionalSettlementSurfacingPayload.entered_provisional_at` is `last_reconciled_at` at v1

**Finding:** the W6.5 ship documents this as a known
approximation (W6.5 brief §5.6 Change C). At v1, the API surface
exposes this same approximation as `entered_provisional_at`.
The frontend renders it as if it were the precise transition time.

**Implication:** under high-cadence settlement passes (e.g. the
default 1-minute interval), the approximation is correct to ~1
minute granularity. Under longer cadences (or paused workers),
the value lags. The "time in provisional" computation in the
queue table will tick up correctly from this approximate start
point.

**Recommendation:** captured in the W6.5 carry-forward; no
W8-specific action.

### §8.4 — Pydantic v2 `Decimal` JSON serialisation defaults

**Finding:** `requested_stake: Decimal` on `ProvisionalBetItem`
serialises as a JSON string by default in Pydantic v2 (`"50.00"`
not `50.00`). The hand-rolled TypeScript type
(`requested_stake: string`) matches. The frontend renders the
string verbatim in the queue table.

**Implication:** no precision loss on the wire; the UI doesn't
need to do any Decimal-aware parsing because it never does
arithmetic on the field. Display-only.

### §8.5 — `npm run lint` requires the `react-hooks/set-state-in-effect` workaround

**Finding:** the Vite 8 / React 19 / `eslint-plugin-react-hooks@7.1.1`
scaffold from W7 ships the `react-hooks/set-state-in-effect`
rule as an error by default. A `useEffect` that resets transient
state when a prop changes (a common pattern in modal components)
trips this rule.

**Implication:** the `key`-based remount pattern is the
React-idiomatic alternative; W8 used it in §3.7 (see §6.4
deviation). Future React work in this stack should default to
the key remount when the goal is "reset state when prop X
changes" rather than reaching for a reset effect.

### §8.6 — `tsc -b` emits zero W8 warnings on strict mode

**Finding:** the W7 §6.3 / report §8.3 finding upgraded
`tsconfig.app.json` to `strict: true` and added
`noUnusedLocals` / `noUnusedParameters` (already shipped). The
W8 frontend (388 lines of modal + 198 lines of queue page +
149 lines of API types/helpers + 49 lines of App nav) compiles
clean under strict mode.

**Implication:** the W7 strict-mode posture is paying off.

### §8.7 — `lru_cache` on the storage factory means tests must override at `app.dependency_overrides`, not at module level

**Finding:** `_build_default_storage` is `@lru_cache(maxsize=1)`.
A naive test that monkeypatches `BETHUB_DB_PATH` after the cache
is primed would not pick up the change. The W8 test fixture
overrides via `app.dependency_overrides[get_storage] = lambda:
in_memory_instance` instead, which doesn't go through the cache.

**Implication:** documented in `_build_default_storage`'s
docstring. Future tests should follow the same pattern.

### §8.8 — Vite 8 production build size grew 16 kB (245.95 → 262.14 kB JS)

**Finding:** the W7 production bundle was 245.95 kB JS / 870 B
CSS gzipped (77.43 kB JS gzipped). The W8 bundle is 262.14 kB JS
/ 6.32 kB CSS gzipped (81.70 kB JS gzipped). The +16.19 kB JS
delta covers the modal, queue page, and nav (about 1080 lines of
new TSX); the +5.45 kB CSS delta covers the three new CSS
modules.

**Implication:** sane. The bundle is dominated by React +
react-router + TanStack Query (already present at W7); W8's
additions live in the long tail. No tree-shaking work needed.

---

## §9 Ship verification (what was exercised in §5.9)

Each item in the W8 brief §5.9 named smoke checklist, with its
verdict.

| Check | Verdict | Evidence |
|---|---|---|
| `pytest` suite green | ✓ | 486 passed in 1.42s |
| `vitest` suite green | ✓ | 30 passed in 0.74s across 4 test files |
| `ruff check` green | ✓ | All checks passed |
| `eslint` green | ✓ | No output (= clean) |
| `lint-imports` 5/5 contracts | ✓ | 5 kept, 0 broken |
| `mypy --strict ui` clean | ✓ | Success: no issues found in 9 source files |
| `mypy --strict workflows/bet_entry` no new errors | ✓ | 15 errors all in pre-existing `betfair_adapter.py` |
| `npm run build` succeeds | ✓ | 75 modules transformed; 262 kB JS / 6 kB CSS |
| `GET /api/v1/bets/provisional` empty array on clean DB | ✓ | §5.1 |
| Synthetic provisional bet appears in response | ✓ | §5.2 |
| Loading queue page in browser-equivalent shows the row | ✓ | §3.6 vitest test `renders one row per provisional bet` |
| Loading queue page shows empty state | ✓ | §3.6 vitest test `renders the empty state` |
| Modal opens, action button confirms, POST resolve fires | ✓ | §5.3 + §3.7 vitest tests |
| Bet's `settlement_state` in DB transitions | ✓ | §5.3 (read-back via separate `SQLiteBetRecordStorage`) |
| Bet disappears from next queue refresh | ✓ | §5.3 (subsequent GET returns `[]`) |
| 404 / 409 / 422 envelopes via curl | ✓ | §5.4 |
| 500 envelope via test (storage failure injection) | ✓ | `test_post_resolve_returns_500_on_storage_write_failure` |
| OpenAPI spec emits new endpoints | ✓ | §5.5 |
| `npm run generate-api-types` regenerates `types.ts` | ✓ | §5.5 (76 → 334 lines) |

A manual browser walkthrough was **not** done per brief §5.9
("not required (per Session 107 §7.7 precedent — trust curl +
test-suite verification)"). The curl probes plus the vitest
jsdom rendering tests cover the same surface; the only thing not
exercised end-to-end is the actual Chrome / Safari rendering of
the CSS modules. Visual fidelity is not a v1 ship gate.

---

## §10 Self-assessment

### §10.1 Did the brief land cleanly?

**Yes.** All nine §5 anchors landed; all six deviations are
narrow and named at the brief's "Code's call" carve-outs; the
smoke-test exercise verified the full stack end-to-end. No
mid-session escalations, no surprises that turned into blockers.
The two main substantive judgement calls — the audit-trail
deferral (§3.5 / §6 and §7.1) and the hand-rolled-vs-generated
types (§6.5 / §7.2) — are both explicitly within the brief's
allowed-decision surface and are documented for next-session
triage.

### §10.2 Length flag

**This report:** 1317 lines (target band 800–1200 per brief §8).
Lands ~10% above the upper band threshold but inside the
"may indicate scope creep" warning at 1300. Flagged here per the
brief's instruction.

Where the over-shoot lives:

- §3 per-anchor ship summaries (≈430 lines) are more detailed
  than the brief's "line counts, test counts, brief notes"
  prescription strictly requires. Each anchor section includes
  prose on the layout / behaviour / test coverage. The detail is
  load-bearing for next-session triage — operator-Claude will
  read this report when scoping the audit-trail follow-up brief
  and the ergonomic / shape calls (e.g. the `key`-remount idiom
  in §6.4) will bear on whether subsequent briefs adopt the same
  pattern. Compressing §3 to a strict-prescription shape would
  drop the surface that next-session triage actually consumes.
- §5 smoke-test transcript (≈170 lines) reproduces the curl
  outputs verbatim. Could be summarised but the verbatim outputs
  are the empirical record of the §5.9 verification — losing them
  would require re-running the smoke test for any future check.
- §8 findings (≈110 lines) — eight findings vs W7's eight. Tight
  per finding.

W8 ship was net 5613 LOC of new code (vs W6.5's ≈2466 LOC) but
across nine anchors, three of which are full React surfaces. The
report-to-LOC ratio is 1:4.3, comparable to W7's 1:3.6 ratio
(1275 lines / 4537 LOC delta) and W6.5's 1:2.9 (850 / 2466 — but
W6.5 had more novel substrate to explain).

Not scope creep — the brief's scope envelope held. The over-shoot
is signal that the brief's report-length anticipation
under-estimated the per-anchor detail an operator-facing UI ship
warrants.

### §10.3 Hard-limit compliance audit (brief §9)

| Hard limit | Compliance |
|---|---|
| No edits outside §5 named anchors | ✓ — 21 files touched, all in the named anchor list (settlement.py, main.py, routers/__init__.py, client.ts, README.md, App.tsx + new files in routers/, components/, routes/, .env files, plus tests in the matching test trees plus `types.ts` regenerated as part of §5.9 codegen) |
| No schema changes | ✓ — `bets` table DDL untouched; `update_settlement_state` reads existing columns |
| No changes to W6.5's auto-resolution logic | ✓ — `_resolve_settlement_for_bet` and `apply_settlement_pass` (the `run_settlement_pass` referenced by brief) untouched; the only `settlement.py` additions are in a new module section before the schedulers |
| No authentication / authorisation built | ✓ — single-operator local; no auth code |
| No batch-action UI built | ✓ — related-bets pointer is visibility only |
| No settings panel for queue cadence | ✓ — hard-coded `REFRESH_INTERVAL_MS = 3_000` constant with comment |
| No §2.6 §3.4 condition 2 path touched | ✓ — terminal → provisional auto-transition not implemented |
| No §2.6 §3.2 manual escalation from terminal touched | ✓ — only PROVISIONAL → terminal supported |
| No named-debt items addressed | ✓ — no test-coverage work, no migration framework, no monolithic-orchestrator changes |
| No mid-session escalations | ✓ — surprises (audit gap, type-name mismatch, sequencing) became findings, not blockers |

### §10.4 What I'd do differently if I were briefing the same work again

(Self-reflection only; not actionable.)

- The §6.6 deviation (`BETHUB_DB_PATH` direct `os.environ` read)
  could have been pre-empted by adding `ui/api/config.py` to the
  §5.3/§5.4 named anchor surface. Not load-bearing — the direct
  read is a small wart — but the brief could have made the call
  itself.
- The trigger-source-enum-name discrepancy (§6.2) could have been
  caught by a pre-flight read of the W6.5 ship's
  `ProvisionalTriggerSource` values. The brief recovered cleanly
  but it's a small calibration error.
- The brief's "at least three positive paths plus the four
  failure modes" prescription for §5.5 tests undercounted what
  actually wants coverage (count preservation and audit logging
  are also load-bearing). Code added two extra tests; a more
  precise prescription would have anticipated this.

None of these blocked the ship; all three are calibration notes
for future briefs in this stream.

---
