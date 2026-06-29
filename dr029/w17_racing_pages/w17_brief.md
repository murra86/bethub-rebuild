# W17 Brief — Racing market pages (v3 first functional cut)

**Drafted:** Session 146, opened 2026-06-10 16:06 ACST.
**Status:** LOCKED — operator-confirmed Session 146. Ready for
out-of-session Code execution.
**Executes against:** `dr029/w17_racing_pages/scope_settlement.md`
(the operator-locked scope, S145). This brief expands that scope;
it does not re-open it. Where this brief and the scope file appear
to conflict, the scope file wins and Code surfaces the conflict as
a finding.

---

## §1 — What this brief is and is not

This is a **build brief**. Code builds the v3 racing market pages:
the race-list sidebar, the live odds/EV table, the promo machinery,
the bet-logging panel (with v3 free-bet and balance surfacing), the
⚡ quick-lay tool, and the simple price-movement indicator — plus
the API routes and one small Betfair-client read surface they need.

- **Single bounded Code session.** This is the largest workstream
  of the build. If the work does not fit one session, Code stops at
  a coherent checkpoint, records exactly what is built and what is
  not in the report, and surfaces the remainder as a finding.
  Partial-but-coherent beats complete-but-lost-coherence. A second
  Code session against this same brief resumes from the report.
- **Surprises become findings, not blockers.** Anything in the v3
  codebase or contracts that does not match this brief's assumption
  is recorded in the report and worked around minimally; Code does
  not redesign mid-flight.
- **Remediation routes to operator-Claude triage**, not to Code's
  own judgement. The report carries findings; the next Chat session
  routes them.
- **This is a first functional cut, not a final design.** Layout is
  deliberately refine-in-use (scope §1). Code optimises for clean
  data/presentation separation so layout changes post-W17 are cheap
  small briefs, not rebuilds.

## §2 — Why this work exists

The racing pages are the operator's daily working surface — the
screen open during every betting burst. v2's racing page carries
the whole daily operation today. v3 cutover (W16) is blocked on
W17: the operator cannot leave v2 until v3 has usable racing pages
wired to v3's bet-entry, balances, and promo machinery. W17 is the
last large pre-cutover workstream.

Scope was settled with the operator at Session 145 and locked at
`dr029/w17_racing_pages/scope_settlement.md`. The five locked
decisions: first-functional-cut posture (§1 there), density as a
named design principle (§2), calculator cut (§3), simple
price-movement indicator in W17 (§4), lean v3-data surfacing in the
log panel (§5). Section 6 of the scope file lists what ports from
v2 as baseline.

## §3 — Pre-reads

Required, in order:

1. `dr029/w17_racing_pages/scope_settlement.md` — the locked scope.
2. This brief, end to end, before any code.
3. `decisions.md` — DR-030 (module boundaries, S124 amendment),
   DR-019 (derived state on read), DR-021 (Adelaide timestamps),
   DR-031 (tech stack), DR-025 incl. S139 commission amendment.
4. `contracts/betfair_client_contract.md` §8 (envelope), §9.1
   (live pricing), §9.4 (scheduled time), §9.7 (market catalogue),
   §11.1 (placement), §14.4 (backward-compatible additions).
5. v3 source read surfaces named per-section in §5 below.

Reference-only (consult when the section touches them, do not read
end-to-end): v2 frontend sources under
`/Users/tim/Desktop/Projects/bethub-v2/frontend/src/` (READ-ONLY —
behavioural reference, not a copy source of record);
`contracts/vps_client_contract.md`.

## §4 — System access

- **Mac filesystem, v3 repo read-write** at
  `/Users/tim/Desktop/Projects/bethub-v3/`. All edits land here.
- **v2 repo READ-ONLY** at
  `/Users/tim/Desktop/Projects/bethub-v2/`. No modifications under
  any circumstance (standing rule — v2 is the live daily system).
- **v3 operational database** — local SQLite per the existing
  store layer. Tests use the in-memory / fixture patterns already
  established in `tests/`.
