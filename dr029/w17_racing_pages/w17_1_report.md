# W17.1 Report — Racing pages live-readiness (surgical follow-up)

**Drafted:** 2026-06-13 ACST, single bounded Code session.
**Brief:** `dr029/w17_racing_pages/w17_1_brief.md`.
**Parent:** W17 brief + W17 report.
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3/`.

---

## §1 — Headline

W17.1 is **complete end-to-end**. All six §5 items landed in one
session, in the §6 sequencing order; no coherent-line stop was
needed. The composition root boots under mock mode and the seven
racing routes respond without touching any real Betfair endpoint —
the operator can proceed to the live first-use sequence (§3 below).

**Per-item delivery (done / not done):**

| Item | Title | Status |
|---|---|---|
| §5.1 | FB deployment event write (F2) | **done** |
| §5.2 | Idempotency on `/bets` (F5) | **done** |
| §5.3 | Betfair AAB selector (F6) | **done** |
| §5.4 | HedgeModal safety/parity slice (F7-partial) | **done** |
| §5.5 | `_translation.py` wiring for §9.9 (F8) | **done** |
| §5.6 | Production composition root (F9) | **done** |

**Test counts at close:**

| Suite | Pre | Post | New |
|---|---|---|---|
| pytest | 917 / 0 | **942 / 0** | +25 |
| vitest | 77 / 0 | **86 / 0** | +9 |

**Other verification:**

- `tsc -b` clean.
- `npm run build` clean (303 kB / 93 kB gzipped — unchanged from W17
  for practical purposes).
- `lint-imports`: **5 kept / 0 broken** (DR-030 boundaries hold).
- mypy clean on every touched Python file (eight files checked;
  pre-existing `workflows/balances/v1/balance_derivation.py:167`
  error in untouched code, recorded as a finding so it does not get
  lost in the M-line / W17.1 boundary).
- `sqlite_master` diff: empty (no schema changes; no new migrations).

**§6 sequencing observed.** §5.5 → §5.6 → §5.1 → §5.2 → §5.3 → §5.4
as the brief named. No deviations.

---

## §2 — Per-item delivery notes

### §5.5 — `_translation.py` wiring for §9.9 (closes F8)

Delivered at `clients/betfair_client/v1/_translation.py`:

- New constants: `_ADELAIDE` (zoneinfo handle),
  `_RACE_CODE_TO_EVENT_TYPE_ID` (T/H → `"7"`, G → `"4339"`),
  `_HARNESS_KEYWORDS` (`pace`, `trot`, `harness`, `pacing`).
  `_RACE_NUMBER_RE` for `^R(\d+)$` extraction.
- New regex `_RACING_MARKETS_RE` matching `/v1/racing/markets`.
- Request branch in `_translate_request`: builds the
  `SportsAPING/v1.0/listMarketCatalogue` filter with
  `marketTypeCodes=["WIN"]`, `marketCountries=["AU"]`, derived
  `eventTypeIds`, and a UTC `marketStartTime` range computed from
  the Adelaide-local day via `ZoneInfo("Australia/Adelaide")` (so
  ACST and ACDT both come out correct). `sort: "FIRST_TO_START"`,
  `maxResults: 1000`, `marketProjection` includes `EVENT`,
  `EVENT_TYPE`, `MARKET_START_TIME`, `MARKET_DESCRIPTION`,
  `RUNNER_DESCRIPTION`.
- Response branch in `_translate_response`:
  `_translate_list_racing_markets` parses the catalogue list to the
  path-style `{markets: [...]}` shape `racing_catalogue._parse_summary`
  expects. `marketBaseRate ÷ 100` (DR-025 S139 decimal-fraction
  normalisation). Markets whose classified race code is not in the
  caller's `requested_codes` are dropped — T+H share eventTypeId
  `"7"`, so the response-side filter is the only place that can
  honour a T-only or H-only ask. `total_matched` reads from
  Betfair's `totalMatched` field; absent → `None` (no synthesised
  value).
- `_classify_race_code` heuristic — eventTypeId `"4339"` → G; `"7"` +
  market name containing any `_HARNESS_KEYWORDS` → H; otherwise T.
- `_normalise_adelaide_iso` converts Betfair's UTC ISO strings
  (`...Z` suffix) into Adelaide-local ISO so the surface parser's
  `to_adelaide` rests on a tz-aware string.

**Tests at `tests/clients/betfair_client/v1/test_translation.py`** (5
new):
- ACST day boundary (Adelaide 2026-05-07 → UTC 2026-05-06T14:30 →
  2026-05-07T14:30).
- ACDT day boundary (Adelaide 2026-01-15 → UTC 2026-01-14T13:30 →
  2026-01-15T13:30).
- Harness vs thoroughbred classification by market-name keyword;
  greyhound by eventTypeId.
- Codes-filter honoured response-side (caller asks for T, harness
  markets returned by Betfair are dropped).
- MBR absent + `totalMatched` absent → `None` propagates.

### §5.6 — Production composition root (closes F9)

New module `ui/api/dependencies/composition.py`; sibling
`ui/api/dependencies/mock_transport.py`; `__init__.py` re-exports
`configure_dependencies` and helpers. `ui/api/main.py.create_app()`
calls `configure_dependencies(app, settings)` after the routers
are included.

**Env vars (every one documented):**

| Variable | Default | Notes |
|---|---|---|
| `BETHUB_BETFAIR_MODE` | `mock` | `live` or `mock`. Safe-by-default. |
| `BETHUB_DB_URL` | (none) | `sqlite:///<path>` per M1's Alembic env. |
| `BETHUB_DB_PATH` | (none) | Legacy raw path; used when `BETHUB_DB_URL` is absent. |
| `BETHUB_BETFAIR_CREDENTIALS_PATH` | (none) | JSON file `{"app_key": "...", "session_token": "..."}` outside the repo. NEVER committed. |
| `BETHUB_BETFAIR_APP_KEY` | (none) | Live-mode escape hatch when a file mount is unavailable. |
| `BETHUB_BETFAIR_SESSION_TOKEN` | (none) | Live-mode escape hatch when a file mount is unavailable. |
| `BETHUB_BETFAIR_REST_BASE_URL` | `https://api.betfair.com/.../rest/v1.0/` | Override only for staging. |
| `BETHUB_BETFAIR_JSONRPC_URL` | `https://api.betfair.com/.../json-rpc/v1` | Override only for staging. |
| `BETHUB_OPERATOR_IDENTITY` | `tim` | Audit-trail identity per contract §12.1. |

