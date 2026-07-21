# BetLog build brief (locked S171)

**Type:** build brief — net-new feature, read-WRITE on the v3
repo code. Single bounded Code session.
**Commissions:** Claude Code, out-of-session.
**Builds against:** `interface_triage/betlog_scope.md` (locked
S169, amended S171) + `interface_triage/betlog_review_report.md`
(the read-only review, S171). Every code anchor below is lifted
from that review.
**Repo (code, READ-WRITE — named anchors only):**
`/Users/tim/Desktop/Projects/bethub-v3`.
**Output:** `interface_triage/betlog_build_report.md` (in
`bethub-rebuild`, not the code repo).

---

## §1 — What this brief is and is not

**Is:** a build brief. Code builds BetLog — the bet-viewing
surface v3 has no equivalent of today — as a read + edit/delete
feature. One filtered bets feed, one read endpoint, a scoped
edit path, a hard-delete path, and the frontend page that
consumes them. The insurance "placed?" confirm is **scaffolded
only** (button present, no write path) — its write lands in a
later brief.

**Is not:** a settlement console, a manual "add bet from
scratch" flow, or a promo-join build. Those are out of scope
(§9). Code builds what §5 names and nothing adjacent.

**Single bounded session.** If the full build does not fit one
Code session, the sanctioned stop-point is **backend-complete-
and-tested** (§5.1–§5.7 done, all tests green, report written);
the frontend (§5.8) becomes a clean follow-on brief. Do
not push past budget to half-finish the frontend — a coherent
backend with a green suite beats a broken end-to-end. State the
split in the report if it happens; it is a finding, not a
failure.

**Surprises become findings.** If an anchor below has drifted
(line moved, method renamed), Code adapts to the live code and
notes it — the review was read-only and the tree is in flight.
If a build choice turns out unsafe (e.g. a "safe-to-edit" field
proves settlement-driving), Code stops at that piece, reports
it, and continues with the rest. Remediation of anything
surprising routes to the next operator-Claude triage, not to
Code chasing it mid-session.

## §2 — Why this work exists

The operator is cutting v3 over for live betting and has **no
way to see his bets** today — a settled-lost insurance qualifier
vanishes into the data with nowhere it surfaces. BetLog is the
viewing surface, and it is the home the free-bet "placed?"
confirm needs before the credit-in work (a later brief) can
land. The S171 review confirmed the locked scope is buildable
against the real v3 code, with the read-side plumbing this brief
specifies. No committed cutover date — ready beats rushed.

## §3 — Pre-reads

**Required (read before building, confirm understanding before
the first edit):**

1. `interface_triage/betlog_scope.md` — the locked scope (S169,
   amended S171). The contract for *what* BetLog is.
2. `interface_triage/betlog_review_report.md` — the read-only
   review. The map of *where* everything is (every §-anchor
   below traces to it).

**Reference-only (consult as needed, not required cover-to-
cover):**

- `store/schema/bets.py` — bets + bet_legs schema.
- `workflows/balances/v1/balance_derivation.py` — the existing
  P&L derivation to reuse (§5.2).
- `ui/api/routers/racing.py` — endpoint + DI patterns to follow.
- `workflows/bet_entry/v1/settlement.py` — the do-not-touch
  seam (§8). Read to know the boundary, not to change it.

## §4 — System access

- **v3 repo code** (`/Users/tim/Desktop/Projects/bethub-v3`):
  **READ-WRITE**, named anchors in §5 only.
- **Databases:** none. This build needs schema + code only; it
  does **not** read or write any `.db`. (The feed reads bets at
  *runtime* via the repository; the build itself touches no live
  data.)
- **git:** dirty-tree discipline (§8). No git state-changing ops.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021
  (timestamp anchoring, Adelaide local time) for every time
  reference in the report.

## §5 — Substantive scope (the build)

Backend first (§5.1–§5.7), then frontend (§5.8). All
anchors are from the review report; verify each against the live
file before editing (the tree is in flight).

### §5.1 — Filtered bets read (repository method)

**The gap:** there is no "list/filter bets" method and no
all-bets read in the repository. Every existing list method
filters on status only (`list_unsettled_bets`
`store/repositories/bets.py:754`, etc.) with no account / book /
promo / date parameters.

