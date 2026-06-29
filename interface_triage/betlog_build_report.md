# BetLog build report

**Status:** complete — full build (§5.1–§5.8) landed in a single bounded
session. Both suites green; settlement seam byte-identical.
**Built per:** `interface_triage/betlog_build_brief.md` (locked S171),
against `betlog_scope.md` (S169, amended S171) +
`betlog_review_report.md` (S171).
**Repo (code, read-WRITE — named §5 anchors only):**
`/Users/tim/Desktop/Projects/bethub-v3`.
**Session window:** 2026-06-20 ~15:27 → ~15:52 ACST (Adelaide local,
DR-021).
**Verdict:** all eight pieces built and tested; the backend stop-point
(§5.1–§5.7) was reached with budget to spare, so §5.8 was carried too —
no session split.

> Scope discipline: only the §5 anchors were touched; the settlement /
> placement seam (§8) is unchanged; no `.db` was read or written; no git
> state-changing operations were run. Proof below.

---

## §0 — Baselines (captured at session start, before any edit)

Per §7 / DR-031:

| Suite | Command | Pre-build | Post-build | Delta |
|---|---|---|---|---|
| Python | `uv run pytest -q` | **1028 passed, 4 warnings** | **1092 passed, 4 warnings** | +64 new, 0 regressions |
| Frontend | `npm test` → `vitest run` | **91 passed / 14 files** | **99 passed / 15 files** | +8 new, 0 regressions |

The 4 Python `DeprecationWarning`s (`HTTP_422_UNPROCESSABLE_ENTITY`) and
the 2 benign vitest `--localstorage-file` warnings are the pre-existing
noise named in the review §G.3 — unchanged, none added, none "fixed"
(out of scope per §10). No skipped/xfailed tests in either suite.

New tests: **64 Python** (27 store + 14 P&L + 23 endpoint) + **8
frontend** = 72 total.

---

## §1 — Per-piece build summary

### §5.1 — Filtered bets read (`store/repositories/bets.py`)

Added three store-pure read methods to `SQLiteBetRecordStorage` (and the
matching `BetRecordStorage` Protocol stubs):

- **`list_bets(...)`** — every filter optional + combinable:
  `account_at_book_ids` (the resolved AAB-id set — see §5.6),
  `cycle_ids`, `strategy_tags`, `is_free_bet`, `placed_from`/`placed_to`
  (date range), and `settlement_states`. Newest-first
  (`ORDER BY placed_at DESC, bet_id DESC`) with `offset`/`limit`
  pagination — the offset/limit shape the review (§C.3) said did not
  exist. Legs for the whole page are fetched in **one** `IN (...)` query
  and grouped in memory, so this is *not* the per-row leg N+1.
- **`count_bets(...)`** — total matching-row count over the same filter
  set, so the feed can report `total` for pagination.
- **`count_bets_by_cycle(cycle_ids)`** — `{cycle_id: count}` for the row
  cycle marker (§A.4).

The filter SQL is shared between `list_bets` / `count_bets` via a single
module helper `_bets_filter_sql(...)`, which returns `None` for an
**unsatisfiable** filter (an explicitly empty id set, e.g. a persona
with zero account-at-book rows, or an empty settlement-state set) so the
callers short-circuit to empty rather than emit `IN ()`. The
`settlement_states` tuple may contain `None` to match SQL `NULL` (a
freshly-logged bet before its first settlement pass) — this is what lets
the "Pending" toggle include both `NULL` and `'pending'`.

**Store-pure confirmed:** the new code uses stdlib + `sqlite3` only; no
`workflows` import. `store-pure` import-linter contract holds.

**No new index added** (§5.1 / §10). At v3's day-0 data scale the
filtered scan is correct and fast; the natural candidates if the
operator's book grows are `bets(placed_at)` and
`bets(account_at_book_id)` — noted, not added speculatively.

### §5.2 — Per-bet P&L (`workflows/balances/v1/balance_derivation.py`)

