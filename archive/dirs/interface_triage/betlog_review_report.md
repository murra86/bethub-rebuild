# BetLog codebase-review report (read-only findings)

**Status:** complete, single session. Read-only review per
`interface_triage/betlog_review_brief.md` (locked S170).
**Reviewed against:** `interface_triage/betlog_scope.md` (locked S169).
**Repo (code, READ-ONLY):** `/Users/tim/Desktop/Projects/bethub-v3`.
**Report written:** 2026-06-20 ~10:47 ACST (Adelaide local, DR-021).
**Verdict (see §H):** **Buildable with adjustments.** No blocker; the
gaps are read-surface plumbing the build brief must name, not scope
contradictions.

> Findings only. No fixes, no code, no build plan. Where a gap exists
> this report names what the build brief must resolve — it does not
> resolve it. `git status` left identical to session start (no git ops,
> no edits, no `.db` access).

**Path note:** the brief's repo path (`bethub-v3`) and the report output
path (`bethub-rebuild/interface_triage/`) are two separate directories.
All v3 code anchors resolve under `bethub-v3`; the triage docs and this
report live under `bethub-rebuild`. Confirmed consistent with brief §4
(read v3) vs §8 (write to bethub-rebuild). No contradiction.

---

## §A — Bets read surface

### A.1 — The scannable row fields

Every row field in `betlog_scope.md` maps to a real column or a clean
derivation. Schema: `store/schema/bets.py:17-47` (bets),
`:49-68` (bet_legs).

| Row field | Source | Anchor |
|---|---|---|
| Selection / runner | `bet_legs.betfair_selection_name` | `store/schema/bets.py:58` |
| Side (Back/Lay) | `bets.side` (NULL = BACK) | `store/schema/bets.py:44`; domain enum `domain/bets/__init__.py:149-162` |
| Free marker | `bets.is_free_bet` | `store/schema/bets.py:23` |
| Stake @ odds | `bets.matched_stake` / `bets.matched_price` | `store/schema/bets.py:28-29` |
| State | `bets.settlement_state` (Pending/Won/Lost/Void) | `store/schema/bets.py:39`; enum `domain/bets/__init__.py:107-122` |
| Book + persona | `bets.book_or_exchange` + `bets.account_at_book_id` | `store/schema/bets.py:33-34` (persona join → §A.3) |
| P&L (settled) | **derived, not stored** | see below |

**P&L is not a stored column — and a per-bet derivation already exists
but is not exposed for reads.** `workflows/balances/v1/balance_derivation.py`
holds `_bet_cash_return(row)` (`:189-279`), a pure DR-019 derivation that
computes a bet's cash outcome from `settlement_state` + `matched_stake` +
`matched_price` + `side` + `commission` + free-bet conversion, with the
lay/back and won/lost/void branches all handled. Three caveats the build
brief must weigh:

1. It is **private** (`_`-prefixed) and lives in the balances workflow,
   not in any read-API path.
2. It computes **gross cash return**, not net P&L — e.g. a won back bet
   returns `matched_stake × matched_price` (`:271`), stake included. The
   row's "P&L" (profit) is a further `return − stake` step the endpoint
   must do (cash) or interpret per free-bet semantics.
3. It takes a raw `sqlite3.Row` (`:189`), not a `BetRow`/`BetRecord`.

The domain model carries **no** P&L computed field — `BetRecord` exposes
only `is_past_settlement_window` (`domain/bets/__init__.py:346-367`).
→ *Build brief must decide:* reuse/promote `_bet_cash_return` into a
read-side per-bet P&L derivation, or compute P&L in the endpoint. Either
way it is DR-019-derived on read; no schema change needed.

### A.2 — The tuck-in detail fields

| Detail field | Source | Anchor |
|---|---|---|
| Bet id | `bets.bet_id` (PK) | `store/schema/bets.py:19` |
| Exact placed time | `bets.placed_at` (ISO8601 Adelaide) | `store/schema/bets.py:32` |
| Commission | `bets.commission` (NULL → 8% read fallback) | `store/schema/bets.py:45` |
| Cycle chain | `bets.cycle_id` | `store/schema/bets.py:20` (see §A.4) |
| **Full promo terms** | **no home on the bet** | see below |