**Build:** add a single filtered read method to
`SQLiteBetRecordStorage` (`store/repositories/bets.py`) — e.g.
`list_bets(...)` — that filters on, all optional and
combinable:

- `account_at_book_id` (direct column).
- account (persona) — resolves to the set of that persona's
  `account_at_book_id`s, then `IN (...)` (see §5.6 for the join
  source).
- book — the **structured** key: `account_at_book_id` →
  `accounts_at_book.book_id` → the AAB-id set →
  `bets.account_at_book_id IN (...)`. **Not** `book_or_exchange`
  (see §5.6, operator-locked S171).
- `strategy_tag` (+ `is_free_bet`) — the only per-bet promo
  dimension (§5.5).
- date range on `bets.placed_at`.
- `settlement_state` (Pending / settled / all).

Plus **pagination** — newest-first on `placed_at`, with an
offset/limit shape (none exists today; the `max_results` ceiling
at `:150-188` is the seed pattern, but add offset). Keep the
method **store-pure** (stdlib + sqlite3 only — no `workflows`
import), consistent with the layer contract.

**No new index is required** for correctness at v3's data scale;
`placed_at` and `account_at_book_id` are the natural candidates
if the operator's book grows — note in the report, do not add
unless trivially clean.

### §5.2 — Per-bet P&L (reuse the existing derivation)

**The gap:** P&L is not stored. A per-bet derivation already
exists but is private and not read-exposed:
`_bet_cash_return(row)` in
`workflows/balances/v1/balance_derivation.py:189-279` — a pure
DR-019 (derived-state-on-read) calc handling lay/back,
won/lost/void, commission, and free-bet conversion.

**Build:** **reuse it, do not recompute.** Promote
`_bet_cash_return` into a read-side per-bet derivation usable by
the feed (un-private it, or expose a thin public wrapper in the
balances workflow that the feed calls). Three things to handle,
all named by the review:

1. It returns **gross cash return**, not net P&L — a won back
   bet returns `matched_stake × matched_price` (stake included,
   `:271`). The feed's "P&L" (profit) is the further
   `return − stake` step; do it at the read layer, interpreting
   free-bet semantics (free bets convert at winnings-only).
2. It takes a raw `sqlite3.Row` (`:189`), not a `BetRecord` —
   feed the row shape it expects, or adapt the wrapper.
3. Read the **8% commission fallback from the single existing
   constant** `_DEFAULT_COMMISSION` (`:153`). Do **not** add a
   third copy — two already exist (`:153` read-side and
   `staking.py:55` write-side).

P&L is derived on read; **no schema change, no stored column.**

### §5.3 — Bets-feed GET endpoint

**The gap:** no bets-list / bets-feed GET exists on any router
(confirmed §C.1).