The existing `_bet_cash_return` was **reused, not recomputed** (§5.2).
Three thin public wrappers were added next to it:

- `bet_cash_return(row)` — gross cash return (stake included).
- `bet_net_pnl(row)` — **net profit/loss**, the figure BetLog shows.
- `bet_is_settled(state)` — gate for "P&L once settled".

The net step (§5.2 caveat 1, "the further `return − stake` step") is:

> **net P&L = gross cash return − cash committed at placement**
> = `_bet_cash_return(row) − _bet_cash_stake_committed(row)`

This reuses **both** existing DR-019 derivations unchanged and collapses
to the correct figure across the full matrix — verified by test:

| Case | net P&L |
|---|---|
| won cash back (10 @ 3.0) | `+20.00` (= stake×(price−1)) |
| lost cash back | `−10.00` |
| void cash back | `0` |
| won free bet (conv 0.7) | `+14.00` (winnings-only × conversion) |
| lost free bet | `0` |
| won lay (S=10, c=8%) | `+9.20` (= S×(1−c)) |
| lost lay | `−20.00` (= −liability) |
| lay, NULL commission | 8% fallback applied |

The wrappers accept any column-addressable mapping (a `sqlite3.Row` *or*
a plain dict), so the read API feeds them the row shape they expect
(§5.2 caveat 2–3) without un-privatising the originals or disturbing
existing callers. The 8% fallback reads the **single existing**
`_DEFAULT_COMMISSION` (`:153`) — **no third copy** (§5.2 caveat 3).
P&L is derived on read; **no schema change, no stored column.**

### §5.3 — Bets-feed GET endpoint (`ui/api/routers/bets.py`, new)

A **new router** `ui/api/routers/bets.py`, mounted `prefix="/api"`
alongside the others in `ui/api/main.py` and re-exported from
`ui/api/routers/__init__.py` (the two-line composition pattern). DR-030 /
import-linter clean — routers aren't individually named in
`.importlinter`, and `ui → store/domain/workflows` stays within the
layered contract.

- `GET /api/v1/bets` — takes the §5.1 filters + pagination as query
  params and returns its **own** typed response models (`BetFeedResponse`
  / `BetFeedItem` / `BetLegItem`), defined locally as `LogContextResponse`
  does. The Betfair `_envelope_to_http` freshness helper was **not** used
  — a bets feed has no staleness axis (review §C.2).
- **Server-side** filtering + pagination (no pull-all-and-filter-in-
  memory, §C.3).
- Reuses the existing DI providers `get_bet_storage` (reads) and
  `get_accounts_storage` (reference maps) — **no new providers** (§5.3).

### §5.4 — Edit write path (scoped, fenced)

**Store fence** (`SQLiteBetRecordStorage.edit_bet`): only the four
editable fields are parameters; every settlement-driving field
(`settlement_state`, `match_status`, `commission`, `side`, the leg
`betfair_market_id`/`betfair_selection_id`, `cycle_id`) is **structurally
un-editable** — it is not a parameter and cannot be reached. `strategy_tag`
is always editable; `requested_stake`/`matched_stake`/`matched_price` are
editable **only while PENDING** (`settlement_state` in {NULL, `pending`})
— on a settled / in-review bet a stake/price edit is **rejected** (a
`WriteResult` with an `error_message` prefixed `blocked:`). A private
`_UNSET` sentinel distinguishes "leave untouched" from "set to NULL"
(clearing `strategy_tag` is a valid edit).

**Endpoint** (`PATCH /api/v1/bets/{bet_id}`): `BetEditRequest` is
`extra="forbid"`, so any never-editable field a client sends is rejected
with **422** before the store is even called. `model_fields_set` drives
presence (so `{"strategy_tag": null}` clears, omission leaves). The store
fence result maps: `bet_id not found` → **404**, `blocked:` → **409**,
else 500.

### §5.5 — Promo display (strategy-tag only — locked)

