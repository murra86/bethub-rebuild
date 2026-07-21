# Money-movement door — build report

**Session:** built IN-SESSION during S236 (operator elected in-session
build after locking brief v2), against
`/Users/tim/Desktop/Projects/bethub-v3`.
**Brief:** `money_movement_door_brief.md` (v2 — refined against
architecture §A.5 + W14 after operator-directed review).
**Built:** 2026-07-09, ~12:15–12:45 ACST.
**Start state:** clean tree, `main` = `16de45a` = origin/main.
**End state:** clean tree, `main` = `efdbf0d`, pushed.
**Bet-safety:** no Betfair contact; live store untouched by the build
(all tests on tmp-path fixture stores); workers as found (ON, live day).

---

## 1. Per-item outcome

### §5.1 Backend — **BUILT**
- New thin router `ui/api/routers/cash_flow.py`, wired in
  `ui/api/routers/__init__.py` + `ui/api/main.py`.
- `POST /api/v1/cash-flow/movements`: four kinds exactly
  (`deposit` / `withdrawal` / `funding` / `remittance`), `extra="forbid"`.
  FK shape enforced per kind (W14 §5.1.4): slosh kinds take
  `account_at_book_id` (router resolves the other two FKs; 404 unknown);
  float kinds take `account_id` only (404 unknown holder); the wrong FK
  for the kind is a 422. Amount > 0 and ≤ 2dp; `occurred_at` optional,
  defaults now (Adelaide), future rejected, naive input assumed
  Adelaide. One `CashFlowEventBase` through the EXISTING
  `CashFlowStoreAdapter.append_event`, `source=operator`, then commit.
  Response carries the recomputed affected balances from the two
  EXISTING derivations (book cash where applicable + holder parked
  pool) so the UI shows landed truth without a second trip.
- `GET /api/v1/cash-flow/holdings`: per-active-holder parked pool +
  `total_with_holder` via `compute_account_holder_cash_holding`, plus
  `float_seeded` (any `account_holder_balance_adjustment` with
  `day_0_opening` for that holder — computed from event presence, not
  stored).

### §5.2 Balances screen — **BUILT**
- Float line per person (italic row) with the `unseeded` chip when no
  day-0 holder opening exists; screen-level note when any float is
  unseeded ("figures are relative until the opening-balance pass").
- Person subtotal = float + books; grand row = **Whole operation**
  cash with the books/floats split named beneath it.