**Build:** a **new router** `ui/api/routers/bets.py`, mounted
`prefix="/api"` alongside the others in `ui/api/main.py:136-139`.
(Placement call — see §6. DR-030 / import-linter clean: routers
aren't individually named in `.importlinter`; `ui → store /
domain / workflows` stays within the layered contract.)

- A GET that takes the §5.1 filters + pagination as query params
  and returns a typed response model (define its own, as
  `LogContextResponse` does at `racing.py:391-407`; the Betfair
  `_envelope_to_http` freshness helper at `:303` is **not** a
  fit — a bets feed has no staleness axis).
- Serialise via the reusable `_models_to_jsonable`
  (`racing.py:335`).
- Depends on `get_bet_storage` (`racing.py:167`) for the read
  and `get_accounts_storage` (`:176`) for the reference maps
  (§5.6). Reuse the existing DI providers; do not add new ones.
- Server-side filtering + pagination (do not pull-all-and-
  filter-in-memory; §C.3).

### §5.4 — Edit write path (scoped)

**The gap:** no arbitrary-field edit method exists — only
targeted updates (`update_settlement_state` `:714`, etc.). No
PATCH endpoint.

**Build:** a scoped edit method on the repository + a PATCH on
the bets router. **The safe-edit set is fenced** (§D.3 of the
review; settlement reads the live row each pass, so editing
settlement-driving fields on an unsettled bet feeds bad data
into auto-settle):

- **Editable:** `strategy_tag` (cosmetic, always safe); and
  `requested_stake` / `matched_stake` / `matched_price` **only
  while the bet is still PENDING and pre-settlement** — the "I
  typed the wrong stake" fix.
- **Never editable** (reject at the method, not just the UI):
  `settlement_state`, `match_status`, `commission`, `side`, the
  leg's `betfair_market_id` / `betfair_selection_id` (settlement
  match keys), and `cycle_id` (re-parents the bet across
  cycles). On a settled bet, **stake/price are also locked** —
  editing them silently rewrites realised P&L.

The method enforces the fence server-side; the frontend mirrors
it (disabled fields), but the server is the source of truth.

### §5.5 — Promo display (strategy-tag only — locked)

No build beyond the tag. Per the S171 scope amendment (Option
A): the row shows `strategy_tag` (Safety Net / Price Booster /
SGM / Synthetic Each-Way, the closed enum at
`domain/bets/__init__.py:73-89`) as the short tag + the "Free"
marker (`is_free_bet`); the tuck-in shows the free-bet
conversion rate (`free_bet_conversion_rate`). **No promo fine
print, no bet→promo join** — there is no FK from `bets` to
`promo` / `promo_template` and a plain bet has no promo record.
Do not build the join.

### §5.6 — Persona / book reference join + the Book key

**The N+1 risk (§A.3):** resolving persona + book labels per bet
is up to three lookups (`account_at_book_id` → AAB row →
`account_id` → `accounts.name`; `book_id` → `books.name`), and
there is no single bet→persona/book JOIN method.

**Build:** **pre-load reference maps once per feed request, join
in memory** — mirror `list_accounts` (`racing.py:753-791`),
which already loads `list_active_accounts` + `list_active_books`
+ all accounts-at-book in one shot. Do **not** per-row query.

**The Book key (operator-locked S171):** the account-health
"book" lens keys on the **structured** path
`account_at_book_id` → `accounts_at_book.book_id` → `books`, via
`list_active_accounts_at_book_for_book`
(`store/repositories/accounts.py:325-334`) to get the AAB-id
set. **Not** `bets.book_or_exchange` — that is free-text written
from POST input (`racing.py:899`) and drifts from the `books`
table. The structured key is drift-free; an account-health lens
that silently misses bets is worse than useless.

### §5.7 — Delete write path (hard, fenced)

**The gap:** no DELETE method or endpoint exists anywhere
(confirmed §D.2).

**Build:** a hard-delete method on the repository + a DELETE on
the bets router, implementing the **operator-locked rule (S171,
"go hard"):**

> **Hard-delete only when the bet is BOTH unsettled
> (`settlement_state` in {NULL, `pending`}) AND un-cycled** — no
> other bet shares its `cycle_id`, and no `promo_events` /
> `ops_events` reference it. Otherwise **block the delete** and
> require edit instead (return a clear "blocked: settled or
> cycled" error, not a silent no-op).

Mechanics (from §D.2):

- Run as a **transaction**: delete `bet_legs` first, then
  `bets` — there is **no `ON DELETE CASCADE`**
  (`store/schema/bets.py:66`), and `PRAGMA foreign_keys = ON` is
  set (`store/repositories/bets.py:474`), so a raw
  `DELETE FROM bets` with legs present raises a FK violation.
- Keep `foreign_keys = ON` so an **unexpected** `ops_events`
  referent surfaces as an error rather than a silent orphan.
- Hard delete = the row is gone, no trace. This is only ever
  reachable for a pending, standalone, mistake bet — nothing
  downstream to orphan.

### §5.8 — Frontend page (the BetLog surface)

The frontend is well past a bare scaffold (§F) — it is a routed,
typed, react-query app. BetLog adds little infrastructure:

- **Route + nav:** one `<Route path="/betlog">` in
  `ui/web/src/App.tsx:47-53`, one `<Link>` in the `NavBar`
  (`:22-40`), one page `src/routes/BetLog.tsx` +
  `BetLog.module.css` (mirror the existing
  `routes/{Racing,Provisional,Accounts,Health}.tsx` + CSS-module
  pattern).
- **Data layer:** add `src/api/bets.ts` (mirror
  `src/api/accounts.ts` etc.), `useQuery` over the typed `apiGet`
  wrapper (`src/api/client.ts:72`). **Add an `apiDelete`
  wrapper** to `client.ts` — the only missing primitive (get /
  post / patch exist; delete does not). Use `apiPatch` (`:97`)
  for edit.
- **The page (per the locked scope):** flat list, **newest-
  first**, no race grouping. Filters across the top (account /
  account-at-book / book / promo-type-as-strategy-tag / date /
  state toggle Pending·Settled·All). Scannable row (selection,
  side, Free marker, stake @ odds, state, P&L once settled, book
  + persona). Tuck-in on open (bet id, exact timestamp,
  commission, strategy tag + conversion rate, **cycle chain**
  insurance → free bet → deployed → net, reconstructed read-side
  by grouping on `cycle_id` and ordering by `placed_at`, §A.4).
  Edit + Delete actions on the bet, fenced per §5.4 / §5.7.
- **"Placed?" confirm — SCAFFOLD ONLY.** Render the button in
  the row/tuck-in where the credit-in confirm will live. **No
  write path** — it is inert this brief (the write is the
  free-bet credit-in brief, brief 3, landing in
  `workflows/promos/v1/`, §E.3). Wire nothing to it; name it in
  the report as the brief-3 seam.
- **vitest:** add tests matching the existing `*.test.tsx`
  pattern (§G). `npm test` → `vitest run`.

## §6 — Sequencing within session

Dependency order (a different order is fine if Code sees one
cleaner, but this is the natural build path):

1. **§5.1 filtered read** + **§5.6 reference join** — the data
   spine everything else reads through. Build + unit-test first.
2. **§5.2 P&L derivation** — reuse/promote, then the net-P&L
   read step. Test against known won/lost/void/free cases.
3. **§5.3 GET endpoint** — wires §5.1 + §5.2 + §5.6 into the
   feed. Endpoint test.
4. **§5.4 edit** + **§5.7 delete** — the write paths, with the
   server-side fences. Test the fence rejections explicitly
   (settled-bet edit blocked; cycled/settled delete blocked).
5. **§5.8 frontend** — consumes the now-built feed/edit/delete.
   Page + `apiDelete` + vitest.

Backend (1–4) is the coherent stop-point if budget runs short
(§1). Promo display (§5.5) is not a step — it is just the tag
already on the row, no build.

## §7 — Empirical verification (baselines)

Both suites are **green at start** (captured in the review, §G).
Capture both pre and post so the report shows what moved:

- **Python:** `uv run pytest -q` (per DR-031 — the v3 repo is a
  `uv` project; bare `python3 -m pytest` fails at collection).
  Baseline **1028 passed, 0 failed, 0 skipped**. Post-build:
  **1028 + new tests, 0 regressions.** The 4 pre-existing
  `DeprecationWarning`s (HTTP_422) are noise, not failures — do
  not "fix" them (out of scope); just don't add to them.
- **Frontend:** `npm test` → `vitest run`. Baseline **91 passed
  across 14 files**. Post-build: **91 + new, 0 regressions.**
  The two benign Node `--localstorage-file` warnings are
  pre-existing noise.

Every new method/endpoint/page gets test coverage matching the
existing pattern. A red suite at close is a stop-and-report
condition, not something to push past.

## §8 — Settlement seam (DO NOT TOUCH)

This is the bet-safety boundary. The live-proven settlement +
placement paths must end the session byte-identical.

**Do not modify:** `workflows/bet_entry/v1/settlement.py`,
`reconciliation.py`, or `orchestrator.py`. Read-only if read at
all.

**The exact seam (§E.1):** settlement matches a market off the
**first leg's canonical Betfair ids** —
`leg = record.legs[0]`, `market_id = leg.betfair_market_id`,
`selection_id = leg.betfair_selection_id`
(`settlement.py:356-358`) — plus `bets.settlement_state`
gating. BetLog must never disturb those fields for any bet
settlement may still touch. That is exactly **why §5.4 fences**
the leg ids, `settlement_state`, and stake/price-on-unsettled.

**Why BetLog edit/delete is structurally safe (§E.2):**
settlement is invoked only by its three pass/resolution entry
points and mutates state only through repository methods.
**Repository writes do not call settlement** — the store layer
imports nothing from `workflows` (store-pure). So BetLog's
edit/delete, built as repository-level writes, **never reach the
settlement engine**. The only coupling is data, not call-path:
settlement reads the *live* row on its next pass — which is the
whole reason the §5.4 fence exists. Build the fence and the seam
holds.

**Placement path** (`placement.py` and the live-proven lay path)
is likewise untouched — BetLog does not place bets.

## §9 — Output spec

**Single file:** `interface_triage/betlog_build_report.md` (in
`bethub-rebuild`, **not** the code repo). Adelaide-local
timestamps (DR-021).

**Structure:**

- Per-piece build summary (§5.1–§5.8): what was built, the files
  + line regions touched, the key decisions made in the build.
- Test results: pre + post counts for both suites, the new
  tests added, any deviation from the 1028 / 91 baselines
  explained.
- The settlement-seam confirmation: `git diff` proof that
  `settlement.py` / `reconciliation.py` / `orchestrator.py` /
  `placement.py` are untouched.
- Any anchor drift found vs the review (lines moved, methods
  renamed) and how Code adapted.
- If the session split at the backend stop-point (§1): what is
  done, what the frontend follow-on needs.
- Self-assessment + scope-discipline confirmation.

**Length:** ~300–550 lines (range, not a hard line; the build
detail earns length, padding does not).

**Does NOT contain:** the next brief; the free-bet credit-in
design; promo-join work; any cutover scoping.

## §10 — Hard limits (NOT in scope)

- **No settlement / placement touch** — §8. The do-not-touch
  boundary.
- **No `.db` access** — schema + code only; the build reads no
  live data (§4).
- **No "placed?" write path** — scaffold the button inert; the
  write is brief 3 (free-bet credit-in).
- **No manual-settle console** — v3 auto-settles + routes to
  burst-review; BetLog is a viewing surface (scope).
- **No manual "Add Bet from scratch"** — that is the after-the-
  fact manual-entry brief (brief 2), a separate Code session.
- **No promo-join build** — strategy-tag granularity only
  (§5.5, locked S171).
- **No schema changes** — all read-side derivation + new methods
  + new endpoint + frontend. No new columns, no new tables, no
  migration.
- **No new index** unless trivially clean (§5.1) — note the
  candidates, don't add speculatively.
- **No deprecation-warning cleanup** — the pre-existing HTTP_422
  warnings stay (§7).

### Dirty-tree discipline

The v3 tree is **in flight** (streaming / placement modified;
operational store + domain + `ui/web/` untracked). Therefore:

- **No** `git add`, `commit`, `stash`, `restore`,
  `checkout` (file-targeted), `reset`.
- Read working-tree state at session start.
- Edit only the §5 anchors.
- After each edit to a **tracked** file, `git diff <file>` to
  confirm only intended changes.
- `ui/web/` is **untracked** — there is no per-file git diff to
  rely on; verify the frontend by **grep + vitest**, not by
  diff.
- At close, `git status` to confirm the tracked dirty-file list
  is unchanged (only intended new/modified files added).

## §11 — What happens after Code's session

The next operator-Claude session reads
`betlog_build_report.md`, triages it (settlement-seam proof
first, then the per-piece build + test deltas), and routes:

- Clean → BetLog is live; next is operator live-validation, then
  the **manual-entry brief (brief 2)** — which opens with the
  capture.db retention check (read-only, VPS via SSH tunnel,
  `start_process` Python, never copy; DR-027/028 re-read
  trigger).
- A surgical fix flagged → a small follow-on brief, same pattern
  as the racing-page review → fixes arc.
- Split at the backend stop-point → a frontend follow-on brief.

Code does **not** write the next brief. Brief 3 (free-bet
credit-in) lands the "placed?" write path into the scaffold this
brief leaves.

## §12 — Cross-references

- **Scope:** `interface_triage/betlog_scope.md` (locked S169,
  amended S171).
- **Review (the anchor source):**
  `interface_triage/betlog_review_report.md` (S171).
- **DRs:** DR-019 (derived state on read — P&L), DR-021
  (Adelaide timestamps), DR-022 (account / account-at-book /
  book vocab — the filters), DR-030 (module boundaries — the
  router placement), DR-031 (`uv run pytest` test gate), DR-032
  (Betfair canonical — the leg ids + cycle axis). DR-027/028
  named **out of scope** here (BetLog is pure operational store,
  no capture.db).
- **Excluded (parking-lot / other briefs):** manual-entry
  (brief 2), free-bet credit-in (brief 3), launcher brief.

*End of brief. Locked S171. Single bounded Code session;
read-write on named v3 anchors only; settlement seam untouched.*