No build beyond the tag (§5.5). The row/filter use `strategy_tag` (the
closed 4-value enum) + the `is_free_bet` "Free" marker; the tuck-in shows
the free-bet conversion rate (`realised_conversion_rate` preferred, else
`free_bet_conversion_rate`). **No promo fine print, no bet→promo join** —
none was built. The frontend carries `STRATEGY_TAG_LABELS` (Safety Net /
Price Booster / SGM / Synthetic Each-Way) for display.

### §5.6 — Persona / book reference join + the Book key

**Reference maps pre-loaded once per request, joined in memory**
(`_load_reference_maps`) — mirrors `racing.list_accounts`
(`list_active_accounts` + `list_active_books` + all active accounts-at-book
in one shot). No per-row query (the §A.3 N+1 is avoided).

**The Book key is the structured path** (`_resolve_account_at_book_ids`):
`book_id → list_active_accounts_at_book_for_book(book_id) →` AAB-id set
`→ bets.account_at_book_id IN (...)`. The free-text `bets.book_or_exchange`
is **not** used as a filter key (operator-locked S171) — it is carried on
the row for *display only*. Account (persona) and account-at-book resolve
to AAB-id sets the same way; when more than one selector is supplied the
sets are **intersected** ("persona X at book Y" narrows correctly), and an
empty resolution yields an empty feed (a silently-matches-everything lens
would be worse than useless, §5.6).

### §5.7 — Delete write path (hard, fenced)

**Store fence** (`SQLiteBetRecordStorage.delete_bet`): implements the
operator-locked rule (S171, "go hard") — hard-delete **only** when the
bet is BOTH unsettled (`settlement_state` in {NULL, `pending`}) AND
un-cycled (no other bet shares its `cycle_id`, and no `ops_events` /
`promo_events` reference it). Any other case is **blocked** with a clear
`blocked: …` message — never a silent no-op.

Mechanics per §D.2:

- A single transaction (`BEGIN IMMEDIATE` → delete `bet_legs` → delete
  `bets` → `COMMIT`, `ROLLBACK` on error) — there is no
  `ON DELETE CASCADE` (`store/schema/bets.py:66`).
- `PRAGMA foreign_keys = ON` is kept (set by `_connect`, `:474`) so an
  **unexpected** `ops_events` referent surfaces as an FK error at the
  `DELETE FROM bets` step rather than a silent orphan — the backstop
  behind the explicit pre-check.
- The `ops_events` (`bet_id` OR `cycle_id`) and `promo_events`
  (`correlation_id`) pre-checks run **only against whichever of those
  tables exist** in the connected database (checked via `sqlite_master`),
  so the method is self-contained: a bets-only test DB has neither table
  and the method still works.
- The `promo_events` check keys on `correlation_id`. The free-bet deploy
  writer stores it as the **UUID parsed out of** the bet's `cycle_id`
  (the `cycle-`/`bet-` prefix stripped, normalised — see
  `racing.py:_safe_uuid`), not the raw cycle string. A pure-string helper
  `_correlation_candidates(cycle_id)` builds the raw, prefix-stripped, and
  normalised-UUID forms so the fence catches a real referent regardless of
  which form was written (kept store-pure — no ui-convention import).

**Endpoint** (`DELETE /api/v1/bets/{bet_id}`): `bet_id not found` → 404,
`blocked:` → 409, success → 200 `{success, bet_id}`.

### §5.8 — Frontend page (`ui/web/`)

The frontend additions, following the established routed + typed +
react-query + CSS-module conventions:

- **Route + nav:** `<Route path="/betlog">` and a `<Link to="/betlog">`
  "BetLog" in `App.tsx`'s `NavBar` (verified by grep + vitest, not diff —
  `ui/web/` is untracked, §10).
- **Data layer:** new `src/api/bets.ts` (`fetchBetFeed` / `fetchCycleBets`
  / `editBet` / `deleteBet` + types + the strategy-tag enum/labels), over
  the typed wrappers. **Added `apiDelete`** to `src/api/client.ts` — the
  only missing primitive (get/post/patch existed; delete did not). Edit
  uses `apiPatch`. The filter dropdowns reuse the racing router's
  `fetchAccountListing`.
