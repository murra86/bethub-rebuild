# W12 report — Read-side derivations + reference data seed (HALT at alignment)

**Session anchor (open):** 2026-05-14 05:55 ACST
**Session anchor (close):** 2026-05-14 06:03 ACST
**Brief:** `dr029/w12_balances/w12_balances_brief.md`
**Executor:** Claude Code (single bounded session)
**Ship status:** **HALTED at §6.1 alignment check.** No substantive
edits applied. Pre-baselines preserved (753 tests passing, 5/5
contracts kept, mypy clean). All findings surfaced below for
operator-Claude triage.

---

## §1 — Pre-amble

W12 did not ship code this session. The seven §6.1 alignment
checks (plus operator-amplified judgement extension) surfaced
**multiple substantive divergences between brief-spec and shipped
substrate** — enough that the brief's algorithm for the balance
derivation, the journey-state derivation, and the warning-state
derivation cannot be implemented as written against the shipped
W4/W6/W6.5/W11/W13/W14 code.

The halt rule at §6.1 explicitly forbids Code from unilaterally
amending specs, contracts, or DRs to resolve findings. Per that
rule, work stopped after the alignment pass and before §5.1's
slug-flip edit (the earliest substantive step in §6.2 build
order, immediately downstream of the alignment gate).

Findings span:

- **Two adapter-surface naming divergences** (Finding-B; small
  fix at the brief level — methods exist but with different names
  than the brief named).
- **Bet-record substrate gaps** (Finding-C; the bet record carries
  `is_free_bet: bool` but no `promo_id` / `promo_template_id`
  linkage, and the bet storage class exposes no
  `list_by_account_at_book` method). The journey-state derivation
  in §5.8 reads "bet records linked to the promo … via the
  bet-record read surface filtered by linked promo template" —
  this filter shape does not exist.
- **Cash flow event type mismatch with the brief's balance
  algorithm** (Finding-H). The brief's §5.3 algorithm references
  `bet_won` / `bet_lost` cash flow events that carry the bet's
  cash return; the W14 substrate has eight specific event types,
  none of which is bet-settlement-derived. Architecture.md §A.5
  defines the canonical formula differently — cash returns come
  from the bet row (`matched_stake × matched_price`) per §A.6,
  not from cash flow events.
- **`AccountCareWarningClearedPayload` references the prior raise
  event ID, not `warning_type_id`** (Finding-J). The brief's
  warning-state algorithm in §5.7 counts "raised events for the
  warning_type_id at the account_at_book" vs "cleared events for
  the same warning_type_id." The cleared payload does not carry
  `warning_type_id`; it carries `cleared_warning_event_id`. The
  derivation has to walk via the raise event reference, not via
  a warning-type tally.
- **`FreeBetCreditSource` enum values are `TRIGGERED` and
  `FREEBIE`** (Finding-K), not the brief's `INSURANCE_TRIGGER` /
  `BONUS_WINNINGS_TRIGGER` / `GOODWILL` set.
- **`FreeBetCreditedPayload` expiry field is `face_value_expiry`**
  (Finding-L), not the brief's `expires_at`.
- **`AccountCareWarningRaisedPayload.severity_at_raise` is
  mandatory** (Finding-M), not nullable; the brief's algorithm
  "if severity_at_raise is null, fall back to catalogue" cannot
  execute.
- **`warning_catalogue.warning_type_id` is typed `UUID` in
  shipped W13** (Finding-N; the slug-flip §5.1 step zero in the
  brief addresses this; flagged here for visibility because
  Finding-J / Finding-K combine to question whether the slug-flip
  is the right edit shape).
- **No `account_holders` table in W11 substrate** (Finding-O).
  Architecture.md §A.5 defines Location 2 as "per
  account_holder"; W11 ships `accounts`/`books`/`accounts_at_book`
  only. The brief's §5.4 "per-custodian holding by book_id"
  reading interprets custodian-as-bookmaker, which is plausible
  but should be operator-Claude-confirmed.
- **No `EXTERNAL_PAYMENT_EVENT_TYPES` constant or
  `is_external_payment` helper** in `domain.cash_flow`
  (Finding-F per §6.1 ALIGNMENT-CHECK-F; the brief named this
  as a potential finding).
- **`_ensure_adelaide_local` duplicated** across
  `domain.cash_flow` and `domain.promos` (Finding-E; functionally
  identical, prose differs).

Dirty-tree discipline held throughout: no `git add`, no
`git commit`, no `git stash`. 37 pre-existing dirty entries at
session open; same 37 at session close. HEAD unchanged
(`2329604a...`).

---

## §2 — Pre-build alignment findings

The seven §6.1 alignment checks plus operator-amplified judgement
extension. Each finding is annotated with brief-spec ↔
shipped-reality details so operator-Claude has the empirical basis
for triage.

### §2.1 — ALIGNMENT-CHECK-A — W14.1 adapter shape: **PASS**

`workflows/cash_flow/v1/cash_flow_store_adapter.py` (396 lines)
ships per W14.1 spec.

- Class `CashFlowStoreAdapter` exists with
  `__init__(self, conn: sqlite3.Connection)`. ✓
- Public event-read methods: `list_by_account_at_book`,
  `list_by_account`, `list_by_book`, `list_by_event_type`,
  `list_by_correlation_id`, `latest_non_superseded_by_scope`,
  `walk_supersession_chain`. ✓
- Payee surface: `list_payees`, `get_payee`, `update_payee`,
  `create_payee`. ✓

W12's balance derivations would call against this surface
unchanged.

### §2.2 — ALIGNMENT-CHECK-B — W13 promo adapter shape: **PARTIAL PASS / FINDING**

`workflows/promos/v1/promo_store_adapter.py` (785 lines) ships.
Class `PromoStoreAdapter` exists with `__init__(self, conn:
sqlite3.Connection)`. ✓

Event-read methods match brief exactly. ✓

**Reference-data method names differ from brief.**

| Brief named               | Adapter actually exposes      |
|---------------------------|--------------------------------|
| `list_promo_templates`    | `list_templates`               |
| `get_promo_template`      | `get_template`                 |
| `list_warning_catalogue_entries` | `list_warning_types`    |
| `get_warning_catalogue_entry` | `get_warning_type`         |
| `create_promo_template`   | `create_template`              |
| `create_warning_catalogue_entry` | `create_warning_type`   |

`list_promos` and `get_promo` match. `update_template`,
`update_promo`, `update_warning_type` also exist on the adapter.

**Trip risk:** brief §5.2 names `adapter.create_promo_template`
and `adapter.create_warning_catalogue_entry` literally; the seed
script would fail at first call. Brief §6.1 ALIGNMENT-CHECK-B
named only the read methods literally (not the write methods),
so this finding was inevitable. Cheap to resolve at brief level
(rename in brief) or at code level (use actual names).

