# W8 — burst-review queue UI brief

**Status:** locked (Session 108).
**Stream:** §2.6 settlement-race operator-facing surface.
**Author:** operator-Claude, Session 108.
**Code session shape:** single bounded session, end-to-end.
**Output:** `dr029/w4_bet_entry/w8_burst_review_queue_report.md`.

---

## §1 — What this brief is and is not

W8 commissions Code to build the burst-review queue: the operator-facing
surface where bets in `provisional` settlement state surface for action,
on top of the W7-shipped web layer skeleton. The brief covers three
interlocking pieces of work:

1. **Read-side API endpoints** — FastAPI routes that expose the existing
   `list_provisional_settlement_bets()` storage helper as a JSON surface
   the React frontend can consume.
2. **Write-side API endpoints + workflow** — the manual-transition path
   that lets the operator move a bet from `provisional` to a terminal
   state (`settled_won`, `settled_lost`, `voided`). This is the v1
   implementation of the manual-operator-action transition path that
   W6.5 explicitly deferred to "build-proper" (per `settlement.py` line
   310 comment and W6.5 brief §5.5 Change C).
3. **React UI** — the queue page (lists provisional bets, auto-refreshes,
   handles auto-resolution gracefully) and the per-bet modal (shows bet
   data, surfaces transition action buttons, captures
   operator-supplied reason for audit trail).

**Single bounded Code session.** Surprises become findings, not blockers.
Remediation routes to operator-Claude triage in the follow-up session,
not Code's report.

**Out of scope, deferred:**

- **Settings-area cadence control for queue refresh.** Hard-code a
  default cadence in W8 (recommend 3 seconds, see §6); a future "queue
  settings" brief will scope the operator-facing tuning panel once
  operational experience surfaces what knobs matter. Carry-forward
  open item.
- **Greyhound operational constraint** (no in-play window; market goes
  OPEN → SUSPENDED at jump with no live odds in between). Parked as a
  needs-verification item against the settlement-worker layer (W6.5).
  W6.5's read pattern `_resolve_settlement_for_bet()` already handles
  any market that reaches `CLOSED`+settled regardless of how it got
  there, so the constraint is likely already covered — but verification
  belongs against a real greyhound race in operational use, not in the
  W8 queue brief. Carry-forward open item.

**Out of scope, structurally:**

- §2.6 §3.4 condition 2 (post-settlement market void re-transition from
  a terminal state back to `provisional`). W6.5 deferred this to
  build-proper; W8 does not pick it up. Bets in terminal states are not
  re-read by the worker, so this transition cannot fire under v1
  operations. Carry-forward.
- Operator-driven manual escalation from a *terminal* state to
  `provisional` (§2.6 §3.2 manual-escalation path). v1's manual write
  path covers `provisional` → terminal only. Escalation in the other
  direction is build-proper. Carry-forward.
- Settlement-state transitions outside the manual write path. The
  settlement worker's auto-resolution logic stays untouched.
- Schema changes. The `bets` table already carries `settlement_state`
  and the supporting count fields (W6.5 ship state). W8 reads and
  updates `settlement_state`; it does not add columns.
- Authentication / authorisation on the new endpoints. v3 day-one is
  single-operator local; auth is build-proper.

---

## §2 — Why this work exists

Three drivers converge:

1. **§2.6 §3.5 surfacing contract.** The settlement-state spec specifies
   what data the burst-review queue receives when a bet enters
   `provisional`. That data flows through W6.5's
   `ProvisionalSettlementSurfacingPayload` model and the storage
   helper `list_provisional_settlement_bets()`. The queue UI is where
   that data lands in front of the operator.
2. **§2.6 §3.2 manual operator path.** The state machine specifies that
   a `provisional` bet can transition to a terminal state via operator
   decision. W6.5 left this write path unbuilt (`settlement.py` line
   310, W6.5 brief §5.5 Change C). Without W8, the queue would surface
   provisional bets the operator could see but not act on — operationally
   useless.