**Commission fallback location (confirm so the endpoint reads it
consistently):** the read-side 8% fallback constant is
`_DEFAULT_COMMISSION = Decimal("0.08")` in
`workflows/balances/v1/balance_derivation.py:153`, applied at `:235-239`.
It is **duplicated** by `DEFAULT_COMMISSION_RATE = 0.08` in
`workflows/bet_entry/v1/staking.py:55` (write-side staking). BetLog's
commission display should read the same fallback the balance derivation
uses, not re-implement a third copy. → *Build brief note:* two 8%
constants already exist; do not add a third.

**"Full promo terms" is a genuine scope gap.** The bet row's closest
promo field is `bets.strategy_tag` — a closed 4-value enum
(`safety_net` / `price_booster` / `sgm_correlated` / `synthetic_each_way`,
`domain/bets/__init__.py:73-89`), nullable for turnover bets — plus
`is_free_bet` / `free_bet_conversion_rate`. The actual promo metadata
(%, max stake, cash-vs-free-bet fine print) lives in the promo reference
tables: `promo_template.default_terms` + `promo_template.kind`
(`store/schema/promos.py:58-72`) and `promo.instance_label`
(`:74-92`). **There is no FK from `bets` to `promo`/`promo_template`.**
The only structural link from a bet to promo data is
`bets.cycle_id` → `promo_events.correlation_id` (a plain indexed column,
`store/schema/promos.py:122`, `:160`) for free-bet credit/deploy events,
and `promo_events` itself FKs only accounts/books/accounts-at-book
(`:124-129`), not promo_template. So even via `promo_events` the terms
are not cleanly reachable, and a plain (non-free-bet) strategy bet has no
promo record at all. → *Build brief must resolve:* either (a) limit the
row tag + detail to `strategy_tag` + free-bet conversion granularity, or
(b) define and build a bet→promo join (cycle_id → promo_events →
promo_template) — which does not exist today.

### A.3 — Persona name (join path + N+1 risk)

`account_at_book_id` is an id; the human-readable persona + book label
resolve through the accounts store
(`store/repositories/accounts.py`):

- `account_at_book_id` → `accounts_at_book` row → `account_id` + `book_id`
  (`get_account_at_book`, `:285-294`).
- `account_id` → `accounts.name` = **persona name**
  (`get_account`, `:163-170`).
- `book_id` → `books.name` = **book label**
  (`get_book`, `:214-221`).

That is up to **three lookups per bet** — an **N+1 risk** for a list if
done naively. There is **no single bet→persona/book JOIN method** in the
repository. Mitigant already in place: the reference data is small and
the existing `list_accounts` endpoint (`ui/api/routers/racing.py:753-791`)
already loads `list_active_accounts` + `list_active_books` + all
accounts-at-book in one shot, so the feed can pre-load a lookup map and
join in memory. → *Build brief note:* pre-load reference maps, do not
per-row query.

### A.4 — Cycle chain (read-side reconstructability)

`cycle_id` is `NOT NULL` on every bet (`store/schema/bets.py:20`) and the
POST path always populates it (`ui/api/routers/racing.py:892`,
`cycle_id = body.cycle_id or str(uuid4())`). **`cycle_id` has no table of
its own** — a cycle is purely "the set of bets sharing a `cycle_id`"
(documented `store/schema/ops.py:20-21`, DR-032). The chain
(insurance → free bet → deployed → net) is therefore reconstructable
read-side by grouping bets on `cycle_id` and ordering within the group
(e.g. by `placed_at`), computing net from the per-bet returns (§A.1). No
write needed. → *Caveat carried to §D:* because the cycle has no table,
nothing enforces chain integrity — deleting one bet silently breaks its
cycle's net.

---

## §B — Filter feasibility

The six scoped filters (`betlog_scope.md:47-54`) key on these
fields/joins:

| Filter | Keys on | Queryable today? |
|---|---|---|
| Account (persona) | `bets.account_at_book_id` → `accounts_at_book.account_id` | Indirect — needs join/IN-list |
| Account-at-book | `bets.account_at_book_id` | Direct column |
| Book (all personas) | see B.2 — two candidate keys | **Ambiguous** |
| Promo type | `bets.strategy_tag` (+ `is_free_bet`) | Only at strategy-tag granularity (see B.3) |
| Date range | `bets.placed_at` | Direct column |
| State (Pending/Settled/All) | `bets.settlement_state` | Direct column |