**Classification:** (a) brief-spec deviation. Trivial mechanical
update once operator-Claude picks a canonical surface name. No
substrate change.

### §2.3 — ALIGNMENT-CHECK-C — bet record read surface: **MULTIPLE FINDINGS**

The bet-record substrate is the largest source of
brief ↔ reality divergence at W12 alignment.

**File anchors:**

- `domain/bets/__init__.py` — `BetRecord` Pydantic model + the
  `SettlementState` / `MatchStatus` / `EntryPath` / `LegRole` /
  `BetSideTag` / `Construction` / `HedgeSoftBookStakeKind` /
  `PriceSource` / `StrategyTag` enums.
- `store/repositories/bets.py` — `BetRecordStorage` Protocol,
  `InMemoryBetRecordStorage`, `SQLiteBetRecordStorage` with the
  W6/W6.5/W9 surface.
- `store/schema/bets.py` — DDL for `bets` and `bet_legs` tables.
- `workflows/bet_entry/v1/bet_store_adapter.py` — exposes
  `to_rows` / `from_rows` / `to_provisional_payload` helpers; not
  a Pydantic-typed adapter surface in the W14.1 / W13 sense.

**Brief expectation vs shipped reality:**

- **Brief §5.3:** "Bet records for the account-at-book — placed
  bets and settled bets. Read via whatever the v3-shipped bet-
  record read surface exposes (confirm at §6.1 alignment check;
  if no adapter exists yet, fall back to the W4/W6 repository
  surface directly)."
- **Reality:** No method exists on `SQLiteBetRecordStorage` for
  listing bets by `account_at_book_id`. Methods present:
  `write_bet_record`, `update_match_status`, `read_bet_record`
  (by bet_id), `list_unreconciled_bets`, `list_unsettled_bets`,
  `list_provisional_settlement_bets`, `list_bet_ids_for_market`,
  several update-* methods.