3. **W7 follow-through.** W7 shipped the web layer skeleton with the
   `apiGet` seam and the `Health` smoke-test page. W7 §7.4 carry
   identified `VITE_API_BASE_URL` env-var conventions as the right
   substrate for production-deploy address management; W8 is the first
   real consumer of API endpoints, so the convention lands here.

---

## §3 — Pre-reads

**Required (read in order):**

1. `dr029/2_6_settlement_race/2_6_settlement_race.md` §3.1, §3.2, §3.4,
   §3.5 — settlement state machine, transitions, burst-review trigger
   conditions, surfacing contract.
2. `dr029/2_6_settlement_race/2_6_settlement_race.md` §4.4 — abandoned
   race (race-wide voiding via related-bets pointer).
3. `dr029/w4_bet_entry/w6_5_settlement_worker_brief.md` and
   `_report.md` — settlement worker spec and ship-state. The
   surfacing payload, storage helper, and `_build_surfacing_payload`
   builder all live in this stream.
4. `dr029/w4_bet_entry/w7_web_layer_skeleton_brief.md` and
   `_report.md` — substrate the queue UI attaches to. The `apiGet`
   client, the `Health` route as styling/test precedent, the
   `create_app()` factory, the router-registration pattern.
5. Working tree at `bethub-v3/ui/api/` and `bethub-v3/ui/web/` — the
   shipped skeleton.
6. Working tree at `bethub-v3/workflows/bet_entry/v1/settlement.py`,
   `storage.py`, `models.py` — the read helpers and write surfaces W8
   builds against.

**Reference-only (read on demand):**

- `decisions.md` §DR-030 (repo layout) and §DR-031 (tech stack with
  W7 amendment locking version baseline).
- `decisions.md` §DR-032 (canonical reference layer for bet records).
- `architecture.md` §D12 + Session 42 architectural-extension flag —
  Betfair as canonical source for bet record identifiers.
- `dr029/w4_bet_entry/w6_5_settlement_worker_report.md` — the W6.5
  ship report, in case implementation details of the read path matter
  for the modal's display logic.

---

## §4 — System access

- **Filesystem:** read-write on `bethub-v3/ui/api/`,
  `bethub-v3/ui/web/`, `bethub-v3/workflows/bet_entry/v1/settlement.py`,
  `bethub-v3/workflows/bet_entry/v1/storage.py`. Read-only on all
  other v3 paths.
- **Database:** the v3 operational SQLite store at
  `bethub-v3/data/bethub.db` (or wherever the test fixture builds it
  to). W8 commissions read and write paths against the `bets` table's
  `settlement_state` column and the audit-trail surface that goes with
  it; existing helpers handle the SQL.
- **No VPS access.** This brief is local Mac filesystem only.
- **No live Betfair API calls.** The worker's settlement reads are
  not triggered by W8's UI. The queue reads from the stored bet
  records; the worker keeps running on its existing cadence.
- **Adelaide local timestamps per DR-021** for every time-of-day
  reference in the report and in the UI display surfaces.

---

## §5 — Substantive scope sections

Nine named anchors. Each anchor is a discrete deliverable; together
they constitute the W8 ship.

### §5.1 — `apiPost` and `apiPatch` client wrappers

**File:** `bethub-v3/ui/web/src/api/client.ts`.

Add two wrappers alongside the existing `apiGet`. Mirror its shape:
typed return, `ApiError` on non-2xx, `${API_BASE_URL}${path}` URL
composition. POST and PATCH bodies: JSON-encoded. Headers: `Accept:
application/json` + `Content-Type: application/json`.

