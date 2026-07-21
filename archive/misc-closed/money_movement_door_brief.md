# Money-movement door — build brief (v2, refined against W14/§A.5)

**Status:** DRAFT v2 — pending operator lock (S236). v1 superseded in place
after review of the prior money-movement design work (operator-directed).
**Commissioned from:** Session 236 live-day findings + review of
`architecture.md` §A.5 (two-location cash model) and
`dr029/w14_cash_flow/w14_cash_flow_brief.md` (which shipped the substrate
and explicitly deferred "Operator entry UI — deposit form, withdrawal
form" to W17+ operator-facing work — **this brief is that work**).
**Executes as:** one bounded Claude Code session against
`/Users/tim/Desktop/Projects/bethub-v3`.

---

## §1 What this brief is and is not

A **surgical additive build**: the operator-entry UI + thin router for
recording money movements, writing through the EXISTING cash-flow event
adapter, plus surfacing the money model's second balance location on the
Balances screen. Single bounded Code session; surprises are findings.

NOT: any change to balance derivation or other fenced money code; not
profit-share, external payments, corrections/supersession, or bank
integration.

## §2 Why this work exists — and the model it must honour

**The two-location model (architecture.md §A.5, locked Slice 5 / S13):**
operation cash sits either **at a book** (Location 1, per
account-at-book) or **with the person as their cash float** (Location 2,
"parked pool" per account holder — the person's bank account IS the
float). Four movement types cover the operator's day-to-day:

| Movement | Event type | Effect |
|---|---|---|
| Deposit to a book | `account_at_book_deposit` | float ↓, book ↑ (internal slosh) |
| Withdraw from a book | `account_at_book_withdrawal` | book ↓, float ↑ (internal slosh) |
| Top-up a person's float from Tim's bank | `account_holder_funding` | float ↑ (bank-touching) |
| Return float to Tim's bank | `account_holder_remittance` | float ↓ (bank-touching) |

One event moves value between locations — both derivations consume it
with opposite signs (`compute_account_at_book_balance` and
`compute_account_holder_cash_holding`, both live in
`workflows/balances/v1/balance_derivation.py`; the Location-2 function is
complete but surfaced NOWHERE in the UI today).

**S236 live findings driving this:**

1. No consolidated money view existed (read side landed S236 — the
   `/balances` screen, commit `16de45a` — but it shows Location 1 only).
2. No way to record money in/out. The operator's real $325 deposit
   (Kate@CrownBet) was registered by script — live event `f2e1c5e0`,
   Location-1 balance verified −150 → +175.
3. **That same event correctly drove Kate's Location-2 float to −$325**
   — because **no account holder's float was ever seeded** (S232 seeded
   Location 1 only; the §A.5 day-0 custodian openings — ~$12.5k working
   capital — were never written). Location 2 is unseeded across the
   whole operation. Until floats are seeded AND deposits/withdrawals are
   recorded routinely, the Location-2 figures mislead.
4. **The Kate@CrownBet class:** any account-at-book registered after
   seeding derives negative as soon as stakes are logged, until its
   first deposit is recorded.

**Operator-side prerequisite (NOT Code's job — named here so the brief
is honest):** a one-off Location-2 seeding pass, S232-style — the
operator states each person's current cash float; events land as
`account_holder_balance_adjustment` / `day_0_opening` via the governance
session (Kate's figure stated as at BEFORE the 09-Jul $325 deposit, or
netted accordingly). The screen ships regardless; figures are honest
only after seeding.

## §3 Pre-reads (required, in order)

1. This brief.
2. `/Users/tim/Desktop/Projects/bethub-rebuild/architecture.md` §A.5 (the
   two-location model — read in full).
3. `/Users/tim/Desktop/Projects/bethub-v3/domain/cash_flow/__init__.py` —
   event types, payloads, FK rules per type (`_check_fk_rules`): deposit/
   withdrawal need ALL THREE FKs; funding/remittance need `account_id`
   ONLY (book fields MUST be None).
4. `/Users/tim/Desktop/Projects/bethub-v3/workflows/cash_flow/v1/cash_flow_store_adapter.py`
   — the append door (used as-is; NOT edited).