- **NO live Betfair API calls and NO live order placement during
  this build.** All client-surface work is tested against mocked
  REST/Streaming clients per the existing test patterns in
  `tests/clients/betfair_client/`. The ⚡ quick-lay placement path
  is wired end-to-end but exercised only against mocks. The
  operator exercises the live path on first real use post-W17.
  This is a bet-safety hard rule, restated in §9.
- **No capture.db / VPS access.** The racing pages are
  operational-line only (DR-027/028 — two-database architecture;
  integration by reference only). Nothing in W17 reads the
  analytical store.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for every
  time-of-day reference in code comments, the report, and any
  logged output.

## §5 — Substantive scope

Eleven numbered scope sections. Each names its read surfaces and
its deliverable. v2 file references are behavioural baselines —
Code re-implements against v3's architecture, it does not
copy-paste v2 code.

### §5.1 Design posture and density (governs all UI sections)

Per scope §1–§2, restated as build directives:

- **Component structure keeps layout cheap to change.** Data
  acquisition (polling, API calls, derived state) lives in hooks /
  data modules; presentation components consume typed props. No
  business logic inside JSX layout. A post-W17 layout brief should
  be able to reshape a page by touching presentation components
  only.
- **Density is a design principle, strongest on the race screen.**
  Compact rows, small type where v2 set the precedent (v2 uses
  10–12px table type), every column earning its width. No
  decorative padding. The odds table must comfortably show a
  12-runner field plus the log panel on a standard laptop screen
  without horizontal scrolling.
- **Future-work note (NOT W17 scope):** columns may eventually be
  defined by which promo is active. Code records this in the
  report's future-work section and keeps column definitions in a
  single declarative structure so that change stays cheap.

### §5.2 Betfair client — racing catalogue listing (new read surface)

**Gap:** v1.0 of `betfair_client` exposes single-market reads only
(§9.1 prices, §9.7 catalogue). The race-list sidebar needs "today's
AU racing WIN markets" as a listing read. v2 gets this via its own
catalogue call in `src/api/racing.py`.

**Deliverable:** one new read surface in
`clients/betfair_client/v1/` (new module, e.g.
`racing_catalogue.py`), exposed per the existing envelope
discipline:

```python
def list_racing_markets(
    day: date,                      # Adelaide-local calendar day
    race_codes: Sequence[RaceCode], # T / H / G filter
    rest_client: BetfairRestClient,
) -> ReadEnvelope[list[RacingMarketSummary]]: ...
```

`RacingMarketSummary` carries at minimum: `market_id`, venue,
country, race number, race code (T/H/G), scheduled start (Adelaide
local), runner count, market status, total matched volume, and the
Betfair event id. Field names follow the existing catalogue model
conventions. WIN markets only — place-market listing is out of
scope (Strategy 4 territory, analytical arc).

**Contract addition:** a new §9.9 sub-section in
`contracts/betfair_client_contract.md` documenting the surface,
added per §14.4 (backward-compatible addition, no version bump).
Code writes the contract section in the same style as §9.1/§9.7
(endpoint path, signature, parameter spec, return shape, failure
modes, example call).

**Read surfaces for this section:**
`clients/betfair_client/v1/market_catalogue.py`,
`live_pricing.py`, `_connection.py`, `envelope.py`, plus the
matching tests under `tests/clients/betfair_client/`.

**MBR / commission:** the racing pages need each market's Betfair
market base rate (commission) for lay maths and EV (DR-025 S139
amendment — commission is sourced per-market from Betfair, never a
hardcoded table). If the existing catalogue/prices models do not
already expose MBR, extend `RacingMarketSummary` (and/or the §9.7
catalogue model per §14.4) to carry it. The UI must receive MBR
from the API, never hardcode it.

### §5.3 ui/api — racing routers

**Deliverable:** a new racing router package under
`ui/api/routers/` (e.g. `racing.py`, registered in
`ui/api/routers/__init__.py` and `main.py` like the existing
health/provisional routers). DR-030 module boundaries apply: the
router is a thin HTTP adapter — it calls client surfaces and
workflow functions, holds no business logic of its own, and maps
envelopes to HTTP responses.