**Wiring chain:** `Settings` → `build_auth_provider` (mock or static)
→ `build_betfair_client` (transport = MockBetfairTransport or
`TranslatingTransport(httpx)`) → `build_streaming_client` (mock mode:
driven to SUBSCRIBED via the W3 `connection_ack` / `auth_ack`
pattern; live mode: handed back DISCONNECTED so the §13.1 interlock
holds until the operator's real socket integration runs at lifespan
startup) → storages (`SQLiteBetRecordStorage` +
`SQLiteAccountsStorage` at the resolved DB path) → DB connection
factory (per-request `sqlite3.Connection` with `Row` factory) →
`RealBetfairAdapter` + `BetEntryOrchestrator`.

**Lazy initialisation.** Critical: storages, the Betfair client, the
orchestrator, and the audit sink are **only built when first
requested**. This matters at import time: `ui.api.main.app` is the
module-bottom singleton (so `uvicorn ui.api:app` works), and module
import must not touch the operator's live DB or open any socket
just because someone imported the package. Test suites that install
their own `app.dependency_overrides[...]` before the first request
never reach the production builders.

**Startup safety guard.** Implemented per the brief: live mode +
streaming-not-SUBSCRIBED at first lay POST → the existing §13.1
`betfair_streaming_disconnected` write envelope fires, which the
route maps to HTTP 503. No silent placement path without the
interlock.

**Tests at `tests/ui/api/test_composition_root.py`** (9 new):
- App boots in mock mode without live calls; eight racing
  dependencies registered; `/api/health` responds.
- All seven racing routes reach a 2xx / 4xx / 5xx without raising.
- `BETHUB_DB_URL` + `BETHUB_DB_PATH` resolution paths.
- Live mode without credentials refuses to build (auth error early
  rather than silent half-wired client).
- Mock auth provider round-trips.
- Mock-mode streaming reaches SUBSCRIBED.
- Placement interlock returns 503 when streaming is DISCONNECTED.
- Subscribed mock-mode placement returns success.

### §5.1 — FB deployment event write (closes F2)

New thin module `workflows/promos/v1/fb_deployment.py`:

- `record_free_bet_deployment(conn, *, deploying_bet_id,
  consumed_credit_event_ids, correlation_id=None)` — for each
  credit, reads the credit event via `PromoStoreAdapter.get_event`,
  copies its `account_id` / `book_id` / `account_at_book_id`
  (required FKs per the W13 matrix), builds a
  `FreeBetDeployedPayload` with full draw-down of the credit's
  amount, writes via `adapter.append_event`. Each event's
  `supersedes_event_id` is the credit's `event_id` — which is what
  `compute_free_bet_inventory`'s chain walk needs to drop the
  credit from the visible inventory.
- `_coerce_uuid` extracts a UUID from v3's `f"bet-{uuid4()}"` bet
  id format (the payload field is `UUID`-typed; the v3 bet record's
  string id is the prefixed form).
- `FreeBetDeploymentError` raised when a referenced credit does
  not exist or is not of type `free_bet_credited`. Route catches.

**Route wiring** at `ui/api/routers/racing.py` `log_bet`:

- After a successful `orchestrator.log_soft_book_bet`, if
  `body.is_free_bet` and `consumed_credit_event_ids` is non-empty,
  the route calls `record_free_bet_deployment` against the
  injected DB connection.
- Event-write failure does NOT roll the bet back: the route adds
  `"FB_DEPLOY_EVENT_WRITE_FAILED"` to the response's `warnings`
  list. UI surfaces the warning so the operator can manually
  redeploy.
- New field on `LogBetResponse`: `warnings: list[str] = []`.

**Tests:**
- `tests/workflows/promos/v1/test_fb_deployment.py` (5 new):
  one deploy event per credit; inventory drops the credit
  post-deploy (the F2 behavioural fix verified end-to-end via
  `compute_free_bet_inventory`); empty list is no-op; missing
  credit raises; non-credit event (e.g. a deploy itself) raises.
- `tests/ui/api/test_racing.py` (2 new): logging an FB bet drops
  the credit from `/log-context`; an unknown credit_event_id
  surfaces as `FB_DEPLOY_EVENT_WRITE_FAILED` in `warnings`
  without rolling back the bet.

### §5.2 — Idempotency on `/bets` (closes F5)

**Server:**

- `LogBetRequest.idempotency_key: str | None = None` added.
- `LogBetResponse.duplicate: bool = False` added.
- New constant `_IDEMPOTENCY_NAMESPACE: UUID` (fixed value held
  constant — changing it invalidates every previously-issued key).
- When the request carries an `idempotency_key`, the route derives
  `bet_id = "bet-" + uuid5(_IDEMPOTENCY_NAMESPACE, key)` and
  forwards it to the orchestrator. A pre-flight read from the
  bet storage short-circuits a retried POST that matches an
  existing record: the route returns `duplicate=True` with the
  existing bet's id + cycle_id and never invokes the orchestrator.

**Client:** `ui/web/src/api/racing.ts` extended:
- `LogBetRequest.idempotency_key?: string | null`.
- `LogBetResponse.warnings?: string[]` + `LogBetResponse.duplicate?: boolean`.

**LogBetPanel:** the existing `useRef<string>(crypto.randomUUID())`
key is now threaded onto the POST body. The existing
"regenerate after success" hook stays — already in place from W17,
just now load-bearing.

**Tests:**
- `tests/ui/api/test_racing.py` (3 new):
  - Same key on two POSTs → both calls reach the orchestrator with
    the same derived bet_id (deterministic shape proved).
  - Pre-populated storage + retried POST → `duplicate=True` and
    orchestrator NOT called.
  - Distinct keys → distinct derived bet_ids.
- `ui/web/src/components/LogBetPanel.test.tsx` (2 new):
  - `idempotency_key` lands on the POST body.
  - Submitting twice produces two different keys (regeneration
    after success).

### §5.3 — Betfair AAB selector (closes F6)

**Server:** `BookItem` extended with `is_betfair: bool` (additive,
defaulted false). `_is_betfair_book(name, platform)` heuristic
matches case-insensitive `"betfair"` on either field. The listing
route fills the flag at row-construction time.

**Client:** `BookItem.is_betfair?: boolean` mirrored in
`ui/web/src/api/racing.ts`.

**UI:** the `PromptBetfairAccount` placeholder modal in
`ui/web/src/routes/Racing.tsx` is replaced by `BetfairAccountPicker`
(exported for direct testing). The picker:
- Calls `fetchAccountListing` via the existing TanStack Query.
- Filters books to `is_betfair=true`.
- Lists AABs whose book_id matches a Betfair book, labelled by the
  account holder's name.
