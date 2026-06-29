# W17.1 Brief — Racing pages live-readiness (surgical follow-up)

**Drafted:** Session 147, 2026-06-13 ACST.
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3/`.
**Parent:** W17 brief (`w17_brief.md`, locked S146) + W17 report
(`w17_report.md`, delivered 2026-06-13).
**Type:** Surgical fix bundle + deployment wiring. Single bounded
Code session.

---

## §1 — What this brief is and is not

This is a surgical follow-up to W17. It closes the gap between
"W17 delivered, mock-tested" and "racing page live-usable and
safe for the operator's first real session". Six items, all named
in the W17 report's findings (F2, F5, F6, F7-partial, F8, F9).

It is NOT a feature build, NOT a layout/density pass, and NOT a
live-validation session. Code writes and tests the wiring; the
operator performs all live Betfair interaction personally,
post-delivery, per §4.

Single bounded Code session. Surprises become findings in the
report, not blockers and not scope expansion. If the work does
not fit one session, stop at a coherent boundary (per §6
priority) and report.

## §2 — Why this work exists

W17 delivered the full racing page (report §1: 917/0 pytest,
77/0 vitest, all eleven §5 sub-sections). Four findings block or
degrade safe live use:

- **F2** — logging a free-bet does not write the
  `free_bet_deployed` event, so a deployed FB keeps appearing as
  available inventory in the log panel.
- **F5** — the bet-log POST has no idempotency protection on the
  wire; a timeout-and-retry could double-log a bet.
- **F6** — the quick-lay flow asks the operator to paste a raw
  Betfair account-at-book UUID (placeholder prompt-modal).
- **F7 (partial)** — two preserved-v2 stake behaviours are absent
  from the HedgeModal first cut: the $50 default stake on
  bonus-winnings cash bets (a named v2 safety behaviour per the
  W17 brief §5.4/§5.11) and FB stake rounding to $5. In-modal
  price freshness (~500 ms lay polling while open) is also
  absent; placing a lay off a stale price near the jump is an
  operational risk.

Two further findings block live operation entirely:

- **F8** — `list_racing_markets` has no `_translation.py`
  wiring to Betfair's `listMarketCatalogue`.
- **F9** — no production composition root: the FastAPI app has
  no real dependency wiring (Betfair client, streaming client,
  storage, DB connection), so the page cannot run against live
  systems at all.

W16 cutover is blocked on W17 being validated live; this brief
is the remaining build work before that validation can happen.

## §3 — Pre-reads

Required, in order:

1. This brief, end-to-end, before any edit.
2. `dr029/w17_racing_pages/w17_report.md` — §5 findings F2,
   F5–F9 (the substrate for every item below).
3. `dr029/w17_racing_pages/w17_brief.md` §4 (bet-safety rules),
   §5.4, §5.10, §5.11 (the behaviours being completed).
4. `contracts/betfair_client_contract.md` §9.9 (the listing
   surface F8 wires) and §9.5 (placement, for §5.6 wiring).

Reference-only (open on demand):

- `dr029/w17_racing_pages/scope_settlement.md`.
- `dr029/m1_maintenance/m1_report.md` (Alembic + baseline
  context; pytest standing baseline is now 917/0 post-W17).

## §4 — System access and bet safety

- Mac filesystem, read-write, v3 repo only
  (`/Users/tim/Desktop/Projects/bethub-v3/`).
- **Zero live Betfair API access. Zero order placement. The
  hard rule from W17 §4 carries unchanged.** All wiring in
  §5.5/§5.6 is written and tested against mocks/fakes. The
  operator performs the first live read and the first live ⚡
  lay personally, post-delivery, using the go-live runbook the
  report provides (§8).
- No v2 access. No VPS access. No capture.db access (DR-027/
  DR-028: this is operational-line work only).
- Operator's live DB: never touched. Scratch DBs in /tmp only.
- Adelaide local timestamps (ACST/ACDT) per DR-021 in the
  report.

## §5 — Scope

Six items. Each names its anchors; named anchors only.

### §5.1 — Free-bet deployment event write (closes F2)

Add a small write surface in the workflows layer, called by the
bets route, so logging an FB bet supersedes the consumed credit.

- New function in `workflows/promos/v1` (suggested:
  `record_free_bet_deployment(...)` in a new thin module or in
  `promo_store_adapter.py`'s module scope — Code's call, DR-030
  layering respected: ui/api → workflows → store).
- Behaviour: for each id in `consumed_credit_event_ids`,
  construct a `free_bet_deployed` event (enum value exists at
  `store/schema/promos.py:102`; domain models in
  `domain.promos`; adapter note at
  `promo_store_adapter.py:481`) with `supersedes_event_id`
  linking the credit, correlation to the bet record's id, and
  append via `PromoStoreAdapter.append_event`.
- Call site: `ui/api/routers/racing.py` POST `/bets` handler —
  after a successful bet-record write, before the response.
  Event-write failure after a successful bet write must NOT
  fail the response: return success with a `warnings` entry
  (`FB_DEPLOY_EVENT_WRITE_FAILED`) so the operator sees it.
- Effect to verify: `compute_free_bet_inventory` no longer
  returns the consumed credit after the bet is logged
  (this is the W17 report §4 walkthrough step 4 quirk closing).
- Tests: workflows-level unit test (event chain shape) + route
  test (inventory drops after FB bet logged; warning path).

### §5.2 — Idempotency threading on `/bets` (closes F5)

- Client: `LogBetPanel.tsx` already regenerates
  `idempotencyKey` after success. Thread it onto the POST body
  as `idempotency_key` (string) via `ui/web/src/api/racing.ts`.
- Server: in the `/bets` route, derive the bet record id
  deterministically from the key (uuid5 against a fixed
  namespace constant is the suggested shape) so a retried POST
  with the same key produces the same `bet_id`. On a
  primary-key conflict at the storage layer, return the
  existing record as success (HTTP 200, `duplicate: true` in
  the body) rather than erroring or double-writing.
- Tests: route test posting the same body+key twice asserts one
  row, second response flagged duplicate; differing keys assert
  two rows. Frontend test asserting the key rides the body and
  regenerates after success.

### §5.3 — Betfair account-at-book selector (closes F6)

- Replace the `PromptBetfairAccount` placeholder modal in
  `HedgeModal.tsx`.
- Source: the existing `GET /api/v1/racing/accounts` listing —
  filter to the Betfair book's accounts-at-book. If the listing
  body lacks a usable book discriminator, extend the response
  (additive only) rather than adding a new endpoint.
- UI: a "Betfair account" picker, either in the HedgeModal
  header or alongside the log panel's account picker — Code's
  call on placement; density posture per W17 §5.1 applies.
- Selection persists for the browser session (component/state
  level is fine; no server persistence, mirroring W17's
  per-runner override precedent).
- Tests: picker renders from listing; selection threads
  `account_at_book_id` onto the lay POST.

### §5.4 — HedgeModal safety/parity slice (closes F7-partial)

Three pieces only; the rest of F7 stays future-work (§9).

- **$50 default stake on bonus-winnings cash bets.** When the
  active promo config is bonus-winnings and the modal opens in
  cash mode, the back-stake input pre-fills $50 (editable).
  This is a preserved v2 safety behaviour (W17 brief §5.4) —
  it caps habitual stake size on BW cycles. Named constant.
- **FB face value rounds to $5** on pre-fill (v2 parity).
- **In-modal lay-price refresh ~500 ms while the modal is
  open** (`HEDGE_MODAL_POLL_MS = 500`), pausing the page-level
  1 s poll interaction sensibly (Code's call: either reuse the
  prices query with a faster interval scoped to the modal, or
  a dedicated lighter fetch). The pre-filled lay price field
  updates only until the operator edits it (never overwrite a
  hand-entered price). Polling stops on modal close.
- **Liability guard (operator-required, S147).** Before any
  placement POST fires, compute lay liability
  (`lay_stake × (lay_price − 1)`). Require an explicit
  confirm step (reuse the scream-box pattern) when EITHER:
  liability exceeds `MAX_LIABILITY_SOFT_CAP` (named constant,
  default $500, tunable via localStorage like the price
  window), OR the entered lay price diverges from the live
  best lay by more than 10 ticks (fat-finger catch: 4.4 vs
  44). The confirm names the dollar liability explicitly.
  This guard cannot be disabled in code; only the cap value
  is tunable.
- Tests: BW-cash → $50 pre-fill; FB rounding; hand-edited lay
  price not clobbered by a tick; liability-cap confirm fires
  above cap; 10-tick divergence confirm fires; placement
  blocked until confirmed.

### §5.5 — `_translation.py` wiring for §9.9 (closes F8)

- Add `_translate_list_racing_markets` to
  `clients/betfair_client/v1/_translation.py`, following the
  existing translators' pattern (e.g. market_catalogue).
- Filter shape per W17 report F8: `eventTypeIds` {7 = horse
  racing (thoroughbred + harness), 4339 = greyhounds — verify
  against existing translation constants before hardcoding},
  `marketTypeCodes` ["WIN"], `marketCountries` ["AU"], day
  window converted Adelaide-day → UTC `marketStartTime` range.
- Wire `racing_catalogue.list_racing_markets` to it at the same
  boundary the sibling surfaces use.
- Tests: translator unit tests against canned
  `listMarketCatalogue` JSON (fixture-based, no live calls);
  Adelaide day-boundary conversion cases (incl. ACDT).

### §5.6 — Production composition root (closes F9)

- Build the real dependency wiring under
  `ui/api/dependencies/` (currently an empty package) +
  registration in `ui/api/main.py` / `ui/api/config.py`.
- Wires, config-driven via environment variables (document
  every var): live Betfair client (auth from env/credentials
  file path — never committed), streaming client (placement
  interlock per the existing W3
  `test_streaming_blocks_writes.py` pattern), DB connection to
  the operator's v3 DB path via `BETHUB_DB_URL` (consistent
  with M1's Alembic env resolution), bet storage, accounts
  storage, bet-entry orchestrator, audit sink, operator
  identity.
- A `MOCK_BETFAIR=1` mode that wires the test fakes instead —
  this is what Code uses to integration-test the composition
  root end-to-end (app boots, all seven routes respond) without
  any live call, and what the operator can use for a dry run.
- Startup guard: if live mode is configured but the streaming
  client is not SUBSCRIBED, write routes return the existing
  503 connectivity shape (no silent placement path without the
  interlock).
- Tests: app-factory integration test in mock mode (boot + all
  routes reachable + placement interlock honoured). No live
  test.

## §6 — Sequencing within session

1. §5.5 translation wiring (pure, isolated).
2. §5.6 composition root (depends on nothing above; do early
   while budget is fresh — it is the largest item).
3. §5.1 FB deployment event.
4. §5.2 idempotency.
5. §5.3 AAB selector.
6. §5.4 HedgeModal slice.

Rationale: the two live-blocking items (F8/F9) carry the most
unknowns; front-load them. Items 3–6 are small and separable.
If the session overruns, the coherent stop line is after item 4
(page live-wirable + ledger-safe); items 5–6 then report as
not-done findings. Deviate from this order only with reasoning
recorded in the report.

## §7 — Empirical verification

Capture pre and post states in the report:

- pytest: pre **917 / 0** (standing baseline post-W17/M1); post
  ≥ 917 / 0 with new tests counted.
- vitest: pre **77 / 0**; post ≥ 77 / 0 with new tests counted.
- `tsc -b` clean; `npm run build` clean.
- `lint-imports`: **5 kept / 0 broken** pre and post (DR-030
  boundaries hold — §5.1's workflows call from ui/api and
  §5.6's wiring must not break contracts).
- mypy clean on every touched Python file (no-ignore rule).
- §5.1 behavioural check: log-context inventory excludes a
  consumed FB credit post-deploy (test-level).
- §5.2 behavioural check: double-POST single-row assertion.
- §5.6 behavioural check: mock-mode app boots; placement
  interlock 503 path verified.

## §8 — Output spec

Single file: `dr029/w17_racing_pages/w17_1_report.md`.
Anticipated 200–400 lines. Sections:

1. Headline (done/not-done per item; test counts pre/post).
2. Per-item delivery notes (§5.1–§5.6).
3. **Operator go-live runbook** — exact steps the operator runs
   for first live use: env vars (names + where values come
   from), credential file expectations, start commands (API +
   web), the MOCK_BETFAIR dry-run path, then the live first-use
   sequence (read-only smoke: open page, watch live prices on
   one race; then one small ⚡ lay at minimal size). Plain
   language; the operator is not technical.
4. Findings (surprises, gaps, deferred edges).
5. Self-assessment (judgement calls, refused edges, confidence
   per item).

The report contains no recommendations beyond triage routes and
no scope creep into future-work items.

## §9 — Hard limits

- **No live Betfair API calls. No order placement. No
  credentials created or committed.** Mock/fixture testing
  only. The operator does all live interaction post-delivery.
- No operator-live-DB access; scratch DBs in /tmp only, removed
  at close.
- No v2, VPS, or capture.db access (DR-027/DR-028).
- No schema changes (`sqlite_master` diff empty at close). No
  new Alembic revisions.
- Named anchors only; no drive-by edits to W17 deliverables
  outside the items above.
- Excluded F7 tail (stays future-work): liquidity colour
  indicator, handicap composite identity, any further v2-parity
  HedgeModal behaviour not named in §5.4.
- Excluded findings: F3 sparkline visual (layout-refine cycle),
  F4 promo→book quick-tap buttons (pending operator first-use
  verdict; do NOT build an assignment store).
- No W16 cutover work, no W18, no settings-area UI for the
  price-window key (FW11).
- No project-wide mypy; touched files only.
- No mid-session operator escalation; findings go in the
  report.
- Single bounded session; overrun stops at the §6 coherent
  line.

## §10 — What happens after Code's session

The next Chat session (S148) triages `w17_1_report.md`. On a
clean close: the operator runs the go-live runbook — mock dry
run, then live read-only smoke, then one small real ⚡ lay
(the W17 §10 first-use validation). When the operator confirms
the live path, W16 cutover unblocks. Any not-done or finding
items route to a follow-up at triage; Code does not write the
next brief.

## §11 — Cross-references

- W17 brief §4/§5.4/§5.10/§5.11 (rules and behaviours
  completed here); W17 report findings F2, F5–F9.
- DR-021 (Adelaide timestamps); DR-019 (derive-on-read — FB
  inventory effect in §5.1); DR-025 + S139 amendment
  (commission from Betfair MBR — unchanged, carried); DR-027/
  DR-028 (two-database split — no analytical-line access);
  DR-030 (module boundaries — §5.1 layering, lint-imports
  gate); DR-031 (tech stack — `BETHUB_DB_URL` consistency with
  M1's Alembic adoption); DR-032 (canonical bet record).
- Parking-lot exclusions: calculator rethink, cross-account
  spot-check view, sophisticated price-movement analytics (P2),
  promo-defined columns (FW1).

— End of brief.