- **Workaround Code thinks fits:** drop below the storage layer
  to raw SQL via the shared `sqlite3.Connection` —
  `SELECT * FROM bets WHERE account_at_book_id = ?`. This is the
  brief's named fallback in §3.1 item 6
  ("`store/repositories/cash_flow.py` and
  `store/repositories/promos.py` — reference for SQL-level read
  shape if a derivation needs to drop below the adapter for
  performance"). For a list-by-account-at-book query, performance
  is not at issue — the issue is the method genuinely doesn't
  exist.

**Brief expectation vs shipped reality on bet ↔ promo linkage:**

- **Brief §5.8:** "Bet records linked to the promo — read via the
  bet-record read surface filtered by linked promo template
  (confirm at §6.1 alignment for the actual filter shape)."
- **Reality:** No `promo_id` field, no `promo_template_id` field,
  no `triggering_promo_id` field on `BetRecord`. The only
  promo-side flag on the bet record is `is_free_bet: bool` plus
  the optional `free_bet_conversion_rate: float | None`. The
  bet ↔ promo linkage exists only in the *reverse* direction:
  `FreeBetCreditedPayload.triggering_bet_id` and
  `FreeBetDeployedPayload.deploying_bet_id` link a promo event
  back to a bet. There is no forward `bet → promo` field; the
  derivation needs to query the promo event log for events whose
  payload references the bet_id.

**Brief expectation vs shipped reality on stake fields:**

- **Brief §5.3 algorithm:** "Minus pending bet stakes — for each
  bet record whose settlement state is 'placed and not yet
  settled,' the stake amount is committed cash, subtracted from
  the balance."
- **Reality:** `BetRecord` has `requested_stake`, `matched_stake`,
  `unmatched_stake` (Decimal each), `is_free_bet: bool`. There is
  no `cash_stake_amount` field as architecture.md §A.5 references.
  The implicit derivation: `cash_stake = matched_stake if not
  is_free_bet else Decimal("0")`. Free-bet stakes should not be
  subtracted from cash balance per architecture.md §A.5.

**Brief expectation vs shipped reality on identifier types:**

- **Reality:** `BetRecord.bet_id` is `str`, not `UUID`.
  `BetRecord.account_at_book_id` is `str`, not `UUID`. Cross-
  derivation type plumbing needs `str(uuid)` conversion at the
  derivation boundary if the function signatures take `UUID`.

**Classification:** (b) spec-implied substrate concern. The
brief's algorithm shape assumes a Pydantic-typed bet-record read
surface with promo linkage; the substrate has none of those
shapes. Operator-Claude routes to either: (i) revise W12 brief to
work with the shipped substrate shape (raw-SQL list query;
promo→bet linkage only); (ii) commission an interim W12-prep
workstream that adds the missing bet-record read surface; (iii)
defer journey-state derivation to a later workstream when the
bet-record substrate has the necessary linkage.

### §2.4 — ALIGNMENT-CHECK-D — `lint-imports` cross-workflow contract: **PASS**

`.importlinter` (rebuild root, not `pyproject.toml`) at lines
61–67 declares the `workflows-independent` contract as an
**`independence` type with explicit named modules**:

```
[importlinter:contract:workflows-independent]
name = workflows cannot import workflows
type = independence
modules =
    workflows.bet_entry
    workflows.burst_review
```

The contract enforces: `workflows.bet_entry` cannot import
`workflows.burst_review` and vice versa. It does **not** block
`workflows.balances.v1.*` from importing
`workflows.promos.v1.promo_derivations` (neither module is in the
named set). The §5.3 balance derivation's cross-workflow import
of the §5.6 FB inventory function is permitted by the current
contract as-written.

**Operator note:** the contract's *name* ("workflows cannot import
workflows") is broader than its *type*'s actual enforcement
(narrow independence between two named modules). This is
intentional per DR-030 + S124 amendment locking cross-workflow
imports for derivation chains, but the contract name reads
misleadingly. Not a finding requiring action; flagged for
visibility.

### §2.5 — ALIGNMENT-CHECK-E — `_ensure_adelaide_local` validator location: **MINOR FINDING**

Two definitions exist:

- `domain/cash_flow/__init__.py:159` — for cash flow event tz
  validation.
- `domain/promos/__init__.py:190` — for promo event tz
  validation.

`diff` of the two function bodies: prose / error-message strings
differ (cash flow vs promo wording); the validation logic is
**byte-for-byte identical** in structure (timezone-aware check;
ACST/ACDT offset check; identical accept set). Two valid reads:

- (i) duplication is intentional — each domain owns its own
  validator without cross-domain coupling per DR-030 spirit.
- (ii) duplication is incidental — a shared
  `domain/_time.py` (or similar) would deduplicate cleanly.

The brief §6.1 ALIGNMENT-CHECK-E said: "If the helper exists in
two locations (one per domain), pick whichever is canonical —
confirm at this check whether both are identical. If they differ,
surface as ALIGNMENT-FINDING-E for operator-Claude resolution."

They are identical in logic; the prose differs. Code's pick: each
new W12 derivation module imports the validator from whichever
domain it primarily reads from (`workflows.balances` imports from
`domain.cash_flow`; `workflows.promos.v1.promo_derivations`
imports from `domain.promos`). No deduplication recommended at
this stage — duplication is the cheaper read for the operator
and respects DR-030 module-boundary spirit. Operator-Claude can
override.

**Classification:** (c) pre-existing codebase shape; minor.

### §2.6 — ALIGNMENT-CHECK-F — `is_external_payment` classification: **FINDING**

No `EXTERNAL_PAYMENT_EVENT_TYPES` constant exists in
`domain/cash_flow/__init__.py`. No `is_external_payment` helper
method on the enum or as a free function.

The brief named this finding explicitly in §6.1 ALIGNMENT-CHECK-F:
"If no such constant exists, identify the event types directly via
inspection and surface as ALIGNMENT-FINDING-F so operator-Claude
can decide whether a constant should be added (one-line edit in
`domain/cash_flow`, but DR-030-respectful) or W12 lists them
inline."

The eight shipped `CashFlowEventType` values:

| Value | Bank-touching (per architecture.md §A.5)? |
|---|---|
| `ACCOUNT_HOLDER_FUNDING` | Yes — outflow (Tim → custodian) |
| `ACCOUNT_AT_BOOK_DEPOSIT` | No — internal (custodian → book) |
| `ACCOUNT_AT_BOOK_WITHDRAWAL` | No — internal (book → custodian) |
| `ACCOUNT_HOLDER_REMITTANCE` | Yes — inflow (custodian → Tim) |
| `ACCOUNT_AT_BOOK_BALANCE_ADJUSTMENT` | No — model-side correction |
| `ACCOUNT_HOLDER_BALANCE_ADJUSTMENT` | No — model-side correction |
| `EXTERNAL_PAYMENT` | Yes — outflow (Tim → payee) |
| `PROFIT_SHARE_DISTRIBUTION` | **Conditional** on `funding_source` payload field |

"Bank-touching" is the architecture-canonical concept for the
operation-net-flow derivation, not "external payment." Brief §5.5
uses "external payment" terminology; architecture §A.5 uses
"bank-touching." The conditional case (profit-share with
`funding_source = 'tim_direct'` is bank-touching;
`funding_source = 'account_holder_cash_holding'` is not) means a
classification helper must read the event payload, not just the
event type.

**Classification:** (b) spec-implied substrate concern.
Operator-Claude triage: add a `BANK_TOUCHING_EVENT_TYPES`
classification constant (plus a profit-share-funding-source
checker) to `domain.cash_flow`, OR W12 derivation lists them
inline. The conditional case is the load-bearing detail.

### §2.7 — ALIGNMENT-CHECK-G — `WarningSeverity` and `FreeBetCreditSource` enum locations: **PARTIAL FINDING**

**`WarningSeverity`** at `domain/promos/__init__.py:120` —
three-tier scheme per DR-015 (`RED`, `AMBER`, `YELLOW`).
Importable. Matches brief expectation. ✓

**`FreeBetCreditSource`** at `domain/promos/__init__.py:137` —
enum values are `TRIGGERED` and `FREEBIE` (binary). Importable.
**Does not match brief.**

Brief §6.1 ALIGNMENT-CHECK-G stated:
"`FreeBetCreditSource` distinguishes `INSURANCE_TRIGGER` /
`BONUS_WINNINGS_TRIGGER` / `GOODWILL` / etc. per the W13 shipped
enums."

The W13 shipped enum has only two values: `TRIGGERED` (any
upstream-bet-triggered credit, regardless of whether it's
insurance-shaped or bonus-winnings-shaped) and `FREEBIE` (no
upstream bet). The richer enum the brief assumed does not exist.

Brief §7.3 scenarios reference the rich enum values:

- Scenario CASH-4: `credit_source = INSURANCE_TRIGGER` (does not
  exist; shipped value would be `TRIGGERED`).
- Scenario CASH-5: `credit_source = GOODWILL` (does not exist;
  shipped value would be `FREEBIE`).

Routing the rich semantics through the binary enum requires
additional context — e.g., reading the `triggering_promo_instance_id`
and following back to the template's `kind` (`INSURANCE` /
`BONUS_WINNINGS` / `PRICE_BOOST` / `EW_CASHBACK` / `OTHER`) to
derive whether the trigger was an insurance trigger or a
bonus-winnings trigger.

**Classification:** (b) spec-implied substrate concern.
Operator-Claude triage: either (i) expand `FreeBetCreditSource`
to the richer enum (DR-030-compatible additive edit), (ii) revise
brief to use the binary `TRIGGERED`/`FREEBIE` enum and read
"insurance vs bonus-winnings" via template-kind lookup, or (iii)
treat the rich enum semantics as informational labels at the
W17 UI layer with W12 producing only the binary shipped enum.

### §2.8 — ALIGNMENT-FINDING-H — Balance algorithm vs cash flow event types: **LOAD-BEARING FINDING**

The §5.3 balance derivation algorithm assumes bet settlement
returns appear as cash flow events:

> Plus settled bet returns — for each settled bet, the return
> amount credits back to the cash balance via the cash flow event
> log (the bet's settlement event writes a `bet_won` or `bet_lost`
> cash flow event with the return amount). So in practice,
> settled returns are ALREADY in the cash flow events sum;
> they don't get added separately.

**The W14 substrate ships no `bet_won` / `bet_lost` event type.**
The eight `CashFlowEventType` values listed in §2.6 above are
exhaustive; none represents a bet settlement return.

**Architecture.md §A.5 canonical formula (the load-bearing
source):**

```
at_book_balance =
  + Sum(account_at_book_deposit) inflows
  − Sum(account_at_book_withdrawal) outflows
  ± Sum(account_at_book_balance_adjustment) signed adjustments
  − Sum(bets.cash_stake_amount) cash stakes placed
  + Sum(per-bet computed cash_returned per §A.6) cash returns
  + Sum(promo_cash_credited where status='finalised')
```

And §A.6: "Cash returned is computed on read per DR-019. No
`cash_returned_to_book` column is stored on the `bets` row. Cash
return derives from `matched_stake × matched_price × dead_heat /
removed_runner handling` against the bet's settlement state."