5. `/Users/tim/Desktop/Projects/bethub-v3/workflows/balances/v1/balance_derivation.py`
   — `compute_account_at_book_balance` (~389) and
   `compute_account_holder_cash_holding` (~514). READ ONLY — no edits.
6. `/Users/tim/Desktop/Projects/bethub-v3/ui/web/src/routes/Balances.tsx`
   — the S236 read-side screen this lands on.
7. `/Users/tim/Desktop/Projects/bethub-v3/ui/api/routers/promos.py` — the
   S235 B2 additive thin-router precedent.

Reference-only: `dr029/w14_cash_flow/w14_cash_flow_brief.md` (§5.1.4 FK
rules; deferred-scope list), `race_page_rework_report.md` §9.

## §4 System access

Read-write on bethub-v3 source + tests. Live store read-only at most;
all verification on tmp-path fixture stores. No Betfair contact; workers
as found; **dist rebuild only with the app confirmed down**. Adelaide
timestamps per DR-021.

## §5 Substantive scope

### §5.1 Backend — one additive endpoint, four kinds

`POST /api/v1/cash-flow/movements` in new thin router
`/Users/tim/Desktop/Projects/bethub-v3/ui/api/routers/cash_flow.py`
(wired like existing routers). Request (`extra="forbid"`):

- `kind`: `"deposit" | "withdrawal" | "funding" | "remittance"` — maps to
  the four event types above. Nothing else creatable here.
- `account_at_book_id` (required for deposit/withdrawal; MUST be absent
  for funding/remittance) — router resolves `account_id` + `book_id`.
- `account_id` (required for funding/remittance; MUST be absent for
  deposit/withdrawal — it derives from the AAB there).
- `amount`: Decimal > 0, ≤ 2dp.
- `occurred_at`: optional; default now (Adelaide); reject future.
- `reference` / `notes`: optional.

Build `CashFlowEventBase` with the matching payload class,
`source=OPERATOR`, fresh ids, append via the adapter, commit. Response
returns the event id plus the recomputed **affected balances**: for
deposit/withdrawal both the account-at-book balance AND the holder's
parked pool; for funding/remittance the parked pool. (Read-side calls to
the two existing compute functions — no new derivation.)

### §5.2 Balances screen — Location 2 + the movement door

On `/balances` (`ui/web/src/routes/Balances.tsx`):