**B.1 — None of these are queryable through an existing repository
method.** Every existing list method filters on `match_status` or
`settlement_state` only and exposes no account/book/promo/date
parameters: `list_unreconciled_bets` (`store/repositories/bets.py:642`),
`list_unsettled_bets` (`:754`), `list_provisional_settlement_bets`
(`:795`), `list_bet_ids_for_market` (`:805`). There is **no
`list_bets(...)` with filters and no "all bets" read** at all. The fields
themselves are all present and filterable in SQL — the gap is the
**method**, not the data. (Confirmed by precedent: the balance derivation
already had to drop to raw SQL because "`SQLiteBetRecordStorage` exposes
no `list_by_account_at_book`" — `workflows/balances/v1/balance_derivation.py:24-38`,
`:125-147`.)

**B.2 — The "book" filter is ambiguous and carries free-text drift
risk.** There are two distinct "book" notions:
- `bets.book_or_exchange` — a **free-text string** written straight from
  operator/POST input (`"betfair"` or a soft-book name;
  `ui/api/routers/racing.py:482`, `:899`, `:1092`). Not a `books.book_id`.
- the `books` table reached via
  `account_at_book_id` → `accounts_at_book.book_id` → `books`
  (`store/repositories/accounts.py:285-294`, `:214-221`).

These can disagree (free-text "Bet365" vs the `books` row). The clean,
drift-free book identifier is the **`account_at_book_id` → `books.book_id`
path**, not `book_or_exchange`. → *Build brief must decide* which key the
account-health "book" lens uses; if `book_or_exchange`, flag the
free-text-drift risk. Filtering "all personas at one book" is a single
query against `accounts_at_book` (`list_active_accounts_at_book_for_book`,
`store/repositories/accounts.py:325-334`) to get the AAB-id set, then a
`bets.account_at_book_id IN (...)` — feasible, but not one existing call.

**B.3 — Promo-type filter is limited to `strategy_tag` granularity.** Per
§A.2 there is no clean bet→promo-type linkage; `strategy_tag` (4 values)
+ `is_free_bet` is the only per-bet promo dimension. True "promo type"
(insurance / bonus-winnings / price-boost — `promo_template.kind`,
`store/schema/promos.py:62-65`) is not joinable from a bet today. → *Build
brief:* scope this filter to strategy-tag (+ free/cash) unless it also
builds the promo join.

**B.4 — Not cleanly queryable as-is:** every filter (the data exists, the
method does not). The build brief needs **one new filtered list method**
(or a raw-SQL read in the endpoint following the balance-derivation
precedent) covering account / account-at-book / book / strategy-tag /
date-range / settlement-state, plus the in-memory reference-map join for
persona/book labels (§A.3). No new index is strictly required for
correctness at v3's data scale, but `placed_at` and `account_at_book_id`
are the natural candidates if the operator's book grows (see §C.3).

---

## §C — API surface

**C.1 — There is no bets-list / bets-feed GET endpoint today. Confirmed.**
The racing router's GETs are: `list_races` (`ui/api/routers/racing.py:619`),
`get_market_prices` (`:684`), `get_market_catalogue_endpoint` (`:695`),
`get_log_context` (`:707`), `list_accounts` (`:753`). No bets read route
exists on any router (`accounts.py` / `provisional.py` / `health.py` are
non-bets). The build needs the read-feed.

*Placement read (DR-030 / import-linter):* `.importlinter` defines a
`layers` contract where `ui | ops` may import `workflows`, `domain`,
`store`, `clients`, `contracts` (`.importlinter` `[importlinter:contract:layers]`).
There is **no per-router contract** — routers are not individually named
in `.importlinter`. Therefore **both options are DR-030-clean and neither
needs an `.importlinter` change:**
- **Extend `racing.py`** — already hosts the non-racing `list_accounts`
  GET (`:753`) and already imports `store.repositories.bets` (`:103-106`)
  and the balances derivation (`:107-110`), so a bets-feed adds no new
  cross-layer edge.
- **New `ui/api/routers/bets.py`** — same allowed imports; mounted with
  `prefix="/api"` alongside the others in `ui/api/main.py:136-139`.
  Cleaner separation given racing.py is already ~1,160 lines; carries no
  contract cost.

Both keep `ui → store/domain/workflows` within the layered contract;
`store-pure` (`store` imports nothing in-project) is unaffected by either
since any new repository method stays stdlib+sqlite3.