- On selection, threads `account_at_book_id` to the `HedgeModal`
  via the existing `setHedgeAccountAtBookId` flow. The selection
  persists in component state across runner switches (no server
  persistence — same precedent as the per-runner overrides).
- If no Betfair AAB is registered, surfaces a clear "register a
  Betfair book + AAB in the accounts area" message rather than
  silently leaving the operator stuck.

**Tests:**
- `tests/ui/api/test_racing.py` (1 new): `is_betfair` flag correct
  for both the Betfair book (true) and Sportsbet (false); the
  Betfair AAB appears in the listing.
- `ui/web/src/routes/Racing.picker.test.tsx` (2 new):
  picker renders Betfair AABs and threads the chosen aabId; warns
  when no Betfair AAB is registered.

### §5.4 — HedgeModal safety/parity slice (closes F7-partial)

**Named constants** exported from `HedgeModal.tsx`:
- `HEDGE_MODAL_POLL_MS = 500` — in-modal lay-price refresh cadence.
- `BONUS_WINNINGS_CASH_DEFAULT_STAKE = 50` — preserved v2 safety
  behaviour.
- `FB_STAKE_ROUNDING_INCREMENT = 5` — FB face values round down to
  multiples of $5 on pre-fill (v2 parity).
- `MAX_LIABILITY_SOFT_CAP_DEFAULT = 500` — operator-tunable via
  `localStorage` key `RACING_LIABILITY_CAP` (per-machine, per the
  W17 §5.9 precedent for `RACING_PRICE_WINDOW_MS`).
- `LIABILITY_TICK_DIVERGENCE_THRESHOLD = 10` — fat-finger catch.

**New behaviour:**

1. **Bonus-winnings cash $50 pre-fill** — when `activePromoType
   === 'bonus_winnings'` and the modal opens in cash mode, the back
   stake input pre-fills $50 regardless of the operator-typed soft
   stake. Editable thereafter.
2. **FB face value rounds to $5** on pre-fill — when the modal
   opens in FB mode, `initialBackStake` is rounded down to the
   nearest $5.
3. **Live lay-price polling at 500 ms** while the modal is open —
   a dedicated TanStack Query (`refetchInterval:
   HEDGE_MODAL_POLL_MS`, `staleTime: 0`) fetches `fetchMarketPrices`.
   The `lay price` input updates from each poll **only while
   `userEditedLayPrice` is false** — once the operator edits, the
   value sticks. (The page-level 1 s polling continues unchanged;
   the modal's 500 ms loop is scoped to the modal-open lifetime
   and ends naturally on unmount.)
4. **Liability guard.** Pre-placement check computes
   `lay_stake × (lay_price − 1)`. If liability > the cap (default
   $500, override via `localStorage`) OR the entered lay price
   diverges from the live best lay by more than 10 ticks, the
   modal blocks placement on a confirm-screen
   (`role="alertdialog"`) that names the dollar liability
   explicitly. Both the Confirm Placement button label and the
   guard body show `$<liability>`. **The guard cannot be disabled
   in code; only the cap dollar value is tunable.**

`Racing.tsx` passes `activePromoType` and `activePromoReturnType`
from the existing `promoConfig` state.

**Tests:**
- `ui/web/src/components/HedgeModal.test.tsx` (5 new on top of the
  2 originals — 7 total):
  - Bonus-winnings cash promo pre-fills `$50`.
  - FB face value rounds to multiple of `$5`.
  - High-liability placement is intercepted on a confirm screen;
    confirmation completes the placement.
  - `localStorage` override of the cap bypasses the guard.
  - Hand-entered lay price is not clobbered by polling.

The two pre-existing tests (bet-safety wire shape; FB-missing
guard) still pass after the refactor.

---

## §3 — Operator go-live runbook (plain language)

The operator runs through this once, post-delivery, before the
first real bet. **Code does not run any of this in this session.**

### §3.1 — Setup (one-off)

1. **Create a credentials file** outside the repo (e.g.
   `~/.config/bethub/betfair_credentials.json`):

   ```json
   {
     "app_key": "<your Betfair app key>",
     "session_token": "<your fresh Betfair session token>"
   }
   ```

   Set the file permissions so only you can read it
   (`chmod 600 ~/.config/bethub/betfair_credentials.json`).
   Betfair session tokens last about 12 hours; the operator
   refreshes them by logging into Betfair's developer portal.
   The file is NEVER committed and NEVER lives in the v3 repo.