Routes (paths indicative; Code finalises naming consistently with
the existing `/api/v1/...` convention):

1. `GET /api/v1/racing/races?day=YYYY-MM-DD&codes=T,H,G` — today's
   race list via §5.2's `list_racing_markets`. Defaults: today
   (Adelaide), all three codes.
2. `GET /api/v1/racing/markets/{market_id}/prices` — full market
   book via `market_prices` (§9.1). This is the ~1s polling target
   for the open race screen.
3. `GET /api/v1/racing/markets/{market_id}/catalogue` — runner
   names/numbers + market metadata via `get_market_catalogue`
   (§9.7), fetched once per race open (slow-changing).
4. `GET /api/v1/racing/log-context?account_at_book_id={uuid}` —
   the log-panel data surface (§5.7): free-bet inventory via
   `workflows.promos.v1.promo_derivations.compute_free_bet_inventory`
   and balance via
   `workflows.balances.v1.balance_derivation.compute_account_at_book_balance`,
   returned together in one response (one fetch when the operator
   picks an account at log time).
5. Account/book listing reads as needed by the log panel's
   selectors (account holders, books, account-at-books) — via the
   existing store repositories; add minimal read routes only if no
   equivalent already exists.

**Envelope mapping:** `fresh` → 200 with data + `as_of`; `stale` →
200 with data + staleness metadata (the UI shows data-age, it does
not hide stale prices); `unavailable` → 503/404 mapped from the
reason enum, body carrying the reason string. Consistent across
all racing routes; Code documents the mapping in the report.

**Read surfaces:** `ui/api/main.py`, `ui/api/routers/health.py`,
`provisional.py`, `ui/api/dependencies/`, `ui/api/config.py`, the
W12/W13 derivation modules named above, and
`store/repositories/accounts.py`.

### §5.4 ui/api — bet logging and lay placement routes

The page writes bets through v3's existing bet-entry machinery —
W17 adds HTTP routes in front of it, not new bet logic.

1. `POST /api/v1/racing/bets` — log a soft-book back bet from the
   log panel. Calls into `workflows/bet_entry/v1/` (orchestrator /
   record builder) with the racing context: market id, selection
   id, venue, race number, scheduled start, odds, stake, bet type
   (cash / free-bet), promo fields, account-at-book, plus the
   Betfair back/lay snapshot and EV snapshot at log time (v2
   parity — these feed later analytics). Free-bet deployments
   route through the promo event machinery (W13) so inventory
   stays truthful: deploying a free bet writes the
   `free_bet_deployed` supersession event against the selected
   credit.
2. `POST /api/v1/racing/lay` — the ⚡ quick-lay placement. Calls
   the `betfair_client` §11.1 placement surface (lay side, stake
   model). **Hard bet-safety rule carried from v2 (HedgeModal
   comment, preserved verbatim in intent): NEVER place a lay via a
   profit-target bet type — always explicit stake + price. The v2
   incident this guards against was uncapped liability on a free
   bet hedge.** Persistence type (PERSIST/LAPSE) follows the race
   code per v2's `placeLay` behaviour. The route returns matched
   size/price so the UI can show partial fills.
3. The lay-then-log flow records the lay leg as a bet row in v3's
   store (side = lay, matched stake/price, commission from MBR)
   so balances and liability derive correctly per DR-019 — read
   surface: `workflows/bet_entry/v1/` modules and
   `store/schema/bets.py` for the canonical row shape (DR-032).

**Read surfaces:** `workflows/bet_entry/v1/orchestrator.py`,
`record_builder.py`, `models.py`, `betfair_adapter.py`,
`staking.py`, `placement.py` (client), and the W13 promo store
adapter for free-bet deployment events.

**Anything in the existing bet-entry workflow that does not
support a needed field (e.g. EV snapshot columns)** — Code checks
`store/schema/bets.py` first; if a snapshot field is genuinely
absent, Code records the gap as a finding and stores what the
schema supports rather than altering schema beyond what §9 allows.