- **Movement card**: ＋/− on book rows (Deposit to book / Withdraw from
  book) and float lines (Top-up float (from Tim's bank) / Return float
  (to Tim's bank)); amount, optional date-time, optional note;
  **before → after preview**; plain warning when the result is
  negative; two-click (open → Record); double-submit guarded
  (disabled-while-pending). Success line quotes the SERVER's landed
  balance, not the client estimate. Invalidates the
  `['racing','log-context']` family + `['accounts']` + `['review']`.
- "Not recordable yet" note removed.

### §5.3 Registration hand-off — **BUILT**
- After a successful registration on Accounts: non-blocking, dismissible
  prompt "Record the opening deposit for <book> now?" linking to
  `/balances?deposit=<account_at_book_id>`; the Balances screen opens
  the card pre-set to Deposit for that account-at-book and clears the
  param. Registration itself never blocks.

### §5.4 Tests — **BUILT**
- Backend `tests/ui/api/test_cash_flow_movements.py` (11 tests): FK
  shape per kind asserted on the stored row; **two-location slosh**
  (deposit 325 → book +325 AND pool −325 — the live Kate pin);
  **Kate@CrownBet regression** (3 × $50 settled-lost → −150; deposit
  325 → +175 — the exact live figures); withdrawal opposite-signs;
  funding/remittance pool moves with account-only FKs; 404s; 422s
  (amount 0 / 3dp / future time / wrong-FK-for-kind / free-form kind
  incl. `profit_share`); holdings pool + seeded-flag flip after a
  scripted day-0 adjustment.
- Frontend `Balances.test.tsx` (6 tests): grouping + float lines +
  unseeded chip/note + operation total; deposit flow with preview and
  posted body; negative-withdrawal warning; float-kind card posting
  account-scoped; `?deposit=` pre-set open; read-failure honesty.
  `Accounts.test.tsx` wrapped in MemoryRouter (the prompt uses a Link).

## 2. Suites

| Suite | Before | After |
|---|---|---|
| Backend `uv run pytest -q` | 1419 | **1430** (+11) |
| Frontend `npx vitest run` | 163 | **167** (+4 net; Balances suite rewritten 2→6) |

`npm run build` (tsc -b + vite) passes.

## 3. Design calls

1. **One endpoint, `kind` field** (not four endpoints) — one validation
   spine, one client function; the kind enum is the closed vocabulary.
2. **Response returns landed balances** — the card's success line quotes
   the server's recomputed figure, so what the operator reads is ledger
   truth, not a client-side estimate.
3. **`float_seeded` derived from event presence** per request — no
   stored flag, nothing to migrate, honest by construction.
4. **Uniform floats for every active holder including Tim** — the
   ledger treats all holders alike; Tim's float is as real as Kate's
   (his bank is still excluded from the model; only the float claim is
   tracked).
5. **Negative-figure warning wording** names the real-world check
   ("check the ledger if the book/bank shows otherwise") rather than
   blocking.
6. **Naive `occurred_at` assumed Adelaide** (DR-021) rather than
   rejected — the datetime-local input sends naive strings.

## 4. Residuals (all LOW)

- **R1** — no server-side idempotency key on movements (brief §9;
  same class as S235 F3). UI-guarded; a double-tap cannot slip past
  disabled-while-pending, but a network retry theoretically could.
- **R2** — the holdings read runs one derivation per holder per
  request (5 holders today; same class as S235 F4).
- **R3** — movement edit/undo is script territory (supersession door
  unbuilt, per W14's own deferral). A typo'd amount needs a
  governance-session correction event.
- **R4** — the card's `occurred_at` sends UTC ISO from datetime-local
  (browser-local = Adelaide on the operator's Mac); fine in practice,
  worth one glance if a movement is ever recorded off-Mac.

## 5. §9 self-assessment (fence)

`git diff 16de45a..efdbf0d --name-only` touches ONLY: the new router,
router wiring (`routers/__init__.py`, `main.py` import/include lines),
the new test file, and `ui/web/**` (cashflow API client, Balances,
Accounts + styles/tests). **Zero edits** to `balance_derivation.py`,
`cash_flow_store_adapter.py`, `domain/cash_flow/__init__.py`,
`store/schema/*`, or anything in the race-page money fence. No schema
change, no migration, no new table. Excluded kinds not creatable (422
test-pinned). Git: two-commit-free single commit `efdbf0d`, pushed,
co-author trailer, green tree.

**Process note (flagged live):** `npm run build` doubles as the
frontend type gate AND the dist rebuild, so running the gate rewrote
the served dist while the app was up — third occurrence today of the
S232 rule tension. Build window ~100ms, app unaffected. Standing-rule
refinement routed to the S236 close (gate-vs-serve conflict needs a
clean answer: separate build dir for gating, or accept the swap).

## 6. Live-integration classification (S189 honesty)

**Implemented-not-live.** The running app predates the router — a
restart is required before the endpoints exist live. What each live
look must confirm:

- First real **deposit** and **withdrawal** through the card: event in
  the ledger, both balances move, Balances + money check agree with the
  book's own screen.
- First real **float top-up / return**: pool moves; operation total
  sane.
- **Registration → opening deposit** hand-off on the next new
  account-at-book.
- **Location-2 seeding pass** (operator figures; governance session,
  script) — floats are relative until then; the `unseeded` chips and
  note must disappear after.

## 7. What happens after

Per brief §10: next governance session triages this report, runs the
Location-2 seeding pass with the operator's float figures (Kate's
stated as at before the 09-Jul $325 deposit, or netted), and confirms
the live-look items above rode a real racing/banking day.

<!-- MONEY MOVEMENT DOOR COMPLETE -->