- **The page** (`src/routes/BetLog.tsx` + `BetLog.module.css`): a flat,
  **newest-first** list (no race grouping); filters across the top
  (account / account-at-book / book / promo-type-as-strategy-tag /
  free-or-cash / date from-to / state toggle Pending·Settled·All); a
  scannable row (date, selection, side, Free marker, stake @ odds, state,
  P&L once settled, book + persona, cycle marker); a tuck-in on open (bet
  id, exact timestamp, commission, strategy tag + conversion rate, the
  **cycle chain** reconstructed read-side via `?cycle_id=` ordered by
  `placed_at` with a running net, §A.4); and the **Edit + Delete** actions
  — fenced in the UI (stake/price inputs disabled once not pending; Delete
  disabled unless pending && un-cycled) mirroring the server, which stays
  the source of truth (a server `blocked:` 409 is surfaced as an inline
  error).
- **"Placed?" confirm — SCAFFOLD ONLY.** Rendered in the tuck-in actions
  row, **disabled, wired to nothing** (`data-testid=
  "placed-confirm-scaffold"`), with a "coming soon — brief 3" title. No
  write path. It is named here as the **brief-3 seam** (free-bet
  credit-in, landing in `workflows/promos/v1/`, §E.3).
- **vitest:** `src/routes/BetLog.test.tsx` (8 tests) matches the existing
  `*.test.tsx` pattern.

---

## §2 — Sequencing (§6)

Built in the dependency order the brief named: §5.1 + §5.6 (data spine) →
§5.2 (P&L) → §5.3 (GET) → §5.4 + §5.7 (write paths) → §5.8 (frontend).
Each piece was unit/endpoint-tested as it landed (store tests → P&L tests
→ endpoint tests → vitest), so no piece was built on an unverified one.

---

## §3 — Test results (detail)

**Python — `uv run pytest -q`: 1028 → 1092 (+64), 0 regressions.**

New files:

- `tests/store/repositories/test_bets_betlog.py` (**27**) — `list_bets`
  ordering / pagination / each filter / NULL-settlement / unsatisfiable
  empty set; `count_bets`; `count_bets_by_cycle`; `edit_bet` fence
  (strategy always, stake-on-pending OK, stake-on-not-pending blocked ×4
  states, clear-to-NULL, not-found); `delete_bet` fence
  (unsettled+uncycled OK incl. legs gone, NULL-settlement OK, blocked when
  settled ×4, blocked when cycled, not-found, blocked by `ops_events`
  referent, blocked by `promo_events` UUID-form referent).
- `tests/workflows/balances/v1/test_betlog_pnl.py` (**14**) — the
  back/lay/free × won/lost/void net-P&L matrix + 8% fallback +
  `bet_is_settled`.
- `tests/ui/api/test_bets.py` (**23**) — feed newest-first + total, label
  join, P&L only once settled, cycle marker, every filter (incl.
  structured book key + persona∩book intersect), pagination, 422 on bad
  strategy tag; PATCH (tag OK, stake-on-pending OK, stake-on-settled 409,
  settlement-field 422, missing 404); DELETE (pending standalone 200 +
  gone, settled 409, cycled 409, missing 404).

**Frontend — `vitest run`: 91 → 99 (+8), 0 regressions; `tsc -b` clean.**

`src/routes/BetLog.test.tsx` (8) — rows render (state / P&L / Free
marker), cycle marker only for multi-bet cycles, tuck-in + inert Placed?
scaffold, edit via apiPatch, delete via apiDelete, delete disabled for
settled/cycled, blocked-delete server message surfaced, state toggle
drives the feed query.

No deviation from the 1028 / 91 baselines beyond the new tests; warning
counts unchanged.

---

## §4 — Settlement-seam confirmation (§8) — git diff proof

The four do-not-touch files are **byte-identical to session start**.
`git hash-object` at start and at close:

| File | Hash (start == close) |
|---|---|
| `workflows/bet_entry/v1/settlement.py` | `ab95ea35c3ce58e2b0124ba089fa1bb358552f25` |
| `workflows/bet_entry/v1/reconciliation.py` | `13a7558d03198cacee49c65b2b119eed0ad3b2c0` |
| `workflows/bet_entry/v1/orchestrator.py` | `e4cb691b8426d8f2cdf1be4f6d338b59b3b586b3` |
| `clients/betfair_client/v1/placement.py` | `2cc726860c2d6284028aad39d2d6ae1581ba5d10` |

`git diff --stat` on the three `bet_entry` files at close is **empty**
(clean vs HEAD too). `placement.py` shows a pre-existing diff vs HEAD
(+51 lines) — that change was **already in the dirty tree at session
start** (W3 work); its hash being unchanged from my start snapshot proves
**I added nothing to it**.

**Why the seam held (review §E.2, confirmed in build):** BetLog's
edit/delete are repository-level writes. `store/` imports nothing from
`workflows` (store-pure, import-linter), so a repository write **cannot**
reach the settlement engine — the only coupling is data, on settlement's
*next* live-row read, which is exactly why §5.4 fences the
settlement-driving fields and §5.7 blocks deletes of anything settlement
may still touch. Placement is untouched — BetLog places no bets.

---

## §5 — Dirty-tree discipline (§10)

- **No git state-changing ops** — no `add`/`commit`/`stash`/`restore`/
  `checkout`/`reset` were run. (Read-only `git status` / `git diff` /
  `git hash-object` / `git ls-files` only.)
- Working-tree state was read at session start and the tracked-modified
  (`M`) file list at close is **identical** to that snapshot — **no
  committed-tracked file was newly modified by this session.**
- **All edited files are part of the in-flight untracked tree** (the
  operational store + ui layers, untracked at session start), confirmed
  via `git ls-files --error-unmatch`. So there were no *tracked*-file
  edits requiring per-file diff review; the seam files (committed/tracked)
  were verified untouched by hash instead.
- **`ui/web/` is untracked** → the frontend was verified by **grep +
  vitest**, not diff (route + nav in `App.tsx`, `apiDelete` in
  `client.ts`, inert `placed-confirm-scaffold` in `BetLog.tsx` all grep-
  confirmed; 8 vitest tests green).
- **No `.db` access** — the build touched no live data. Tests use
  `tmp_path` SQLite only.

**Files edited** (all within already-untracked in-flight files):
`store/repositories/bets.py`, `workflows/balances/v1/balance_derivation.py`,
`ui/api/main.py`, `ui/api/routers/__init__.py`,
`ui/web/src/api/client.ts`, `ui/web/src/App.tsx`.

**Files created** (new): `ui/api/routers/bets.py`,
`ui/web/src/api/bets.ts`, `ui/web/src/routes/BetLog.tsx`,
`ui/web/src/routes/BetLog.module.css`,
`ui/web/src/routes/BetLog.test.tsx`,
`tests/store/repositories/test_bets_betlog.py`,
`tests/workflows/balances/v1/test_betlog_pnl.py`,
`tests/ui/api/test_bets.py`.

---

## §6 — Anchor drift vs the review

The review was read-only against an in-flight tree; every anchor was
re-verified against the live file before editing. **No material drift was
found** — the cited line regions resolved as described:

- `list_unsettled_bets` SQLite impl at `:754`, `PRAGMA foreign_keys = ON`
  at `:474`, `max_results` seed pattern — all present as cited.
- `_bet_cash_return` `:189-279`, `_bet_cash_stake_committed` `:303-325`,
  `_DEFAULT_COMMISSION` `:153` — present as cited (the net-P&L reuse
  leans on `_bet_cash_stake_committed`, which the review named in passing;
  it carries the lay-liability and free-bet-zero logic that makes the
  subtraction correct).
- racing DI providers `get_bet_storage` `:167`, `get_accounts_storage`
  `:176`, `get_db_connection` `:185`; `_models_to_jsonable` `:335`;
  `LogContextResponse` `:391`; `list_accounts` `:753-791` — all present.