### §5.5 ui/web — EV engine port (TypeScript)

**Deliverable:** v2's EV engine ported to TypeScript under
`ui/web/src/ev/` (or equivalent module path), as pure functions
with unit tests. The maths runs client-side so EV recomputes on
every ~1s price tick with no server round-trip (v2 parity; the
functions are pure and cheap).

Port, preserving behaviour exactly unless noted:

- `evEngine.js` → probability pipeline (odds → fair probabilities,
  geometric back/lay midpoint with back+2-tick fallback, corrected
  Harville place probabilities with GAMMA 0.77 / DELTA 0.62 /
  EPSILON 0.48, lazy 4th-place computation), confidence tiers
  (high / low / none on lay-spread ticks), and all EV formulas:
  raw, insurance, bonus winnings (adjusted-odds approach with cap
  clamping), boosted odds, free-bet lay-hedge, and
  `bonusWinningsEffectiveOdds` for lay sizing.
- `tickLadder.js` → Betfair tick ladder (`addTicks`,
  `ticksBetween`).
- `softOddsLadder.js` → AU soft-book price increments
  (`snapSoft`, `stepUp`, `stepDown`) for the manual-odds stepper.
- `commission.js` → **changed, not ported as-is:** commission comes
  from the market's MBR delivered by the API (§5.2). The TS module
  keeps a `getCommission(mbr)` shape with the same 8% fallback
  when MBR is missing, but no venue/state table (DR-025 S139
  amendment — Betfair is the commission source).
- Free-bet conversion default 0.70 (`DEFAULT_FB_CONVERSION_RATE`)
  carried unchanged.

**Tests:** vitest unit tests pinning the port to v2's outputs —
at minimum one fixture field (8–12 runners with back/lay) where
expected win/2nd/3rd/4th probabilities and EV values are computed
once from v2's JS and asserted in TS to 6 decimal places. This is
the regression net for the operator's daily EV numbers.

**Read surfaces:** v2 `frontend/src/utils/evEngine.js`,
`tickLadder.js`, `softOddsLadder.js`, `commission.js` (read-only).

### §5.6 ui/web — race list sidebar

v2 baseline: `TodaysRacing.jsx` + the sidebar in `RacingPage.jsx`.

- Today's races from `GET /api/v1/racing/races`, grouped/sortable
  by start time; venue + race number + code badge (T/H/G).
- Race-code and venue filters.
- Time-to-jump colouring (v2 parity: visual urgency as jump
  approaches).
- Liquidity (total matched) shown per race.
- Completed races remain selectable with a LOG affordance
  (back-capture of bets after the jump — daily reality when a bet
  was placed but not logged mid-burst).
- Refresh cadence: the list re-fetches on a slow cycle (~60s) and
  on manual refresh; only the open race polls at ~1s.

### §5.7 ui/web — odds/EV table (the race screen core)

v2 baseline: `OddsComparisonTable.jsx` (692 lines) — behavioural
parity for everything below unless the scope file cut it.

- **Columns:** runner number + name; Betfair back / lay / matched;
  raw EV%; promo EV% (when a promo config is active); manual
  soft-book odds entry with the soft-ladder stepper (§5.5);
  price-movement indicator (§5.9). The ▶ send-to-calculator button
  is CUT (scope §3) — no calculator anywhere in W17.
- **EV display:** confidence-tiered per the engine — full value
  (high), `~` prefix (low), warning prefix (none / no lay). Colour
  by sign (v2 parity).
- **Field machinery:** overround row; small-field warning;
  scratched runners excluded from field normalisation; results
  mode with placings once the market closes.
- **Per-runner promo overrides** persisted per-market for the
  session (v2 parity); storage is client-side state — server
  persistence of overrides is NOT in scope.
- **Data age:** visible last-update indicator off the polling
  envelope's `as_of`; stale envelopes surface as an aged-data
  visual state, not silently.
- **Density:** the table is the screen where scope §2 bites
  hardest — compact rows, 12+ runners visible with the log panel
  open, no horizontal scroll at laptop width.

### §5.8 ui/web — promo machinery