**C.2 — Response-helper / DI reuse is partial.** `_models_to_jsonable`
(`ui/api/routers/racing.py:335`) is reusable for serialising a list of
pydantic response models. `_envelope_to_http` (`:303`) is **not** a fit —
it is shaped for Betfair freshness envelopes (`fresh`/`stale`/
`unavailable`, `:314-332`); a bets feed is a plain DB read with no
staleness axis. The feed would define its own response model (as
`LogContextResponse` etc. do, `:391-407`) and depend on **`get_bet_storage`**
(`:167`, for repository reads) and/or **`get_db_connection`** (`:185`, if
it follows the balance-derivation raw-SQL precedent), plus
`get_accounts_storage` (`:176`) for the persona/book reference maps
(§A.3).

**C.3 — No server-side filtering or pagination exists for a feed.** The
repository's list methods take only status tuples + `max_results`
(`store/repositories/bets.py:150-188`); there is no offset/cursor and no
field filtering. As written, a feed would either pull via a new filtered
query or pull-all-and-filter-in-memory. v2 holds 1,900+ bets; v3 grows
from zero but the design should not assume tiny. → *Build brief:* specify
server-side filtering + a pagination shape (the existing `max_results`
ceiling pattern is the seed, but there is no offset today).

**C.4 — Edit + delete write endpoints do not exist. Confirmed.** The only
writes are `POST /v1/racing/bets` (`log_bet`, `:853`) and
`POST /v1/racing/lay` (`place_lay`, `:994`). No PATCH/PUT/DELETE on any
router. They belong on the same router as the feed (C.1). Delete
*semantics* are §D; the endpoint slots simply do not exist yet.

---

## §D — Edit / delete safety

### D.1 — What is linked downstream of a bet

| Downstream | Link to bet | FK? | Anchor |
|---|---|---|---|
| `bet_legs` | `bet_legs.bet_id → bets.bet_id` | **FK, no cascade** | `store/schema/bets.py:66` |
| `ops_events` | `ops_events.bet_id → bets.bet_id` | **FK, no cascade** | `store/schema/ops.py:74` |
| `ops_events` (cycle) | `ops_events.cycle_id` | plain column, no FK | `store/schema/ops.py:20-21,63` |
| `promo_events` (FB deploy/credit) | `deploying_bet_id` (UUID from bet id) + `correlation_id` (= cycle_id) | **no FK to bets** | `workflows/promos/v1/fb_deployment.py:59-77,143`; `store/schema/promos.py:122-129` |
| `cash_flow_events` | none direct; balance derived live off `bets` | no FK to bets | `store/schema/cash_flow.py:84-89`; `workflows/balances/v1/balance_derivation.py:382-392` |
| settlement / reconciliation | reads live `bets`/`bet_legs` rows each pass | reads only (see §E) | `workflows/bet_entry/v1/settlement.py` |
| cycle attribution | bets sharing `cycle_id` (no table) | structural only | `store/schema/ops.py:20-21` |

Lookups that already key on these: `ops_store_adapter.list_*_for_bet` /
`_for_cycle` (`workflows/ops/v1/ops_store_adapter.py:101,118`).

### D.2 — Does a hard delete orphan anything?

- **`bet_legs`:** FK with **no `ON DELETE CASCADE`**
  (`store/schema/bets.py:66`). `SQLiteBetRecordStorage._connect()` sets
  `PRAGMA foreign_keys = ON` (`store/repositories/bets.py:474`), so a
  raw `DELETE FROM bets` with legs present would **raise a FK violation**
  (RESTRICT). Legs must be deleted first inside a transaction.
- **`ops_events`:** FK to `bets` (`store/schema/ops.py:74`) — same
  RESTRICT/orphan exposure if ops rows reference the bet.
- **`promo_events`:** **not** FK-protected against bets. A hard delete
  leaves `free_bet_deployed` / credit events whose `deploying_bet_id` /
  `correlation_id` point at a now-gone bet/cycle — a **silent dangling
  reference**, and it breaks the cycle's net (the chain loses a link).
- **Cycle net:** because a cycle is just bets sharing `cycle_id` (§A.4),
  deleting any bet in a cycle silently corrupts that cycle's chain
  calculation.
- **There is no DELETE method anywhere today** (no `DELETE FROM bets`,
  no `delete_bet` in store/workflows/ui) — confirmed by search.

### D.3 — Edit: safe vs unsafe fields

Settlement reads the bet's **live** row each pass (§E), so editing
settlement-driving fields on a still-unsettled bet feeds bad data into
auto-settle:

- **Unsafe to edit (corrupts settlement/cycle):** `settlement_state`,
  `match_status`, `matched_stake`, `matched_price`, `commission`/`side`
  on an unsettled bet (settlement and the live P&L/liability derivation
  read these — `workflows/bet_entry/v1/settlement.py:356-358`,
  `workflows/balances/v1/balance_derivation.py:170-279`), the leg's
  `betfair_market_id`/`betfair_selection_id` (the settlement match keys),
  and `cycle_id` (re-parents the bet across cycles).
- **Plausibly safe (cosmetic / pre-settlement correction):**
  `strategy_tag`, and `requested_stake`/`matched_stake`/`matched_price`
  **only while still PENDING and before any settlement pass** — i.e. the
  "I typed the wrong stake" fix the operator wants. Once settled, a stake
  edit silently rewrites realised P&L.

The repository today has only **targeted** update methods
(`update_match_status` `:585`, `update_settlement_state` `:714`,
`update_reconciliation_bookkeeping` `:679`, `update_last_read_market_state`
`:827`) — there is **no arbitrary-field edit** method. The build brief
must add a scoped one.

### D.4 — Delete-safety verdict (the operator call)

**The operator's lean is the right rule, and the code supports it.**
State the rule the build brief implements:

> **Hard-delete only when the bet is BOTH unsettled (`settlement_state`
> in {NULL, `pending`}) AND un-cycled (no other bet shares its
> `cycle_id`, and no `promo_events`/`ops_events` reference it). Otherwise
> block delete and require edit instead.** The delete must run as a
> transaction that removes `bet_legs` first then `bets` (no cascade
> exists), with `PRAGMA foreign_keys = ON` so an unexpected `ops_events`
> referent surfaces as an error rather than an orphan.

Rationale from the code: the only clean-delete case is a bet with no
downstream rows and no cycle siblings — exactly "unsettled AND
un-cycled". Anything settled has live P&L/balance contribution
(`balance_derivation.py:382-392`); anything cycled or promo/ops-linked
orphans a reference (§D.2). A soft-delete (marked-removed) is the safer
default for the *blocked* cases but the operator's stated preference is
edit-not-delete there, which the rule honours. → *Build brief decides*
hard vs soft for the un-cycled-unsettled case; both are structurally safe
there.

---

## §E — Settlement seam (do-not-touch boundary)

> `settlement.py` / `reconciliation.py` / `orchestrator.py` were **read
> only** for this section. Not modified.

**E.1 — Exact read interface settlement uses off a bet.** Settlement
matches a market by reading the **first leg's canonical Betfair ids** off
the in-memory `BetRecord`:

- `_resolve_settlement_for_bet` (`workflows/bet_entry/v1/settlement.py:319`):
  `leg = record.legs[0]` (`:356`),
  `market_id = leg.betfair_market_id` (`:357`),
  `selection_id = leg.betfair_selection_id` (`:358`).
- `_resolve_provisional_for_bet` (`:494`): same reads at `:553-555`.
- `record.settlement_state` gating (`:1182-1185`).
- Candidate selection reads via `storage.list_unsettled_bets(...)`
  (`:731`, `:954`) and `storage.read_bet_record(bet_id)` (`:1177`,
  `:1222`).

So BetLog's read/edit/delete must not disturb, for any bet settlement may
still touch: `bet_legs.betfair_market_id` / `betfair_selection_id` (leg
0), and `bets.settlement_state`. Entry points are
`run_settlement_pass` (`:698`), `run_provisional_resolution_pass`
(`:914`), and `apply_manual_operator_resolution` (`:1128`).