1. **Float rows.** Each person's group gains a "cash float" line —
   `compute_account_holder_cash_holding.parked_pool` via a small additive
   read endpoint (`GET /api/v1/cash-flow/holdings` returning per-holder
   parked pool; thin router, read-only) — and the person subtotal becomes
   `total_with_holder` (float + books). Grand total = whole-operation
   cash. Until seeding, negative/zero floats render as-is (truth over
   comfort); a one-line note may say "floats unseeded — figures relative"
   IF any holder has no `day_0_opening` holder-side adjustment (derivable
   from the holdings response by a boolean flag Code adds to the read
   endpoint's items — computed from event presence, not stored).
2. **Movement card.** Book rows get **＋/−** (Deposit to book / Withdraw
   from book); person float lines get **＋/−** (Top-up float from Tim's
   bank / Return to Tim's bank). Plain-language labels as written here.
   Card shows the affected balance(s) **before → after** using the §5.1
   response; two-click (open card → confirm). A movement that takes a
   figure below zero is allowed with a plain warning ("the tool will
   show −$X — check the ledger if the book/bank shows otherwise").
   Optional date-time (defaults now), optional note. Double-submit
   guarded UI-side (disabled-while-pending + reset — Log Past Bet
   precedent; server key excluded per §9).
3. Success → invalidate the `['racing','log-context']` family +
   `['accounts']` + the holdings key. Remove the screen's "not
   recordable yet" note.

### §5.3 Registration money-in prompt

After a successful account-at-book registration on the Accounts screen:
non-blocking prompt "Record the opening deposit for <person @ book>
now?" → the §5.2 card pre-set to Deposit for that AAB. Dismissible;
registration never blocked. Kills the Kate@CrownBet class going forward.

### §5.4 Tests (fixture stores only)

- Router per kind: event lands with the FK shape §5.1.4 requires
  (deposit all-three; funding account-only with book fields None);
  response balances correct pre→post (both locations for slosh kinds);
  404 unknown AAB/account; 422 on amount ≤0 / >2dp / future occurred_at /
  wrong-FK-for-kind / free-form kind.
- **Two-location slosh assertion:** deposit 325 on a fixture → AAB cash
  +325 AND holder parked pool −325 (the live Kate case, pinned).
- **Kate@CrownBet regression:** registration + $150 settled-lost stakes,
  no opening event → −150; deposit 325 → +175.
- Holdings read endpoint: parked pool figures + unseeded flag.
- Frontend: card flows for all four kinds, before→after rendering,
  negative warning, double-submit guard, invalidation, registration
  prompt routing. Frontend gate is **`npm run build`** (S235 F1).

## §6 Sequencing

§5.1 router + tests → holdings read endpoint → §5.2 screen → §5.3
prompt → full suites → dist rebuild only if app confirmed down. Commit
per coherent step, push at end, green tree only (S227 guardrails).

## §7 Empirical verification

Suite baselines before first edit; both suites green after; the
two-location and Kate regressions red-before/green-after where they pin
new behaviour. Report states fixture-verified vs live-shape-confirmed
(the Kate figures are the captured real case).

## §8 Output spec

Single report at
`/Users/tim/Desktop/Projects/bethub-rebuild/money_movement_door_report.md`
(~200–350 lines): per-item outcomes with anchors, design calls, suite
counts, commits, §9 self-assessment (diff-verified), residuals,
live-look checklist (next real deposit / withdrawal / float top-up /
registration). Ends `<!-- MONEY MOVEMENT DOOR COMPLETE -->`.

## §9 Hard limits — NOT in scope

- **No edits to** `balance_derivation.py`, `cash_flow_store_adapter.py`,
  `domain/cash_flow/__init__.py`, `store/schema/*`, or anything in the
  race-page-rework §9 money fence. Composition only; if a line must be
  crossed, STOP and record a finding.
- No schema changes / migrations / new tables.
- **Only the four named kinds.** Excluded: `external_payment` (payee
  flows), `profit_share_distribution` (the §A.5 funding-with-profit-share
  pairing is rare and subtle — record the funding leg in-tool, route the
  profit-share event to a governance-session script, residual for a
  later door), both `*_balance_adjustment` types (correction/seeding
  territory — script + governance session), supersession-based edits of
  mis-entered movements (W14's named deferral; fix-by-script for now).
- No server-side idempotency key (S235 F3 class — UI-guarded; residual).
- No Location-2 seeding by Code (operator figures required — §2).
- No live-store writes, no Betfair contact, no worker changes, no app
  launch, no dist rebuild while the app is up.

## §10 What happens after

Next governance session: triage the report inventory-first; run the
**Location-2 seeding pass** with the operator's float figures (script,
S232-style, `day_0_opening` holder adjustments — Kate's netted for the
already-recorded $325); confirm the live-look checklist rides the next
real movements; route residuals.

## §11 Cross-references

- DR-019 (derive on read), DR-021 (Adelaide anchors), DR-022
  (vocabulary), DR-030 (thin routers).
- `architecture.md` §A.5 (two-location model; bank-touching table;
  operation-net-flow view — NOT built here, later surface).
- `dr029/w14_cash_flow/w14_cash_flow_brief.md` (substrate; §5.1.4 FK
  rules; "Operator entry UI … W17+" — this brief).
- `dr029/w12_balances/*` (the two compute functions this door reads).
- S232 `b6_seeding_pack.md` (seeding precedent, Location 1).
- S236: live deposit event `f2e1c5e0`; Balances screen `16de45a`.
- Excluded/parked: external payments door; profit-share door; composed
  transfer (book→book = withdraw+deposit, two entries); movement-edit
  via supersession; operation-net-flow view; cash-age FIFO surveillance
  (W14-deferred Burst Review surface).