So cash returns are computed FROM THE BET ROW (matched_stake ×
matched_price), not from cash flow events. The brief's algorithm
double-counts settled returns conceptually — but in practice
under-counts them because no cash flow events carry them in the
first place.

**Operational impact at the brief's scenarios:**

- **Scenario CASH-2:** brief expects "Cash flow event: bet
  return credit $150 linked to the bet record." Such an event
  cannot be written today (no event type for it). The expected
  `cash_balance = $300.00` cannot be reached via the
  brief-as-written algorithm.
- **Scenario CASH-3:** brief assumes no cash flow event on loss
  (correct in shipped substrate), expected `cash_balance =
  $150.00` ($200 deposit minus $50 stake). The shipped algorithm
  would compute: deposit $200 minus matched_stake $50 = $150,
  matching. CASH-3 works.
- **Scenario CASH-4 step 4:** Betfair cash flow event for lay
  liability release + commission winnings credit — these would
  need cash flow events, but the shipped event types don't have
  this shape. The closest match is
  `account_at_book_balance_adjustment` — but the architecture
  treats that as a model-side correction event, not an automatic
  hedge-settlement event.

**Classification:** (b) spec-implied substrate concern.
Load-bearing. Operator-Claude triage options:

- (i) Revise the W12 brief's balance algorithm to follow
  architecture.md §A.5 verbatim: read cash flow events for the
  per-account-at-book scope, plus read the bets table for stake
  subtraction and computed cash return addition, plus read
  `promo_cash_credited` from `promo_events`.
- (ii) Commission a bet-settlement-event workstream (`bets_events`
  or similar) before W12 ships, so the brief's "events are the
  source of truth" framing holds end-to-end. This is a
  substantial architectural shift; not lightly taken.
- (iii) Continue with derived-cash-return-from-bet-row but adjust
  brief scenarios CASH-2 / CASH-4 to reflect the actual event
  flow shape. Brief assertions on cash flow event presence get
  removed; bet row stake/return becomes the authoritative source.

### §2.9 — ALIGNMENT-FINDING-I — Operation net flow scope: window vs since-day-0

Brief §5.5 specifies: "For a given Adelaide-local window
(`start_at`, `end_at`), returns the operator's total inflow,
outflow, and net cash movement."

Architecture.md §A.5 specifies:
"`operation_net_flow = + sum(account_holder_remittance) − sum(account_holder_funding) − sum(external_payment) − sum(profit_share_distribution where funding_source = 'tim_direct')`"
plus: "Cumulative net impact on Tim's bank since day 0".