v2 baseline: `PROMO_PRESETS` (`promoPresets.js`, 10 presets),
`usePromoConfig.js`, the preset selector / config bar / guidance
banner in `RacingPage.jsx`.

- **Preset grid ports as-is** — the ten presets are the operator's
  real daily promo shapes (insurance $25/$50 × FB/cash × insured
  positions, free bet, bonus winnings FB/cash, boosted odds).
  Defined in one declarative TS structure.
- **Config bar:** active preset's parameters editable (max stake,
  return %, insured positions, bonus %, min odds) — v2 parity.
- **Per-runner overrides** per §5.7.
- **Promo EV wiring:** active config feeds `promoEV` per runner.
- **W13 linkage (lean):** W17 does NOT build promo-instance
  tracking UI. The presets are bet-time configuration; the W13
  promo event machinery is touched only at free-bet deployment
  (§5.4). Anything richer (promo journey surfacing, AccountCare
  warnings on the racing page) is out of scope.

### §5.9 ui/web — price-movement indicator (simple version)

Scope §4, expanded into a build spec:

- **Mechanism:** an in-session rolling price memory per runner,
  fed by the ~1s polling of the open market. Held in app memory
  only — nothing persisted to the database, nothing survives a
  page reload. Memory holds (timestamp, best back, total matched)
  tuples, pruned past the window.
- **Surface per runner:** ↑/↓ arrow + % change of best back over
  the window. Drift up (price lengthening) is the
  Strategy-2-relevant signal; visual weight goes to drifters.
- **Window:** default 5 minutes, a tunable client-side setting
  (settings stored client-side, e.g. localStorage; a settings
  server surface is NOT W17 scope). Not hard-coded anywhere.
- **Sparkline:** include a small per-runner sparkline of the
  window's price path. Cheap once the memory exists; render only
  when enough samples exist.
- **Matched-spike flag:** include. `total_runner_traded_volume` is
  already on the §9.1 price model; flag a runner whose matched
  volume jumps abnormally within the window (Code picks a simple
  robust threshold, documents it in the report, makes it a
  constant in one place). This is the "sudden money" cue.
- **Sophisticated version is OUT** (analytical arc, P2): no
  capture.db history, no drift-profile-vs-typical modelling.

### §5.10 ui/web — bet-logging panel (with v3 data surfacing)

v2 baseline: `LogBetFromRacePage.jsx` (735 lines) — inline bottom
panel, not a modal; stays open between consecutive bets;
player/bookmaker selection lifted to the page so it persists
across runner switches. All of that behaviour carries.

Ports from v2:

- Snapshot semantics: Betfair back/lay + EV snapshot captured at
  LOG click, visible timestamp + age ticker, 5-minute race-context
  staleness warning, live-vs-snapshot drift flag (>3 ticks) and EV
  shift flag (>3pp).
- Odds + stake entry; odds sanity check vs Betfair back (>30%
  divergence warning); optimal-max-stake hint for capped
  bonus-winnings FB promos; free-bet partial-use note.
- Account selection: account holder + book pickers with
  frequency-ordered book list, type-to-filter, quick-tap book
  buttons from promo assignments **only if** an equivalent
  promo→book assignment concept exists in v3's store — if not,
  quick-tap buttons are omitted and recorded as a future-work
  note (do NOT build a new assignment store for this).
- Idempotency: client key per submission, regenerated after
  success; abort/timeout handling on the POST.

New in v3 (scope §5 — the lean cut, both in the panel at log
time, neither on the odds table):