**E.2 — Is there a write path from a view/edit action that could reach
settlement? No — and a clean seam exists.** Settlement is invoked only by
the three pass/resolution entry points above (scheduled passes +
burst-review's manual resolution). It mutates state exclusively through
repository methods — `storage.update_settlement_state` (`:753`, `:976`,
`:1193`), `update_reconciliation_bookkeeping` (`:868`),
`update_last_read_market_state` (`:895`). **Repository writes do not call
settlement** — `SQLiteBetRecordStorage`'s methods write columns directly
(`store/repositories/bets.py:482-853`) and import nothing from
`workflows` (store-pure, `.importlinter`). Therefore BetLog edit/delete,
built as repository-level writes (a new scoped edit method + a delete),
**never reach the settlement engine**. The one indirect coupling is data,
not call-path: settlement reads the *live* row on its next pass, which is
exactly why §D.3 fences settlement-driving fields on unsettled bets.

**E.3 — "placed?" confirm forward pointer (brief 3 — naming only).** The
eventual confirm *write* lands in the **promo / free-bet credit-in write
zone**: `workflows/promos/v1/` — the free-bet deployment writer
`record_free_bet_deployment` (`workflows/promos/v1/fb_deployment.py:85`,
already wired into `log_bet` at `ui/api/routers/racing.py:931-938`) and
the promo store adapter writing `promo_events` (credit/deploy event
types, `store/schema/promos.py:99-108`). BetLog scaffolds the button; the
write is brief 3. **Named only — not designed, not built.**

---

## §F — Frontend scaffold

The frontend is **well past the "early Vite scaffold" the brief assumed**
— it is a routed, typed, react-query app with an established component +
CSS-module + per-domain-API pattern. BetLog has a clear place to mount and
clear conventions to follow; it adds little new infrastructure.

**F.1 — Routing and nav both exist.** `ui/web/src/App.tsx` uses
`react-router-dom` `BrowserRouter`/`Routes`/`Route`/`Link` (`:2`,
`:45-54`) with a `NavBar` (`:22-40`) and four route pages
(`/racing`, `/provisional`, `/accounts`, `/health`). BetLog adds: one
`<Route path="/betlog">` (`App.tsx:47-53`), one `<Link>` in `NavBar`
(`:22-40`), and one page component under `src/routes/` (the existing pages
are `src/routes/{Racing,Provisional,Accounts,Health}.tsx`). No routing
infrastructure to build.

**F.2 — Data-fetching pattern is established: react-query over typed
fetch wrappers.** `App.tsx` wraps the app in `QueryClientProvider`
(`:1`, `:44`, global defaults `staleTime:0, retry:false` `:10-20`). Routes
use `useQuery`/`useMutation` (`routes/Health.tsx:17`, `routes/Racing.tsx:72`,
`routes/Provisional.tsx:43`) over typed wrappers in `src/api/client.ts`:
`apiGet` (`:72`), `apiPost` (`:93`), `apiPatch` (`:97`) — throwing
`ApiError` (`:11-28`). Per-domain API modules exist (`src/api/accounts.ts`,
`racing.ts`, `provisional.ts`) plus generated `src/api/types.ts`. BetLog
follows: add `src/api/bets.ts` + `useQuery` in the page. **Gap:** there is
**no `apiDelete` wrapper** (only get/post/patch) — the build adds one for
the delete action.

**F.3 — Component / styling conventions.** CSS modules throughout
(`*.module.css` beside each component/route, e.g. `App.module.css`,
`routes/Racing.module.css`, `components/LogBetPanel.module.css`).
Components live in `src/components/`, route pages in `src/routes/`. A new
BetLog page conforms by adding `routes/BetLog.tsx` + `BetLog.module.css`
and any row/detail sub-components under `src/components/`.

**F.4 — vitest is wired and runnable.** Configured in
`ui/web/vite.config.ts` (`environment: 'jsdom'`, `setupFiles:
['./src/test/setup.ts']`); there is no separate `vitest.config.*`. Test
command is `npm test` → `vitest run` (`ui/web/package.json` scripts).
Existing route/component tests (`*.test.tsx`) are the pattern to match.
Baseline in §G.

---

## §G — Test baselines

Captured at session start, before any inspection, against
`/Users/tim/Desktop/Projects/bethub-v3`. Both green.

**G.1 — Python (`uv run pytest -q`, per DR-031):**

```
1028 passed, 4 warnings in 6.55s
```

→ **1028 passed, 0 failed, 0 skipped.** This is the gate number the build
brief measures against ("1028 → 1028, no regressions").

**G.2 — Frontend (`npm test` → `vitest run`):**

```
Test Files  14 passed (14)
     Tests  91 passed (91)
```

→ **91 passed across 14 files, 0 failed, 0 skipped.**

**G.3 — Pre-existing noise (so a post-build diff is not misread):**

- pytest: 4 `DeprecationWarning`s only — `HTTP_422_UNPROCESSABLE_ENTITY`
  is deprecated (`ui/api/routers/__init__.py:8`, `accounts.py:357/363`,
  and one in anyio). **Warnings, not failures.** No skipped or xfailed
  tests.
- vitest: two benign Node warnings (`--localstorage-file provided
  without a valid path`). Not test failures.

No already-failing or skipped tests in either suite — a clean baseline.

---

## §H — Overall read

**Verdict: BetLog is buildable as scoped, with a defined set of
adjustments. No item in `betlog_scope.md` is contradicted by the code;
the gaps are missing read-side plumbing the build brief must specify, not
scope rewrites.** The two load-bearing risks the operator should know are
both already half-solved in the codebase (a per-bet P&L derivation
exists; the frontend is fully routed), and the one true scope gap
(promo terms) is exactly the one the brief anticipated.

**Adjustments the build brief must resolve (none blocking):**

1. **No bets read surface / feed (A.1, B.1–B.4, C.1–C.3).** The
   repository has no "list/filter bets" method and no all-bets read, and
   no GET endpoint exists. Build adds one filtered read (new repository
   method or endpoint-level raw SQL per the balance-derivation precedent)
   covering account / account-at-book / book / strategy-tag / date-range /
   settlement-state, plus pagination, plus the in-memory persona/book
   reference-map join (N+1 avoidance).

2. **P&L is derived, not stored — promote the existing derivation (A.1).**
   `_bet_cash_return` (`balance_derivation.py:189-279`) is the seed but is
   private, returns gross return (not net P&L), and takes a `sqlite3.Row`.
   Build decides reuse-vs-recompute; read the 8% commission fallback from
   the single existing constant (`:153`), not a new copy.

3. **Promo terms gap (A.2, B.3).** No bet→promo FK; only `strategy_tag` +
   `is_free_bet` are per-bet. Build either limits promo display/filter to
   strategy-tag granularity, or builds the `cycle_id → promo_events →
   promo_template` join (does not exist today). If this touches the
   locked scope's "full promo terms" line, `betlog_scope.md` updates
   first (per brief §10).

4. **"Book" filter ambiguity (B.2).** `bets.book_or_exchange` is
   free-text and can drift from the `books` table; the clean key is
   `account_at_book_id → books.book_id`. Build picks one and names the
   drift risk if it chooses `book_or_exchange`.

5. **Edit/delete write paths do not exist (C.4, D).** Build adds a scoped
   edit method (safe set: `strategy_tag`, and stake/price only while
   PENDING — never settlement-driving fields on unsettled bets) and a
   delete that follows the §D.4 rule (hard-delete only when unsettled AND
   un-cycled, transactional legs-then-bet, FK on). No cascade exists; a
   blocked-case delete must be refused, not forced.

6. **Frontend additions are small (F).** One route + one nav link + one
   page + `src/api/bets.ts`, following react-query + CSS-module
   conventions; add an `apiDelete` wrapper (the only missing primitive).

**What is already safe / confirmed and needs no scope change:**
the scannable-row fields all map (A.1); persona/book join path exists
(A.3); cycle chain is read-side reconstructable (A.4); settlement seam is
clean — BetLog edit/delete via repository writes never reach the
settlement engine (E.2), seam pinned at `settlement.py:356-358` (E.1);
the credit-in forward pointer has a named home (E.3); both test baselines
are green (G).

---

## Self-assessment

**Covered:** every question in §A–§G with file + line/region citations;
the §D.4 delete-safety rule stated; the §E.1 settlement read seam pinned
to exact functions + lines; both §G baselines captured with pre-existing
noise noted; the §H buildable verdict in plain language with the
adjustment list. Single bounded session — comfortably fit; no need to
stop-and-surface.

**Fully answered with high confidence:** A, C, D, E, F, G — read directly
from source, including the settlement engine (read-only) and the full
downstream-reference map.

**Answered with one residual unknown:** §B / §A.2 promo linkage. I
confirmed *structurally* that no bet→promo FK exists and that the only
link is `cycle_id → promo_events.correlation_id`. I did **not** trace
whether, in practice, `promo_events` payloads reliably carry enough to
reach a `promo_template` row for a given bet (that would need `.db` data,
which is out of scope per brief §4). The build brief should treat the
promo-terms join as "to be designed," not "known-present."

**Scope discipline:** no file edited, nothing built, no git operations,
no `.db` access, settlement engine read-only. `git status` unchanged from
session start. Only write this session is this report.

**Length note:** ~470 lines — within the 300–550 band. The tables and the
per-area adjustment naming earn the length; no padding.

*End of report. Read-only review; findings only; builds nothing.*