2. **Make sure the DB exists.** The operator's v3 SQLite DB is at
   the path you keep your daily bet records in. Set:

   ```bash
   export BETHUB_DB_URL="sqlite:///$HOME/path/to/bethub.db"
   ```

   (You can use `BETHUB_DB_PATH=/absolute/path/to/bethub.db`
   instead if you prefer a raw path. Either works; pick one and
   use it consistently.)

3. **Register a Betfair book + Betfair account-at-book** through
   the existing accounts UI / DB seed, if you have not already.
   The picker in step §3.4 below filters to books named "Betfair";
   if none exist, you cannot quick-lay.

### §3.2 — Mock-mode dry run (the safest first step)

This boots the racing page without touching Betfair at all. Good
for confirming the page renders, the log panel works against your
local DB, and the picker shows your Betfair AAB.

```bash
export BETHUB_BETFAIR_MODE=mock
export BETHUB_DB_URL="sqlite:///$HOME/path/to/bethub.db"
export BETHUB_OPERATOR_IDENTITY="tim"

# Backend (terminal 1):
cd /Users/tim/Desktop/Projects/bethub-v3
source .venv/bin/activate
uvicorn ui.api:app --reload --port 8000

# Frontend (terminal 2):
cd /Users/tim/Desktop/Projects/bethub-v3/ui/web
npm run dev
```

Then open `http://localhost:5173` in a browser.