The W7 client.ts header comment explicitly anticipates this addition
("POST/PATCH/DELETE wrappers and richer error-envelope shaping arrive
in W8+ when real endpoints need them"). Land POST and PATCH; DELETE
not needed at v1.

### §5.2 — `VITE_API_BASE_URL` documentation pair

**Files:**
- `bethub-v3/ui/web/.env.development` (new)
- `bethub-v3/ui/web/.env.production` (new)
- `bethub-v3/ui/web/README.md` (edit)

Create the two env files with sensible defaults (`VITE_API_BASE_URL=
http://localhost:8000` for development; production left commented as
`# VITE_API_BASE_URL=https://api.example.com` with a brief comment
naming the production-deploy story). Update README to document the
convention.

W7 §7.4 carry — folded into W8 as agreed at Session 107 close.

### §5.3 — Provisional-bets read endpoint

**File:** `bethub-v3/ui/api/routers/provisional.py` (new), wired into
`main.py` via the `create_app()` factory's router-registration block.

Endpoint: `GET /api/v1/bets/provisional`.

Returns: a JSON array of objects, one per bet in `provisional`
settlement state. Shape derived from `ProvisionalSettlementSurfacingPayload`
flattened to a UI-tractable structure. Suggested fields per item:

- `bet_id`, `placement_time`, `entered_provisional_at`.
- `betfair_market_id`, `betfair_selection_id`, `betfair_event_name`,
  `betfair_market_name` (event/market identity for operator
  recognition).
- `book_or_exchange`, `account_at_book_id`, `requested_stake`,
  `matched_price` (bet-shape recognition).
- `trigger_source` (one of `provisional_unexpected_state`,
  `provisional_post_settlement_void`, `manual_operator_escalation`).
- `operator_escalation_reason` (nullable; populated only on
  manual-escalation trigger source — out-of-scope at v1 per §1, so
  always null for v1).
- `last_read_market_state` — flattened summary of what the worker
  last saw on the Betfair market: market state, settled-time,
  per-runner statuses for the runners involved. Serialise to a
  nested object; Code's call on the exact shape, but it must let the
  modal show the operator what Betfair currently reports.
- `related_bet_ids` — array of bet IDs, possibly empty.

Pagination: not at v1. The storage helper caps at 100 items per call.
If the queue grows past that, that's an operational signal and a
finding for a follow-up brief.

Backend route handler: instantiate the storage's
`list_provisional_settlement_bets()`, map each `ProvisionalSettlementSurfacingPayload`
into the response shape, return.

### §5.4 — Manual-transition write endpoint

**File:** `bethub-v3/ui/api/routers/provisional.py` (same router
file as §5.3).

Endpoint: `POST /api/v1/bets/provisional/{bet_id}/resolve`.

Request body shape:

```json
{
  "new_state": "settled_won" | "settled_lost" | "voided",
  "operator_reason": "string, optional, free-text for audit trail"
}
```

Response: the updated bet record's settlement-state summary, or an
error envelope on failure.

Failure modes the endpoint handles cleanly:

- Bet not found → 404.
- Bet not in `provisional` state → 409 with explanatory message.
- `new_state` not one of the three permitted terminal states → 422.
- Storage write failure → 500 with surface-level error.

The endpoint calls into a new workflow function (§5.5) that does the
state transition and audit-trail write atomically. The endpoint
itself is a thin shell over the workflow.

### §5.5 — Manual-transition workflow function

**File:** `bethub-v3/workflows/bet_entry/v1/settlement.py`.

Add a function to the existing settlement module:

```python
def apply_manual_operator_resolution(
    *,
    bet_id: str,
    new_state: SettlementState,  # SETTLED_WON | SETTLED_LOST | VOIDED
    operator_reason: str | None,
    storage: BetEntryStorage,
    now: datetime,
) -> BetRecord:
    """§2.6 §3.2 manual operator path. Transitions a bet from
    PROVISIONAL to a terminal state on operator decision via the
    burst-review queue. Returns the updated bet record.

    Audit-trail entry records `operator_reason` and the
    settlement-read state at the time of operator action (so post-hoc
    review can reconstruct what the operator saw and what they
    decided per §2.6 §3.5).
    """
```

Called by the route handler in §5.4. Validates the state transition
against the state machine (only `provisional` → one of three
terminal states; reject all other source states). Writes the
audit-trail entry to whatever audit surface the existing settlement
worker uses (the same place auto-resolutions are recorded — Code's
call after reading the existing audit code path).

If no audit-trail surface yet exists for settlement transitions in
the W6.5 ship, surface as a finding in §6 of the report; W8 v1 lands
the transition write itself, and audit-trail extension can be a
small follow-up brief. **Code must explicitly confirm which path it
took in the report's §6 (deviations) section** — either "audit
surface found at `<path>:<lineref>`, manual transitions written to
it" or "no audit surface found in W6.5 ship, transitions land
without audit-trail entry, follow-up brief required." The operator
needs that named call clearly in the report regardless of which
path Code takes.

Pytest tests: at least three positive paths (one per terminal
state) plus the four failure modes from §5.4.

### §5.6 — Queue page

**File:** `bethub-v3/ui/web/src/routes/Provisional.tsx` (new), with
matching `.module.css` and `.test.tsx`.

Wire into the React Router config alongside the existing `Health`
route. URL path: `/provisional`. A minimal top-level navigation
surface lands as part of W8 — see §5.9.

UI requirements:

- Auto-refresh on a fixed cadence. Default: **3 seconds**. Hard-coded
  constant at the top of the file with a clear comment naming the
  future settings-area control. Use TanStack Query's `refetchInterval`
  per the W7 substrate.
- Tabular display, one row per provisional bet. Columns surface the
  fields most useful for operator recognition: event name, market
  name, runner, stake, price, trigger source, time-in-provisional
  (computed from `entered_provisional_at` to now). Runner display
  format is **`selection_id. runner_name`** when the runner name is
  available (e.g. `12345. Cornishman`), or just the `selection_id`
  when it isn't. Runner-name resolution is nice-to-have not
  essential for v1 — Code's call whether the v1 API endpoint
  surfaces a name field given the existing data shape; if it
  requires a fresh Betfair API call or an extra DB join that adds
  meaningful complexity, ship without name and surface as a finding
  for a follow-up brief.
- Click on a row opens the modal (§5.7). Row hover state and
  click-affordance styling per Code's judgement; W7's `Health` page
  styling is a reasonable visual baseline.
- Empty state — "No provisional bets" — when the array is empty.
  This is the common operational state and shouldn't read as an
  error.
- Loading state — first fetch; subsequent refreshes show stale data
  while fetching, no full-page reset.
- Error state — API failure shows a banner with the error and a
  manual retry button. Auto-refresh continues; the banner clears on
  next successful fetch.
- Auto-resolution handling. When a row disappears between refreshes
  (auto-resolved by the settlement worker), no operator action
  needed; the row vanishes from the list. The §3.5 spec is explicit
  on this. If the modal is open against a bet that disappears, the
  modal should detect the missing bet on its next data refresh and
  close itself with a small toast / banner ("This bet was
  auto-resolved").
- Vitest tests: empty-state, populated-state, loading-state,
  error-state, refresh-cycle behaviour (using mock server data).

### §5.7 — Per-bet modal

**File:** `bethub-v3/ui/web/src/components/ProvisionalBetModal.tsx`
(new), with matching `.module.css` and `.test.tsx`. Imported by the
Provisional page (§5.6).

UI requirements:

- Header: bet identity (event, market, runner). Time placed and time
  entered provisional, in Adelaide local time per DR-021.
- Body section 1 — bet record summary: stake, price, book / exchange,
  account-at-book identity. Same fields as the row on the queue page,
  fuller layout.
- Body section 2 — trigger source: which §3.4 condition fired (or
  manual escalation reason if the v1 surface ever shows one — won't
  at v1 but the layout should accommodate). Plain-language framing,
  not the raw enum.
- Body section 3 — last read market state: what Betfair last
  reported. Market state, settled-time, runner statuses. Plain
  table, monospace where useful.
- Body section 4 — related bets: if `related_bet_ids` is non-empty,
  list them with a one-line indication that batch action may be
  appropriate. v1 does not implement batch action; this is a
  visibility surface only.
- Action area — three buttons: "Mark settled (won)", "Mark settled
  (lost)", "Mark voided". Each button is destructive in shape (the
  bet's settlement state is being terminally locked) — a confirmation
  step is required before the API call fires. The confirmation step
  surfaces an optional free-text "reason" field (operator-supplied
  context, recorded to the audit trail).
- On confirm: the modal calls the §5.4 endpoint, shows a loading
  state, and on success closes the modal and shows a brief toast on
  the queue page ("Bet marked settled (won)"). On failure, surface
  the error envelope inline in the modal; the modal stays open so
  the operator can retry.
- Cancel / dismiss: the modal closes without acting on the bet. The
  bet remains in `provisional`; the auto-resolution path keeps
  working.
- Modal accessibility — focus trap, escape-key dismissal, click-
  outside dismissal. Standard modal hygiene.
- Vitest tests: modal opens with bet data, each of three action
  buttons fires the right request, confirmation step works, error
  state surfaces in modal, dismiss closes without action.

### §5.8 — Minimal top-level navigation surface

**File:** `bethub-v3/ui/web/src/App.tsx` (edit), with matching
`.module.css` if styling is needed.

The W7 ship currently has a single route (`/health`) reachable only
by direct URL. W8 introduces the second meaningful page; visibility
matters operationally — if the operator can't see the queue without
typing `/provisional`, it won't get used as much. Land a minimal
top-level navigation surface to make the queue discoverable.

**Scope of "minimal":**

- A simple top-of-page nav bar or sidebar (Code's call on layout
  shape) listing the available routes.
- Two entries at v1: **Burst review** (linking to `/provisional`)
  and **Health** (linking to `/health`). The Burst review entry is
  primary; the Health entry can be smaller / less prominent / under
  a "Diagnostics" group — Code's call.
- No active-route highlighting required (would be nice; not gating).
- No mobile responsiveness required (single-operator desktop use).
- No logo, branding, or visual flourish required. Functional bar
  only.
- No collapsible / hideable behaviour. Always visible.

The nav surface lives in `App.tsx` (or a dedicated `Navigation.tsx`
component imported by `App.tsx` — Code's call) and renders on every
page consistently. Style with the same minimal-CSS approach W7 took
for the Health page.

Vitest tests: at least one rendering test confirming both nav
entries are present and link to the correct paths.

If Code judges that a `Navigation.tsx` component is the cleaner
shape, that's allowed and folds into this anchor. If a `nav.css` /
`Navigation.module.css` falls out alongside, also allowed. Whatever
shape Code lands on, document the file inventory in the report.

### §5.9 — Smoke-test verification

After all of the above lands, Code runs the existing pytest +
vitest suite to confirm green, then runs the smoke-test stack
(FastAPI + Vite per W7 §5.9 / §5.7 conventions) and exercises:

- `GET /api/v1/bets/provisional` from `curl` returns a 200 with an
  empty array on a clean DB.
- Inserting a synthetic provisional bet (via a fixture or short
  Python script) appears in the response.
- Loading the queue page in the browser (or via vitest's jsdom)
  shows the row and the empty state correctly.
- Opening the modal, clicking an action button, confirming →
  `POST /api/v1/bets/provisional/{bet_id}/resolve` fires, returns
  success, the bet's `settlement_state` in the DB transitions to
  the requested terminal state, the bet disappears from the next
  queue refresh.

A manual browser walkthrough is **not** required (per Session 107
§7.7 precedent — trust curl + test-suite verification). If Code
chooses to spot-check in a browser as part of normal development,
that's fine; report's "ship verification" section names what was
exercised.

---

## §6 — Sequencing within session

Suggested order, with dependency reasoning. Code may deviate where a
different order is operationally cleaner; flag any deviation in the
report.

1. **§5.5 first** — workflow function `apply_manual_operator_resolution()`
   in `settlement.py`. Pure backend, fully unit-testable, pins the
   contract the API endpoints serve.
2. **§5.4 next** — the POST endpoint, calling §5.5. Backend tests
   against an in-memory storage fixture confirm the wire-up.
3. **§5.3 next** — the GET endpoint. Independent of §5.4 / §5.5 but
   sharing the router file, so co-locate.
4. **§5.1 next** — `apiPost` / `apiPatch` client wrappers. Frontend
   substrate for the UI work.
5. **§5.2 in parallel with §5.1** — env-var docs are a 10-minute
   addition that doesn't gate anything.
6. **§5.7 next** — per-bet modal. The modal is the more complex of
   the two UI pieces and benefits from being driven by mock data
   first; the queue page can then drop the modal in cleanly.
7. **§5.6 next** — queue page. Brings the modal together with the
   read endpoint, exercises auto-refresh.
8. **§5.8 next** — minimal top-level navigation surface. Wires both
   the queue and the existing health route into a discoverable
   layout. Goes after §5.6 because the queue route needs to exist
   before the nav can link to it.
9. **§5.9 last** — smoke-test verification. Whole-stack end-to-end.

If §5.5 surfaces an audit-trail design question (no existing audit
surface in W6.5's ship), pause, capture the finding, ship the
transition write *without* the audit entry, and flag the audit gap
as a §6 deviation. Do not block W8 on building an audit surface.

---

## §7 — Empirical verification

**Pre-baseline (before any edits):**

- Capture current pytest count for `bethub-v3/workflows/bet_entry/v1/`
  (`pytest workflows/bet_entry/v1/`).
- Capture current pytest count for `bethub-v3/ui/api/`.
- Capture current vitest count for `bethub-v3/ui/web/`.
- Capture line count of `settlement.py`, `client.ts`,
  `routers/health.py` (for ship-delta numbers in the report).
- Confirm `lint-imports` shows 5 contracts kept, 0 broken (W7
  ship-state).

**Post-baseline (after all edits):**

- Re-run pytest across the three areas; report the delta.
- Re-run vitest; report the delta.
- Re-run `ruff`, `eslint`, `mypy --strict`, `lint-imports` — confirm
  green.
- Capture line count delta on each edited file.
- Smoke-test stack curl probes per §5.8.

The report's "Empirical verification" section reproduces the before
/ after numbers as a small table. Same shape as W7 report §3.

---

## §8 — Output spec

**Single output file:** `dr029/w4_bet_entry/w8_burst_review_queue_report.md`.

**Section structure (suggested, Code may adapt within reason):**

1. Executive summary — one paragraph: what shipped, test counts, lint
   state.
2. Pre/post empirical baseline tables.
3. Per-anchor ship summary — one §-section per §5.1 through §5.9,
   with line counts, test counts, brief notes.
4. Where the new files / functions live (paths + line ranges).
5. Wire-up evidence — the smoke-test exercise output.
6. Deviations — Code's calls that diverge from the brief. Includes
   judgement-driven choices made under the brief's "Code's call"
   carve-outs (response-shape decisions in §5.3, audit-trail
   path-taken confirmation in §5.5, runner-name resolution
   in §5.6, nav layout shape in §5.8, etc.).
7. Open questions — anything Code wants the next operator-Claude
   session to triage. Default state: empty if the brief is well-
   anchored.
8. Findings — anything Code noticed that's worth surfacing but isn't
   a deviation or a question. Substrate observations,
   technical-debt notes, future-brief hooks.
9. Ship verification — what was exercised in §5.9.
10. Self-assessment — Code's read on whether this brief landed
    cleanly or surfaced unexpected scope creep.

**Length anticipation:** 800-1200 lines. W7's report landed at
1275; W8 is comparable in surface but with less novel substrate
(more is "wire to existing helpers" than "scaffold new
infrastructure"). Below 800 may indicate under-coverage; above 1300
may indicate scope creep. Either way, flagged in §10
self-assessment.

**Output does NOT contain:**

- Recommendations beyond what the brief explicitly allows in §6
  (deviations) and §7 (open questions). No overall verdict on
  architectural direction.
- Speculation about future briefs. Open questions name what needs
  triaging; the next brief is the next session's call.
- Any edits or notes touching files outside the named anchors in §5.
- Modifications to W7-shipped code outside the named edits to
  `client.ts` (§5.1) and `README.md` (§5.2).

---

## §9 — Hard limits

Non-negotiable. Code is forbidden from:

- **Editing files outside the named anchors in §5.** No "while we're
  here" tidies in adjacent code. Surface as a finding if drift is
  noticed; do not act on it.
- **Schema changes.** The `bets` table's existing columns are the
  surface; W8 reads and updates `settlement_state`, no DDL.
- **Changing W6.5's auto-resolution logic in `settlement.py`.** The
  existing `_resolve_settlement_for_bet` and `apply_settlement_pass`
  functions are read-only territory. W8 only adds
  `apply_manual_operator_resolution`.
- **Building authentication / authorisation.** v3 day-one is local
  single-operator.
- **Building batch-action UI.** Related-bets pointer is visibility
  only at v1.
- **Building the settings panel for queue cadence control.** Hard-
  coded constant in W8; settings is a follow-up brief.
- **Touching the §2.6 §3.4 condition 2 path** (post-settlement market
  void re-transition from terminal). W6.5 deferred this; W8 inherits
  the deferral.
- **Touching the §2.6 §3.2 manual-escalation path from terminal to
  provisional.** Out of scope per §1.
- **Touching the named pieces of debt** — no test coverage strategy,
  no migration framework, monolithic orchestrator file. Carry-forward
  governance items, not W8 work.
- **Mid-session escalation.** Code runs end-to-end. Surprises become
  findings; if W8 can't ship, that's the ship-verification finding,
  not a request for direction.

---

## §10 — What happens after Code's session

The next operator-Claude session reads `w8_burst_review_queue_report.md`,
triages findings via the inventory-first cadence (sweep candidate
`(l)`, six concrete uses prior), and routes:

- **Deviations (§6)** — accept, reject, or amend each. Most
  expected to be no-call (judgement-driven choices Code is allowed
  per the brief).
- **Open questions (§7)** — operator-call items go through the
  plain-language reframe (sweep candidate `(s)`, five concrete uses
  prior, including Session 107). Other items defer or close.
- **Findings (§8)** — most no-call. Substrate-observation findings
  feed sweep candidate `(h)` (brief-length-estimate calibration);
  technical-debt findings feed governance carry; future-brief hooks
  feed the next-stream queue.

**Most plausible follow-on briefs** (not commissioned by W8 — named
only to set context for the next session):

- Audit-trail surface for settlement transitions, if W8's §5.5
  surfaced an audit gap.
- Runner-name resolution for the queue display, if W8's §5.6 ships
  without it.
- Greyhound operational verification, if the carry-forward open item
  surfaces movement.
- Settings-area cadence control (the deferred panel from §1).
- §2.6 §3.4 condition 2 (post-settlement re-void) at build-proper.

W8 does not commission any of these. They are next-session triage
calls.

---

## §11 — Cross-references

- **Scope:** §2.6 settlement-race operator-facing surface
  (`dr029/2_6_settlement_race/2_6_settlement_race.md` §3.4 + §3.5
  primary; §3.1, §3.2, §4.4 supporting).
- **DRs invoked:**
  - DR-030 (v3 repo layout — load-bearing for `ui/api/routers/`
    and `ui/web/src/routes/` placement).
  - DR-031 (v3 tech stack with W7 amendment — load-bearing for
    FastAPI / React / Vite versions; no version bumps in W8).
  - DR-032 (canonical reference layer for bet records — context
    for the read endpoint's response shape; bet-record / bet-leg
    field semantics).
  - DR-021 (timestamp anchoring, Adelaide local time — applies to
    every time-of-day display in the queue and modal).
  - DR-019 (derived state on read — context for the
    time-in-provisional computation).
  - DR-022 (book / account / account-at-book vocabulary — the
    queue surfaces `book_or_exchange` and `account_at_book_id`
    fields; vocabulary discipline applies).
  - DR-027 / DR-028 (cross-database boundary — context only at W8;
    queue does not touch capture.db).
- **Prior reports / briefs this builds on:**
  - W6.5 brief and report — settlement worker substrate the queue
    consumes.
  - W7 brief and report — web-layer skeleton the queue attaches to.
- **Parking-lot items excluded:**
  - Settings-area cadence control (W8 deferred).
  - Greyhound operational constraint verification (W6.5-layer
    needs-verification).
  - Audit-trail surface (potentially surfaced by W8 §5.5; not
    commissioned here).
  - Runner-name resolution (nice-to-have; if not landed at v1 per
    §5.6, lands in a follow-up brief).
  - §2.6 §3.4 condition 2 post-settlement re-void path (W6.5
    deferred to build-proper).
  - Manual escalation from terminal → provisional (build-proper).