- `main.py` router-mount block `:136-139`; `App.tsx` route/`NavBar`
  regions; `client.ts` get/post/patch-but-no-delete — all as described.

**Build decisions worth flagging to triage** (adaptations, not drift):

1. **`cycle_id` filter added to `list_bets` + a `cycle_id` GET param +
   `count_bets_by_cycle`.** Beyond the literal §5.1 filter list, but
   *in direct support of named scope* — the §5.8 / §A.4 cycle-chain
   tuck-in is "reconstructed read-side by grouping on `cycle_id`", which
   needs a way to fetch a cycle's bets and to mark multi-bet cycles on the
   row. Kept store-pure and minimal. Flagged as a decision, not silent
   scope creep.
2. **The "Pending" state toggle includes `provisional`** (in-settlement-
   review), alongside `NULL` + `pending`. Provisional is non-terminal, so
   it reads as "not yet settled" for a viewing surface. ("Settled" =
   `settled_won`/`settled_lost`/`voided`; "All" = no filter.) Note: the
   §5.7 delete fence is **stricter** — it allows delete only for
   {NULL, `pending`}, never `provisional` — which is correct (settlement
   may still be touching a provisional bet).
3. **Date-range compares ISO `placed_at` lexicographically**, following
   the existing `list_unreconciled_bets` precedent (`placed_at < ?`). All
   v3 timestamps are Adelaide-local (DR-021); the only edge is a
   lexicographic compare straddling a DST offset change, which the
   existing methods already carry. No new behaviour introduced.
4. **Persona/book labels are joined from the *active* reference maps**
   (mirroring `list_accounts`). A bet on an archived account-at-book would
   show with `account_name`/`book_name` = null (the row still renders,
   with `book_or_exchange` as the fallback book label). This is a display
   nicety only — the *filter* keys are drift-free regardless. Rare at
   v3 day-0; flagged for awareness.

None of these touched the locked scope or required a `betlog_scope.md`
amendment.

---

## §7 — Session split?

**None.** The brief's sanctioned stop-point was backend-complete-and-
tested (§5.1–§5.7); that was reached with budget remaining, so the
frontend (§5.8) was carried in the same session. The full end-to-end
build is in place and green.

---

## §8 — Self-assessment + scope-discipline confirmation

**Covered:** every §5 piece built and tested; the §5.4 / §5.7 fences
enforced **server-side** (store layer) with the endpoints mapping
rejections to 409/404/422; the §5.6 structured book key and in-memory
reference join; the §5.2 P&L reuse (no recompute, no third commission
constant); the §5.8 page with the inert "Placed?" scaffold named as the
brief-3 seam.

**High confidence:** the store + derivation + endpoint logic — exercised
directly by 64 Python tests including the full fence-rejection matrix and
the back/lay/free P&L matrix. The frontend — 8 vitest tests + a clean
`tsc -b`.

**One residual the review already flagged (carried, not resolved):** the
`promo_events` delete pre-check keys on `correlation_id` against the
candidate forms of the bet's `cycle_id`. The review (§A.2 self-assessment)
noted it did not trace, against live data, exactly what form
`promo_events.correlation_id` carries in practice (that needs `.db`
access, out of scope). The fence is built conservatively (raw +
prefix-stripped + normalised-UUID candidates, plus the `foreign_keys=ON`
backstop for `ops_events`), and the un-cycled+unsettled precondition makes
a promo referent on a deletable bet near-impossible anyway — but a future
operator-Claude with `.db` access could confirm the stored form and tighten
if wanted.

**Scope discipline confirmed:** only §5 anchors touched; settlement /
placement seam byte-identical (hashes above); no `.db` access; no git
state-changing operations; the tracked-modified file list is unchanged
from session start; nothing built outside §5; the "Placed?" write path
was **not** built (scaffold only). Both suites green at close.

*End of report. Single bounded session; full build §5.1–§5.8; settlement
seam untouched.*