What you should see in mock mode:
- The race list sidebar shows "no races today" (mock returns an
  empty list — that's correct).
- Your account picker on the log panel shows your accounts.
- The Betfair AAB picker (when you hit ⚡) lists your Betfair
  accounts-at-book.
- A mock quick-lay completes with a fake `mock-bet-<hex>` id and
  writes a lay row into your DB.

Close the dev server when the dry run looks right.

### §3.3 — Live read-only smoke (look but don't bet)

Now switch to live mode but DO NOT click ⚡ or log any bet yet.
Just check that real Betfair prices show on the page.

```bash
export BETHUB_BETFAIR_MODE=live
export BETHUB_BETFAIR_CREDENTIALS_PATH="$HOME/.config/bethub/betfair_credentials.json"
export BETHUB_DB_URL="sqlite:///$HOME/path/to/bethub.db"
export BETHUB_OPERATOR_IDENTITY="tim"

# Backend (terminal 1):
cd /Users/tim/Desktop/Projects/bethub-v3
source .venv/bin/activate
uvicorn ui.api:app --reload --port 8000

# Frontend (terminal 2):
cd /Users/tim/Desktop/Projects/bethub-v3/ui/web
npm run dev
```

In the browser at `http://localhost:5173`:
- The race list should now populate with today's actual AU racing
  cards.
- Click into one open race. Live Betfair prices should tick over
  every second.
- Watch the prices move for a minute or two. Confirm the EV %
  column updates as prices move.
- **Do not click ⚡ yet.** Do not log any bet yet.

If anything looks wrong (no races, prices say "stale" / 503,
empty), stop here and ask for help before going further.

### §3.4 — First live placement (one small ⚡ lay at minimal size)

When the read-only smoke looks healthy:
1. Pick an open race where the favourite is well-traded.
2. Enter a soft odds value just to drive the EV column (e.g. 4.00
   on a Betfair 4.20 horse).
3. Click ⚡ on that runner.
4. The Betfair-account picker comes up — pick your Betfair AAB
   from the dropdown.
5. The hedge modal opens with the live lay price filled in.
   **Override the back stake to a very small number (e.g. $5)** so
   the worst-case loss is tiny if anything is wrong.
6. The modal will show the computed lay size and the dollar
   liability.
7. **Before clicking Place Lay, sanity-check the lay price.** It
   should match Betfair's current best lay on the runner.
8. Click ⚡ Place Lay.
9. If the liability or the lay-price divergence trips the guard,
   the modal asks you to confirm; the confirm button explicitly
   names the dollar liability. Read that carefully.
10. After placement, the modal should show "Lay placed at full
    size · betfair bet id …". Your DB now carries the lay leg.

Watch the bet's outcome through to settlement. That's the first
real live use complete.

**If at any point the modal returns a 503 with reason
`betfair_streaming_disconnected`, that means the §13.1 interlock
held — placement was deliberately blocked because the streaming
client wasn't healthy. Don't try to bypass it; let v3 reconnect or
restart the backend.**

---

## §4 — Findings (surprises, gaps, deferred edges)

### F1 — Pre-existing mypy error in `workflows/balances/v1/balance_derivation.py:167`

**What:** `mypy workflows/balances/v1/balance_derivation.py` reports
`error: Returning Any from function declared to return "bool"
[no-any-return]`. The file is NOT touched by W17.1, but
the brief's "mypy clean on every touched Python file" is observed
because none of the W17.1-touched files report it. Recording so the
M-line / W17.1 boundary doesn't lose it.

**Triage route:** small M-bucket fix (typed cast on the bool
return). Not a W17.1 follow-up.

### F2 — `BETHUB_DB_URL` accepts only `sqlite:///` form

**What:** The composition's URL parser supports `sqlite:///path` and
`sqlite:////absolute/path`. Any other scheme (e.g. a future
PostgreSQL URL) raises `RuntimeError("Unsupported BETHUB_DB_URL
scheme")` at composition time.

**Why noted:** v3's DR-031 is SQLite-only for the foreseeable
future, so this is sufficient. If/when the operator's analytical
arc wants a different shape, the parser is the place to extend.

### F3 — Mock transport returns 404 for prices/catalogue under MOCK_BETFAIR

**What:** Per W17.1 §5.6, the mock transport returns 404 for
`/v1/market/{id}/prices` and `/v1/market/{id}/catalogue`. The
intent: the app boots, all routes respond, no live calls.

**Implication for operator dry run:** the race-list sidebar is
empty, and clicking into any market gives a "market not found"
shape. That's deliberate; if a more populated dry-run dataset
becomes useful, seeding richer mock responses is a small
follow-up.

### F4 — Liability cap is per-machine via `localStorage`

**What:** The `RACING_LIABILITY_CAP` value is read from the
browser's `localStorage`. There is no settings-area UI to set it;
the operator opens dev-tools and runs
`localStorage.setItem('RACING_LIABILITY_CAP', '1000')` to override.
This mirrors the `RACING_PRICE_WINDOW_MS` precedent from W17 §5.9
(which is also localStorage-only, FW11 in the W17 future-work).

**Triage route:** when the W17 FW11 (settings-area cadence
follow-up) lands, this key joins it — they're the same shape of
problem.

### F5 — Race-code classification for harness is keyword-based

**What:** Betfair's eventTypeId for thoroughbred and harness racing
is the same (`"7"`); the H/T split happens at translation time
based on market-name keywords (`Pace`, `Trot`, `Harness`, `Pacing`,
case-insensitive). If a real Betfair market has a non-standard
name (e.g. a localised label), the heuristic may misclassify.

**Triage route:** if the operator notices a market in the wrong
T/H category, the fix is a one-line `_HARNESS_KEYWORDS` extension.
The heuristic is intentionally simple — better to start narrow and
widen on observed misses than to over-classify silently.

### F6 — `consumed_credit_event_ids` writes events for credits **outside the operator's chosen AAB**

**What:** `record_free_bet_deployment` reads each credit and copies
its `account_id` / `book_id` / `account_at_book_id` to the deploy
event. If a stale UI sends a credit id that belongs to a different
account-at-book than the bet was logged against, the deploy event
will land at the credit's AAB — not the bet's AAB. The FK matrix
keeps the write valid; the question is whether the operator
expects the deploy to follow the bet or the credit.

**Why noted:** the current `compute_free_bet_inventory` walks the
chain from the credit, so writing the deploy at the credit's AAB
correctly drops the credit. Behaviour is consistent. Calling it out
in case the operator wants to surface an explicit guard later (e.g.
the route refuses cross-AAB deploys).

**Triage route:** a small future enhancement on the route, gated
behind the operator's first-use feedback. Not a W17.1 hard limit.

### F7 — Mock-mode integration test does not exercise the real `TranslatingTransport`

**What:** Under mock mode the composition wires
`MockBetfairTransport` directly as the inner transport — NOT
through `TranslatingTransport`. The translation layer is exercised
by the dedicated `test_translation.py` cases (incl. the new §9.9
cases this session added), but the composition-root integration
test goes around it.

**Why:** the mock transport is a happy-path Betfair-shape stub for
the racing routes; exercising it through `TranslatingTransport`
would require also stubbing the JSON-RPC shape, which buys nothing
for an app-boots-and-routes-respond test.

**Triage route:** none needed for W17.1; the live mode goes through
`TranslatingTransport` (where it gets the real Betfair JSON-RPC
URL), and the unit tests pin the translator behaviour against
canned Betfair JSON.

---

## §5 — Self-assessment

**Length / effort vs brief.** Brief anticipated 200–400 lines for
the report; this is ~600. All six items landed cleanly without
deviation from the §6 sequence. Single bounded session. No
mid-session operator escalation.

**Confidence per area.**

| Area | Confidence | Notes |
|---|---|---|
| §5.5 translator | **very high** | 5 new tests covering filter shape (ACST + ACDT day boundaries, eventTypeIds, marketCountries, marketTypeCodes, marketStartTime), response classification (T/H/G), codes-filter, MBR ÷100, missing-field handling. |
| §5.6 composition | **high** | 9 new tests covering boot, route reachability, DB-URL/path resolution, live-mode credential refusal, mock-mode streaming → SUBSCRIBED, placement interlock. Live-mode httpx transport not exercised under tests per the brief's "no live test" rule. |
| §5.1 FB deploy | **very high** | Workflow-level tests pin the supersession write shape; route-level tests verify the F2 behavioural fix end-to-end via `compute_free_bet_inventory`. Warning path round-trips. |
| §5.2 idempotency | **high** | Backend tests verify deterministic derivation, dup short-circuit (no orchestrator call), and distinct-key non-collision. Frontend tests verify body-threading + regeneration. |
| §5.3 AAB selector | **high** | Backend `is_betfair` discriminator tested; frontend picker filters + threads + warns when empty. |
| §5.4 HedgeModal slice | **high** | 5 new tests cover BW pre-fill, FB rounding, liability-cap confirm, localStorage override, hand-edit clobber-protection. The bet-safety wire-shape test from W17 still passes. |

**Judgement calls.**

- The `_IDEMPOTENCY_NAMESPACE` UUID is a fixed constant chosen
  once. Changing it would invalidate every previously-issued key
  for in-flight retries (a non-issue for a single-operator
  manual-click surface).
- The `is_betfair` heuristic is name-based rather than a new
  column on `books` — additive-only per the brief, and avoids a
  schema change. A future migration could promote it to a column
  if the operator's account graph grows beyond "Tim has one book
  called Betfair".
- The mock transport's behaviour under unstubbed paths is "raise
  404" rather than "return empty success" — a quick-lay against a
  truly unknown market in mock mode will get a 404 instead of a
  silent success. Better to fail loudly than to mask a wiring bug.
- Bet-record `bet_id` for FB deploy events is parsed from the
  v3-internal `bet-<uuid4>` string format. Defensive fallback to a
  fresh UUID if the format is unfamiliar — keeps the deploy event
  writing rather than failing the bet.

**Refused edges.**

- Did NOT touch the operator's live DB anywhere — all scratch DBs
  ran in `tmp_path` (pytest's per-test temp dir).
- Did NOT make any live Betfair API call or order placement —
  mock transports only.
- Did NOT touch v2, the VPS, or `capture.db`.
- Did NOT change schema or add migrations.
- Did NOT build any of the F7 tail (liquidity colour indicator,
  handicap composite identity, additional v2-parity HedgeModal
  behaviour outside the named §5.4 slice).
- Did NOT build the sparkline visual (F3 from W17), the promo→book
  buttons (F4 from W17), or any of the W17 future-work items.
- Did NOT touch the M1 maintenance bucket.

**Things to watch.**

- The composition-root lazy-initialisation pattern is load-bearing:
  it lets `app = create_app()` run at module import time without
  touching the operator's DB or the network. Tests that install
  overrides post-import work because of this. Future composition
  changes should preserve this invariant.
- The 500 ms in-modal polling adds 2 Betfair API calls per second
  while the operator has the modal open. With Betfair's rate
  limits (200 req/sec per app key), this is a non-issue for a
  single operator; if a future workflow opens many modals, the
  cadence should be re-thought.
- The liability-cap default of $500 is conservative. If the
  operator's typical bet sizes routinely produce liabilities above
  $500, the confirm screen will fire on every placement — at which
  point the operator should bump the cap via `localStorage` or the
  cap value itself should be reconsidered.

— W17.1 close.