- **Free-bet inventory:** when an account-at-book is selected and
  the bet type is free-bet, the panel lists usable free bets from
  `GET /api/v1/racing/log-context` — face value, source label,
  expiry (earliest-expiry first, per the W13 derivation's sort).
  Selecting credits drives stake (v2 checkbox-list parity) and the
  deployment event on submit (§5.4).
- **Cash balance at the selected account-at-book**, same response,
  shown alongside — the W12 read-derivation (cash balance, pending
  stake, FB total) visible at log time. Read-only display; no new
  derivation logic in the UI.

### §5.11 ui/web — ⚡ quick-lay tool

v2 baseline: `HedgeModal.jsx` (628 lines). Primary daily use:
free-bet hedges and cash turnover. Behavioural parity throughout,
against v3's API.

- **Inputs:** book odds, back stake / FB amount, cash↔free-bet
  toggle. Pre-fill rules carry from v2: free-bet promo pre-fills
  FB face value + FREE type; bonus-winnings cash defaults stake
  $50 (the operator's standard size after the over-staking
  incident with the prior $100 default — preserve exactly);
  bonus-winnings FB defaults to optimal max stake rounded down to
  the nearest $5.
- **Live lay polling** of the runner at ~500ms while the modal is
  open (the §9.1 runner-best shortcut), stopping while the log
  step is open.
- **Lay sizing maths** (via the §5.5 engine): free-bet formula
  `(odds−1)×stake / (lay − commission)`; cash/bonus uses effective
  odds (`bonusWinningsEffectiveOdds` with cap + FB 0.70 discount);
  locked-profit display; commission from MBR.
- **Safety surfaces, all carried:** the FB amount "scream box" and
  confirmation banner (FB → LAY → LOCK line); FB-stake-missing
  guard; liquidity indicator (green/yellow/red on lay-side
  availability vs needed stake); partial-fill banner after
  placement (matched vs required, shortfall persisting in market).
- **Actions:** "⚡ Place Lay & Log" (places via §5.4 route, then
  opens the log step pre-filled) and "Log Back Bet Only"
  (fallback, no placement). Handicap composite identity carries
  (selectionId + handicap pair-key behaviour) for any market shape
  that needs it.
- **Bet-safety rule restated:** explicit stake + price placement
  only; never a profit-target order type (§5.4).

### §5.12 ui/web — page assembly, routing, polish

- New route(s) in `ui/web/src/routes/` (e.g. `Racing.tsx`)
  registered alongside Health/Provisional; the racing page becomes
  the app's default landing route.
- Polling lifecycle: open race polls prices at ~1s; polling pauses
  when the tab is hidden; in-flight request aborted on race
  switch (v2's abort-controller discipline carries).
- Live-polling indicator / data-age surfaces per §5.7.
- API client additions in `ui/web/src/api/` follow the existing
  `client.ts` / typed-module pattern.
- Styling consistent with the existing v3 web scaffold; dark,
  dense, monospace numerics per v2's visual register. No design
  system work — first functional cut.

## §6 — Sequencing within session

Dependency-ordered; Code may deviate where operationally cleaner
and says so in the report:

1. §5.2 client surface + contract §9.9 addition (everything
   downstream needs the race list).
2. §5.3 racing read routers (races / prices / catalogue /
   log-context).
3. §5.5 EV engine port + tests (pure, independently testable).
4. §5.6 race list sidebar → §5.7 odds table (page skeleton with
   live data and EV).
5. §5.8 promo machinery (EV table gains promo EV).
6. §5.10 log panel + §5.4 bet-logging route (bets land in v3).
7. §5.11 quick-lay + §5.4 lay route (mock-tested placement).
8. §5.9 price-movement indicator (needs the polling loop stable).
9. §5.12 assembly/polish; full test pass; report.

If the session cannot fit all nine, the coherent-checkpoint
priority is 1→6 (a page the operator can price-read and log bets
from), with 7–9 surfaced as remainder. Do not start §5.11 unless
it can be finished with its tests.

## §7 — Empirical verification

- **Pytest baseline at start:** run the full suite and record the
  result. Expected baseline 894 passed / 2 failed — the two known
  failures are the FB-inventory test time-bomb (frozen-clock fix
  routed to the M1 maintenance micro-brief, NOT this brief). Any
  other pre-existing failure is a finding. At close: baseline
  failures unchanged, zero new failures, all new tests passing.
- **New Python tests:** §5.2 client surface (parse + envelope +
  failure modes, mocked REST); §5.3/§5.4 routers (FastAPI test
  client with injected storage/mocked clients — follow
  `tests/ui/api/` patterns), including the free-bet deployment
  event write and the lay bet-row persistence.
- **New web tests:** vitest — EV engine regression fixtures
  (§5.5), indicator window pruning + % change calc, lay-sizing
  maths, log-panel validation guards.
- **Manual smoke (mock-backed):** Code runs the app end-to-end
  against mocked Betfair responses and records a short walkthrough
  in the report: pick race → see prices/EV → set promo → log a
  cash bet → log an FB bet consuming inventory → quick-lay flow to
  the partial-fill banner.

## §8 — Output spec

Single report file:
`dr029/w17_racing_pages/w17_report.md`.

Sections: (1) headline — what was built, checkpoint state if the
session ran out; (2) per-§5-section delivery notes — what landed,
deviations from brief with reasons; (3) pytest + vitest results,
baseline vs close; (4) the §7 manual smoke walkthrough; (5)
findings — surprises, gaps, anything routed to triage; (6)
future-work notes collected per §5.1/§5.10; (7) self-assessment —
length/effort vs brief, confidence per area.

Length anticipation: 400–800 lines. The report contains NO
recommendations for next workstreams and NO scope creep notes
beyond findings — routing is the next Chat session's job.

## §9 — Hard limits

Code does NOT:

- Modify anything under `bethub-v2/` (live daily system).
- Place any live Betfair order or call the live Betfair API. All
  placement-path work is mock-tested (§4 bet-safety rule).
- Touch capture.db, the VPS, or any analytical-line surface
  (DR-027/028).
- Build the calculator or any send-to-calculator affordance
  (scope §3 — cut; rethink is a separate future item).
- Build the sophisticated price-movement analytics (P2).
- Build the per-bookmaker cross-account spot-check view
  (standalone parking-lot item, detached from W17 at S145).
- Execute any M1 maintenance micro-brief item: the FB-inventory
  test clock-freeze, the two stale `_COMMISSION_TABLE`
  docstrings, the bets row-factory asymmetry, the `.importlinter`
  doc note, `betfair_adapter.py` mypy cleanup, Alembic adoption.
  All routed to M1, even where W17 code sits adjacent to them.
- Change the store schema, except additive changes explicitly
  required by §5.4 and only if unavoidable — prefer
  record-the-gap-as-a-finding. No migration framework (Alembic is
  M1's).
- Build server-side settings, promo-instance UI, sports pages, or
  account-management UI.
- Refactor existing v3 modules beyond the named touch points.
  Named anchors only; no drive-by cleanups.
- Escalate to the operator mid-session. Findings go in the report.

## §10 — What happens after Code's session

The next operator-Claude Chat session reads
`dr029/w17_racing_pages/w17_report.md` and triages: surface
findings in plain language, route any W17.1 surgical follow-up,
confirm the operator's first-use plan (exercising the live
quick-lay path on a real race at small size is the first live
validation). Post-W17, layout refinements arrive as small
refine-in-use briefs driven by the operator's daily bursts
(scope §1). Code does not write any follow-up brief.

## §11 — Cross-references

- `dr029/w17_racing_pages/scope_settlement.md` — the locked scope
  this brief expands (S145).
- DR-030 (module boundaries), DR-019 (derived state on read),
  DR-021 (Adelaide timestamps), DR-025 + S139 amendment
  (commission from Betfair MBR), DR-026/§A.10 (Betfair canonical
  for market facts), DR-032 (canonical bet record), DR-027/028
  (two-database boundary — named to exclude, not to use).
- `contracts/betfair_client_contract.md` §8, §9.1, §9.4, §9.7,
  §11.1, §14.4.
- W12 balances brief/report (`dr029/w12_balances/`) and W13 promos
  brief/report (`dr029/w13_promos/`) — the derivation surfaces
  §5.7/§5.10 consume.
- Excluded parking-lot items: calculator rethink; cross-account
  spot-check view; promo-defined columns; sophisticated price
  analytics (P2); settings-area cadence follow-up.
- M1 maintenance micro-brief (separate, independent Code session).