The architecture defines the formula as cumulative since day 0;
the brief defines it as window-bounded. Window-bounded is more
flexible operationally (the operator can ask "how did I go last
month?"); since-day-0 is the architecture-canonical formula
(answer to "since day 0, how much net cash has the operation
pulled from / returned to my bank?").

**Classification:** (a) brief-spec deviation from architecture.
Operator-Claude triage: window-based is a reasonable extension;
no architecture amendment needed (architecture defines the
unbounded total; the windowed form is a specialisation). Brief
proceeds as-written if operator confirms.

### §2.10 — ALIGNMENT-FINDING-J — Warning state algorithm vs cleared payload shape

Brief §5.7 algorithm:

> For each unique `warning_type_id` referenced in either the
> raised or cleared events at this account_at_book:
>
> 1. Count raised events for the warning_type at the
>    account_at_book.
> 2. Count cleared events for the same warning_type.
> 3. If raised count > cleared count: warning is active.

**`AccountCareWarningClearedPayload` (shipped W13) has no
`warning_type_id` field.** Its payload (line 528–543):

```python
class AccountCareWarningClearedPayload(_PayloadBase):
    event_type_payload: Literal["accountcare_warning_cleared"] = ...
    cleared_warning_event_id: UUID          # ← links to specific raise
    clearance_reason: str
    clearance_context: dict[str, object] | None = None
```

The clear references the *specific raise event ID* it clears, not
the warning type. Adapter-side validation enforces that the
referenced raise event is of type `accountcare_warning_raised`
and that scoping (account_at_book_id) matches.

**Correct algorithm shape against shipped payload:**

For each raise event at the account_at_book:

1. Check whether any subsequent `accountcare_warning_cleared`
   event has `cleared_warning_event_id == this raise event's
   event_id`.
2. If no — the warning is active (this raise has not been
   cleared).
3. If yes — the warning is not active (this raise has been
   cleared by the named clear event).
4. Group active raises by `warning_type_id` (the field on the
   raise payload, not the clear payload). Most-recent active
   raise per warning_type is the "current" raise.

The semantics are equivalent (clear cancels raise) but the
algorithm walks differently — the clear is a 1-to-1 reference to
a specific raise, not a typed counter against the raise count.

**Classification:** (a) brief-spec deviation. Algorithm needs
rewriting to follow the raise-event-id linkage shape; numeric
output identical assuming each clear targets a unique raise
(which the W13 adapter enforces).

### §2.11 — ALIGNMENT-FINDING-K — `severity_at_raise` mandatory not nullable

Brief §5.7 algorithm:

> `severity`: the `severity_at_raise` field on the most-recent
> raise event (which lets a specific raise override the baseline
> severity). If `severity_at_raise` is null on that raise, fall
> back to the catalogue's baseline `severity`.

**`AccountCareWarningRaisedPayload.severity_at_raise` is typed
`WarningSeverity` (not `WarningSeverity | None`).** Field is
mandatory at construction; no null path exists.

This means the algorithm's catalogue-baseline fallback never
fires. Every raise carries an explicit severity. The catalogue
severity becomes informational only for the warning-type display
label; the operationally-binding severity is always the raise
event's `severity_at_raise`.

**Classification:** (a) brief-spec deviation. Algorithm
simplifies: always use `severity_at_raise`. Catalogue severity
is the warning-type *default* at observation/seed time but the
operator writes a specific raise severity per event.

### §2.12 — ALIGNMENT-FINDING-L — FB credit expiry field naming

Brief §5.6 algorithm and Pydantic output model reference
`expires_at` for the FB credit expiry timestamp.

`FreeBetCreditedPayload.face_value_expiry: datetime | None` (W13
shipped, line 316). No `expires_at` field. The semantics match
(both express the FB's expiration timestamp); the name differs.

Per the seed_data.md spec's framing of "face value of the free
bet is captured at the `free_bet_credited` event (event-level
`amount` field)" — the shipped naming `face_value_expiry`
expresses both that it's the face-value's expiry (after which the
FB cannot be deployed) and ties naming to `face_value` as the
in-architecture concept.

Brief §5.6's `AvailableFreeBet.expires_at: datetime | None` would
need renaming to `face_value_expiry` (or aliased) for parity with
the substrate. Cosmetic.

**Classification:** (a) brief-spec deviation. Trivial rename.

### §2.13 — ALIGNMENT-FINDING-M — No `account_holders` substrate

Architecture.md §A.5 defines Location 2 as "Cash holdings with
custodians" derived "per `account_holder`":

> + Sum(`account_holder_funding` where account_holder_id = X)
> ...
> − Sum(`account_holder_remittance` where account_holder_id = X)

W11 ships three tables: `accounts`, `books`, `accounts_at_book`.
No `account_holders` table. The `accounts.account_id` is the
operator's "persona" (Tim self, Tim's partner, friend, etc. — per
DR-022 vocabulary).

Cash flow events carry `account_id` (the persona who holds the
account), `book_id` (the bookmaker), and `account_at_book_id`
(the persona-at-bookmaker pairing). The architecture's
`account_holder_id` mapping is ambiguous given the W11 substrate:

- (i) "account_holder" = `accounts.account_id` (persona) —
  Location 2 then becomes "cash held in the operator's accounts
  belonging to persona X across all bookmakers where persona X
  holds accounts." Plausible per DR-022.
- (ii) "account_holder" = bookmaker (the bookmaker is the
  *custodian* of the cash from Tim's bank-perspective view) —
  Location 2 then becomes "cash held at bookmaker X across all
  operator personas at that bookmaker." This matches the brief's
  §5.4 framing of "for each `book_id`, returns the total cash
  position aggregated across all of the operator's accounts at
  that book."

The architecture's prose uses "account_holder" but the formula
fields like `account_holder_funding` reference an event type, not
a foreign-key column. Cash flow events carry `account_id` and
`book_id` (and `account_at_book_id`); aggregating by either gives
either (i) or (ii).

**Code's recommended read:** the brief's §5.4 "per-custodian
holding by book_id" is operationally what the operator wants
(answer to "how much cash do I have at Sportsbet across all my
accounts there"). This is reading (ii) of the architecture
prose. Wording the architecture more explicitly would clear up
the ambiguity but isn't strictly necessary if the operator
confirms reading (ii).

**Classification:** (a) brief-spec deviation vs architecture
prose; operationally aligned with operator framing. Light fix to
architecture wording would clarify; W12 brief proceeds as-written
if operator confirms reading (ii).

### §2.14 — ALIGNMENT-FINDING-N — `warning_type_id` slug-flip in dependent payloads

Brief §5.1 step zero flips three payload fields from `UUID` to
`str`:

- `WarningCatalogueEntry.warning_type_id`
- `AccountCareWarningRaisedPayload.warning_type_id`
- `AccountCareWarningClearedPayload.warning_type_id`

**The third field does not exist on the shipped W13 payload** —
see Finding-J. `AccountCareWarningClearedPayload` carries
`cleared_warning_event_id` (UUID, references the raise event)
plus `clearance_reason` and `clearance_context`, not a
`warning_type_id`.

So the slug-flip needs to flip **two** type annotations, not
three:

- `WarningCatalogueEntry.warning_type_id: UUID` → `str`.
- `AccountCareWarningRaisedPayload.warning_type_id: UUID` → `str`.

Plus the W13 test fixtures that seed warning catalogue entries
with `uuid.uuid4()` — swap to slug strings.

Plus the W13 adapter (`promo_store_adapter.py`) — verify
`_require_warning_type(...)` and the
`accountcare_warning_raised` payload-reference validation path
to confirm the `warning_type_id` formatting/casting is consistent
with the str type.

**Classification:** (a) brief-spec deviation. The shipped payload
doesn't carry the third UUID field the brief lists. Operator-
Claude triage: revise the brief's §5.1 step-zero anchor list to
two type annotations, not three.

### §2.15 — ALIGNMENT-FINDING-O — Warning catalogue ID type vs slug-flip ordering

This pairs with Finding-N. Two reads of the slug-flip's purpose:

- (i) `warning_type_id` is the catalogue's PK (per-row identifier)
  and slug values like `rapid_promo_turnover` are the canonical
  PKs. Operator-typeable. Memory-friendly. The catalogue's `label`
  column then carries the human-readable display name.
- (ii) `warning_type_id` is a UUID PK (per W13 shipped) and the
  slug values are aliases / external identifiers stored
  somewhere else.

Brief §5.1 names reading (i): "warning identifiers are slugs
(operator-typeable, human-readable strings like
`rapid_promo_turnover`), not UUIDs." Brief §5.2 follows
through: "Warning slugs from the seed spec (`rapid_promo_turnover`,
`large_deposit_burst`, ...) used verbatim as the `warning_type_id`
values."

The seed_data.md spec confirms reading (i): "Slug IDs per Session
131 call ... `warning_type_id` flips from `UUID` to `str` in
`domain/promos/__init__.py` as W12 brief step zero before any of
these can be written via the typed Pydantic path."

Reading (i) is locked. Finding-N just clarifies that the field
exists on two payloads (catalogue + raise), not three.

**Classification:** (a) brief clarification per Finding-N; not
substrate-touching.

### §2.16 — Summary table

| # | Finding | Classification | Halts substantive edits? |
|---|---|---|---|
| A | W14.1 adapter shape | PASS | No |
| B | Promo adapter method names | (a) | Yes — brief naming needs updating |
| C | Bet record substrate gaps | (b) | Yes — load-bearing for §5.3 / §5.4 / §5.8 |
| D | lint-imports contract | PASS | No |
| E | `_ensure_adelaide_local` duplicated | (c) | No |
| F | No external-payment classification helper | (b) | Yes — minor; brief offered inline-listing fallback |
| G | `FreeBetCreditSource` enum values | (b) | Yes — affects §5.6 inventory derivation |
| H | Balance algorithm vs cash flow event types | (b) | Yes — load-bearing |
| I | Net flow window vs since-day-0 | (a) | No — orthogonal to substrate |
| J | Warning state algorithm vs cleared payload shape | (a) | Yes — algorithm rewrite |
| K | `severity_at_raise` mandatory not nullable | (a) | No — algorithm simplifies |
| L | FB credit expiry field naming | (a) | No — cosmetic |
| M | No `account_holders` substrate | (a) | No — operator confirms reading (ii) |
| N | `warning_type_id` not on cleared payload | (a) | Yes — affects §5.1 step zero |
| O | Warning catalogue slug-flip semantics | (a) | No — clarification only |

**Halting findings (substantive):** B, C, F, G, H, J, N. Eight findings
are halting at varying severity; Finding-C and Finding-H are
load-bearing — neither admits a unilateral Code resolution.

---

## §3 — What Code did

Sequence executed:

1. **Session-open timestamp.** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-14 05:55 ACST`.
2. **Pre-baselines per §7.1.**
   - **Git working-tree snapshot.** 37 short-status entries
     pre-existing. HEAD `2329604aa80b34937a24644ea2eb18477749be85`.
     Confirms substantive pre-existing dirty tree per §9.7 (W11 /
     W13 / W14 substrate lives as untracked entries).
   - **Pytest pre-baseline.** Initial run with system `python3`
     (3.11.9) returned 19 collection errors due to missing httpx
     / starlette dependencies in that interpreter. Switched to
     the project venv at
     `.venv/bin/python` (3.12.7) which has the full dependency
     set: **`pytest tests/ --tb=no -q` → 753 passed in 3.40s.**
     This matches the brief's expected pre-baseline of "753 tests
     passing" exactly.
   - **lint-imports pre-baseline.** `.venv/bin/lint-imports` →
     **5 contracts kept / 0 broken.** Matches brief expectation.
   - **mypy pre-baseline** on touched promo modules
     (`domain/promos`, `workflows/promos`,
     `store/repositories/promos.py`): **Success, 5 source
     files.** Matches brief expectation.
   - **File-existence pre-baseline.** `workflows/balances/`,
     `workflows/promos/v1/promo_derivations.py`,
     `scripts/`, `tests/workflows/balances/`,
     `tests/scripts/` all confirmed absent (expected pre-W12).
3. **§6.1 alignment check.** Read end-to-end:
   - `workflows/cash_flow/v1/cash_flow_store_adapter.py` —
     ALIGNMENT-CHECK-A passed.
   - `workflows/promos/v1/promo_store_adapter.py` (lines 1–200
     and method signatures via grep through 460) — ALIGNMENT-
     CHECK-B partial; method naming finding-B surfaced.
   - `domain/bets/__init__.py` (lines 107–340),
     `store/repositories/bets.py` (class structure),
     `store/schema/bets.py` (full DDL) — ALIGNMENT-CHECK-C
     surfaced multiple substantive findings (no `promo_id` link;
     no list-by-account-at-book method; account_at_book_id is
     str not UUID; bet_id is str not UUID; stake fields are
     `requested_stake`/`matched_stake`/`unmatched_stake` with
     `is_free_bet: bool` flag, not the `cash_stake_amount` field
     architecture.md names).
   - `.importlinter` (rebuild root config file) — ALIGNMENT-
     CHECK-D passed; `independence` contract narrowly scoped to
     `bet_entry`/`burst_review` and permits other cross-workflow
     imports.
   - `domain/cash_flow/__init__.py` line 159 and
     `domain/promos/__init__.py` line 190 — ALIGNMENT-CHECK-E
     duplicated but functionally identical.
   - `domain/cash_flow/__init__.py` event-type enum (line 69)
     and grep for `EXTERNAL_PAYMENT_EVENT_TYPES` — ALIGNMENT-
     CHECK-F finding (no constant exists).
   - `domain/promos/__init__.py` lines 120 (`WarningSeverity`)
     and 137 (`FreeBetCreditSource`) — ALIGNMENT-CHECK-G
     partial; `FreeBetCreditSource` values don't match brief.
   - **Operator-amplified judgement extension** (per S130
     precedent): Code surfaced findings H–O above. Anchors read
     during extension:
     - `domain/promos/__init__.py` payloads (lines 239–544) for
       Findings J / K / L / N.
     - `architecture.md` §A.5 / §A.6 / §A.9 (lines 334–620) for
       Finding-H balance algorithm and Finding-M
       account_holders.
     - `store/schema/accounts.py` (lines 36–80) for Finding-M
       no-account_holders-table verification.
4. **Halt point reached.** Findings above flagged. Per §6.1
   halting rule and the operator's commission, no substantive
   edits applied. Tasks #3–#13 in the session task list (slug-
   flip through full regression) closed unstarted.
5. **Session-close timestamp.** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M:%S %Z"`
   → `2026-05-14 06:03:40 ACST`.

**Session length:** ~9 minutes wall-clock. Short by design —
findings surfaced quickly because the substrate is well-shipped
and the brief's algorithm + payload assumptions diverged
materially from it.

**Sequencing deviations:** none from the §6.2 build order; the
halt fired at step 2 (alignment check). All later steps deferred
to the next session.

---

## §4 — What landed where

**Zero new files.** Zero edited files. Zero moved files.

`store/__init__.py` unchanged. `domain/promos/__init__.py`
unchanged. `workflows/promos/v1/promo_store_adapter.py`
unchanged. No W11 / W13 / W14 substrate file touched.

The W12 expected deliverable list per brief §1.1 (~12-14 new
files plus 2 edited) is unchanged from pre-session state.

---

## §5 — Test results

Pre-baseline: **753 passed in 3.40s.**

No additional runs (no new code; no fixture changes).

Per-file: not exercised. No new tests written.

**Post-baseline = pre-baseline = 753 passed.** No regression
introduced.

---

## §6 — Gate results

Pre-baseline = post-baseline (no code changes):

- **lint-imports:** 5 kept / 0 broken. All five contracts
  continue to hold (DR-030 layered, domain-pure, store-pure,
  contracts-leaf, workflows-independence). No new contracts
  needed (Finding-D confirms the independence contract permits
  the W12 cross-workflow import shape as-is).
- **mypy:** Success on the previously-clean modules. No new
  source files to type-check.
- **ruff:** Not run (no new code).

**Dirty-tree integrity confirmed at close.** `git status --short
| wc -l` → 37 entries (unchanged from session open). HEAD
`2329604a...` unchanged. No state-mutating git commands run per
§9.6. §9.7 dirty-tree discipline held.

---

## §7 — Spot-check result (§7.5)

**Not run.** §7.5 smoke script targets the six derivation
functions plus the seed-mechanism end-to-end. None of those
exist (no code shipped). The smoke script at `/tmp/w12_smoke.py`
was not written for this session — partial-ship discipline (§9.8)
calls for halting at the next coherent boundary, which is the
alignment gate, before the smoke script becomes meaningful.

If operator-Claude prefers a "pre-build smoke" exercising only
the existing shipped surfaces (which is essentially the W13
smoke at `/tmp/w13_smoke.py` from session 130), that's already
covered in the W13 report §7.

---

## §8 — Findings

Findings classified per brief §8 (a)/(b)/(c) buckets:

### (a) Brief-spec deviations from shipped reality

Where Code's implementation would have deviated from the brief
because the brief's text refers to fields, method names, or
algorithm shapes that don't match what's shipped. These are
brief-update opportunities; no substrate change needed.

- **Finding-B — Promo adapter method names.** Brief uses
  `create_promo_template` / `list_warning_catalogue_entries` /
  etc; adapter exposes `create_template` / `list_warning_types`.
  Light brief amendment.
- **Finding-J — Warning state algorithm uses cleared payload
  shape that doesn't exist.** Cleared payload references the
  raise event ID, not warning_type_id. Algorithm rewrite needed.
- **Finding-K — `severity_at_raise` mandatory.** Algorithm
  simplifies — catalogue fallback path doesn't fire.
- **Finding-L — `face_value_expiry` not `expires_at`.** Output
  model rename.
- **Finding-M — Location 2 "per custodian" framing.** Operator
  framing aligns with reading (ii); architecture wording could
  be tightened. Not blocking.
- **Finding-N — `warning_type_id` not on cleared payload.** §5.1
  step-zero edit list reduces from three locations to two.
- **Finding-O — Warning catalogue slug semantics.** Per
  Finding-N; clarification only.
- **Finding-I — Net flow window vs since-day-0.** Brief's
  window-bounded extension is a reasonable specialisation; no
  architecture conflict.

### (b) Spec-implied substrate concerns

Where the brief's spec implies substrate that doesn't exist or
substrate the brief assumed had different shape. These route to
substrate-touching workstream work, DR amendments, or operator-
side scope revisions.

- **Finding-C — Bet record substrate gaps.** Load-bearing for
  §5.3 / §5.4 / §5.8. No `promo_id` linkage on `BetRecord`. No
  `list_by_account_at_book` method on `SQLiteBetRecordStorage`.
  Mitigation options listed in §2.3 above.
- **Finding-F — No external-payment classification helper.**
  Brief allowed inline-listing fallback; light alternative is a
  one-line additive edit to `domain.cash_flow`.
- **Finding-G — `FreeBetCreditSource` enum binary not rich.**
  Brief assumed `INSURANCE_TRIGGER` / `BONUS_WINNINGS_TRIGGER` /
  `GOODWILL` etc; shipped is `TRIGGERED` / `FREEBIE`. Routes to
  either a domain enum expansion, a brief revision to use the
  binary plus template-kind lookup, or treating rich semantics
  at the W17 UI layer.
- **Finding-H — Balance algorithm vs cash flow event types.**
  Load-bearing. The brief's algorithm assumes `bet_won` /
  `bet_lost` cash flow events that don't exist. Architecture.md
  §A.5 / §A.6 define the canonical formula differently — cash
  returns come from the bet row, not from cash flow events.
  Mitigation options in §2.8 above.

### (c) Pre-existing codebase shape

Standing observations rather than W12 issues; logged for visibility
but no immediate action.

- **Finding-E — `_ensure_adelaide_local` duplicated.** Two
  copies in domain modules; functionally identical, prose
  differs. Acceptable per DR-030 spirit; deduplication is a
  future cleanup if desired.

---

## §9 — What was deliberately not done

Mirroring brief §1.2 plus the partial-ship surface this session:

- **No code shipped.** No new files, no edited files, no test
  files, no smoke script.
- **No §5.1 slug-flip edit on `domain/promos/__init__.py`** —
  halted at alignment gate per §6.1 rule; the slug-flip also
  needs revisiting per Finding-N (two locations, not three).
- **No W13 test fixture swap.**
- **No §5.1 fallout cleanup in `promo_store_adapter.py`.**
- **No package marker writes.**
- **No `scripts/seed_promos.py`.**
- **No FB inventory derivation.**
- **No AccountCare warning state derivation.**
- **No promo journey state derivation.**
- **No balance derivations.**
- **No `store/__init__.py` re-export additions.**
- **No tests.**
- **No DR amendments.** No `decisions.md` edits.
- **No `architecture.md` amendments.** Finding-M flags a wording
  tightening opportunity but does not unilaterally apply it.
- **No `.importlinter` contract amendments.**
- **No state-mutating git commands.**

---

## §10 — Open questions for triage

Pulling out the explicit operator-Claude calls Code recommends
for the next session. Where appropriate, Code names which option
seems cleanest from a software-shape view (per Cat 5) without
forcing the call.

**Q1 (Finding-B method names) — small fix.** Update the brief's
literal method names (`create_promo_template`,
`list_warning_catalogue_entries`, etc.) to the shipped
`create_template` / `list_warning_types` / etc., OR vice versa
(rename adapter methods). Code's read: update the brief; the
adapter names are reasonable and shorter, and the brief is the
cheaper edit.

**Q2 (Finding-C bet record substrate) — substantial.** Three
plausible routes per §2.3:
- (i) Revise W12 brief to use raw-SQL list query against the
  `bets` table plus the promo→bet linkage (read from promo events,
  not from a bet field). Cheapest. Code's preferred shape.
- (ii) Commission a small W11.x or W4.x interim workstream to
  add `list_bet_rows_by_account_at_book` to the bet storage class
  plus consider adding a `promo_template_id` linkage on the
  bet record. Cleaner long-term; more work.
- (iii) Defer journey-state derivation entirely (out of W12
  scope; revisit when bet-record substrate has the linkage).
  Cleanest scope cut for this session.

**Q3 (Finding-G `FreeBetCreditSource`) — operator-strategic.**
Three options per §2.7:
- (i) Expand the enum in `domain.promos` to include
  `INSURANCE_TRIGGER` / `BONUS_WINNINGS_TRIGGER` / etc.
  Additive; DR-030-respectful. Operator names what values to
  add.
- (ii) Revise brief to use the binary `TRIGGERED` / `FREEBIE`
  plus template-kind lookup for richer semantics. Cheaper code
  but reads less directly.
- (iii) Treat rich semantics at the W17 UI label layer; W12
  outputs the binary enum. Cleanest separation.

**Q4 (Finding-H balance algorithm) — load-bearing.** Three
options per §2.8:
- (i) Revise the W12 brief's balance algorithm to follow
  architecture.md §A.5 verbatim. Code's preferred path —
  architecture is the canonical source of truth; brief was
  inconsistent with it.
- (ii) Commission a `bets_events` (or `settlement_events`)
  workstream so bet settlement becomes an event. Substantial
  architectural shift.
- (iii) Continue with derived-from-bet-row approach but adjust
  brief scenarios CASH-2 / CASH-4 to reflect the shipped event
  shape.

**Q5 (Finding-I net flow window vs since-day-0) — Cat 5
software call by Code.** Both reads are valid. Code's preferred
path: keep the window form (more operationally flexible; brief
spec is reasonable) and clarify in the brief that the formula is
"net flow over the named window", not "cumulative since day 0".

**Q6 (Finding-J / K / N warning state semantics) — small
cluster.** Combine into one decision pass: revise the brief's
§5.7 algorithm to read raise events with their attached
`severity_at_raise` (mandatory), walk for clear events matching
each raise's `event_id`, and group by `warning_type_id` (on the
raise side). Reduce §5.1 slug-flip from three field annotations
to two. Code's preferred path.

**Q7 (Finding-M custodian framing) — operator-strategic.**
Confirm Location 2's per-`book_id` framing matches the operator's
mental model. Architecture wording could be tightened to remove
the "account_holder" ambiguity. Light architecture edit if
operator confirms.

**Q8 — partial-ship vs full re-brief vs surgical-fix.** Given the
combined findings, the cleanest forward path is probably a brief
revision pass (not a fresh W12 brief; an in-place tightening of
§5.1 / §5.3 / §5.6 / §5.7 / §5.8 to align with shipped substrate)
followed by a fresh Code session to execute the revised brief
end-to-end. Alternative: pull §5.6 / §5.7 forward (FB inventory +
warning state — narrower in scope and lighter on substrate
risks) and defer §5.3 / §5.4 / §5.8 to a follow-up after the
balance-algorithm question (Finding-H) is resolved.

---

## §11 — What Code thinks should land next

Two plausible forward paths plus a recommended one.

### Path A — Brief revision then fresh W12 session

Operator-Claude opens the next session, triages the findings
above (probably Q1 + Q2 + Q4 + Q6 in one pass; Q3 / Q5 / Q7 as
operator calls), revises the W12 brief at the named anchors,
then commissions a fresh Code session to execute the revised
brief.

**Argument for:** clean separation. Operator-Claude does the
spec work; Code does the build work. The revised brief lands as
the operationally-correct spec; the next Code session executes
it without re-discovering findings.

**Argument against:** two operator-Claude sessions (triage +
brief revision) before Code re-engages. Slightly slower than
Path B.

### Path B — Reduced-scope W12 first ship

W12 scope cuts to just FB inventory (§5.6) and AccountCare
warning state (§5.7) for first ship. Both read from the W13
substrate exclusively (no bet-record dependency, no cash-flow
dependency). Brief revisions confined to:

- §5.6: rename `expires_at` → `face_value_expiry` in the output
  model.
- §5.7: rewrite the algorithm against raise-event-id-linked
  clears, mandatory `severity_at_raise`.
- §5.1 slug-flip: two field annotations (catalogue + raise
  payload).
- §5.2 seed mechanism: still ships (no findings against the seed
  content spec).

§5.3 (balance), §5.4 (cash holding), §5.5 (net flow), §5.8
(promo journey) defer to W12.1 (after balance-algorithm
question and bet-record substrate question are resolved).

**Argument for:** ships operator-facing value (FB inventory at
each book, warning state at each book) within the existing
substrate. No new workstreams, no architectural decisions
required. Smaller delta to brief.

**Argument against:** doesn't ship the balance numbers the
operator's daily workflow most depends on. The "value-per-
session" calculus favours Path A or Path C below.

### Path C — Recommended: brief tightening pass at operator-Claude triage, then full W12 Code session

Pull Path A's "brief revision" into the operator-Claude triage
session itself (combine the triage + brief tightening into one
operator session). Each finding gets its decision; each decision
lands as a precise brief amendment at the named anchor; the
revised brief locks at the end of the same session. Next Code
session executes end-to-end against the locked brief.

Concretely:

- **Q1** → revise method names in brief §5.2 / §5.6 / §5.7 /
  §5.8 to match adapter. Probably 6-10 inline name changes.
- **Q2** → pick option (i) — revise brief to use raw-SQL list
  query plus promo→bet linkage. Brief §5.3 / §5.4 / §5.8 algorithm
  sections update. Probably 30-50 lines of brief diff.
- **Q4** → pick option (i) — revise brief §5.3 algorithm to
  follow architecture.md §A.5 / §A.6 verbatim. Probably 40-60
  lines of brief diff.
- **Q6** → revise brief §5.1 slug-flip to two locations; revise
  §5.7 algorithm to raise-event-id-linked semantics; remove the
  catalogue-fallback prose. Probably 25-40 lines of brief diff.
- **Q3** → pick option (iii) — W12 produces binary enum; W17
  layer surfaces rich semantics. Brief §5.6 algorithm and output
  model preserve the binary `FreeBetCreditSource` import; brief
  scenarios CASH-4 / CASH-5 update credit_source string literals
  to `TRIGGERED` / `FREEBIE`. Probably 10-20 lines of brief
  diff.
- **Q5** → keep the window form; clarify brief §5.5 prose to
  remove any "since day 0" inference. Probably 5 lines.
- **Q7** → operator confirms Location 2 framing; consider a
  small architecture.md §A.5 wording tightening alongside. ~10
  lines.

Total brief diff at Path C: ~130-200 lines of revision across
6-8 brief sections. Then the next Code session executes the full
revised W12 build (still ~12-14 new files plus ~2-3 edited).
Single-session shippability remains intact after the revision.

**Code's preference:** Path C. Path A and Path C differ only in
sequencing — Path C bundles triage and revision; Path A
separates them. The brief is precise and the findings are
well-bounded enough that Path C is achievable in one
operator-Claude session.

### Forward-routing thoughts (per the operator commission)

- **W12.1 surgical-fix scope risk** named in brief §10. Not
  triggered by this session: there's no clean W12.1 path because
  no code shipped. The next move is brief revision (a
  triage-and-revise operator session), then a fresh Code
  session for the full W12 build.
- **W15 (`ops_events`)** remains blocked on W12 per Path D from
  Session 131. Unchanged by this session.
- **Hedge classification (DR-025, Finding #8 from S123)** —
  forward-tracked per brief §10. The CASH-4 scenario in brief
  §7.3 would have exercised hedge classification; deferred with
  W12.
- **Bet-record promo linkage** — surfaces as a candidate future
  substrate edit per Finding-C. Probably best routed via a small
  W4.1 or W11.1 surgical-fix workstream that adds
  `promo_template_id` / `triggering_promo_instance_id` to the
  `BetRecord` model alongside a list-by-account-at-book read
  method. Could be done before the next W12 attempt if Q2 lands
  on option (ii).
- **Cash flow event log shape** — Finding-H surfaces a deep
  question about whether the v3 substrate's "events are the
  source of truth" framing applies to bet settlement events.
  Worth a DR-level conversation in the next operator-Claude
  session.

---

**End of W12 report.** No code shipped this session per §6.1
halt rule; comprehensive alignment findings surfaced for
operator-Claude triage. The brief is well-anchored against W13
adapter shapes (Findings A, D pass) but materially diverges from
W4/W6/W11/W14 + architecture.md on balance derivation and bet-
record substrate (Findings C, F, G, H). Path C (triage +
in-session brief tightening, then fresh Code session) is Code's
recommended forward shape.
