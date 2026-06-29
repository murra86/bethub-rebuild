# Batch 1 revision drafts — S134 → S135

**Drafted:** 2026-05-17 13:49 ACST (S134 close)
**Apply at:** S135 open
**Brief target:** `dr029/w12_balances/w12_balances_brief.md`
**Pre-revision backup:** `dr029/w12_balances/.pre_s134_revision/w12_balances_brief.md`

These six anchor drafts are operator-confirmed at S134 close.
S135 applies them via `edit_block` in the order below, then
proceeds to Batch 2 (mechanical applications), then the
architecture.md §A.5 paragraph, then drafts the Code opening
prompt.

The S134 review summary the operator confirmed:
"All good" on Batch 1 summary covering 6 load-bearing changes.

---

## Change 1 — Insert new §1.4 after §1.3

**Anchor:** the `---` separator immediately following §1.3
(the line that closes the "Operator can override any of these
at any time before Code lock." paragraph, at approximately
line 217 of the pre-revision brief).

**Insertion:** add `### §1.4 — Triage context from Session 134`
as a new subsection before that `---`.

**New prose:**

```
### §1.4 — Triage context from Session 134

W12 was first commissioned at S133 against a brief that
assumed several substrate shapes that didn't match what
W4 / W6 / W11 / W13 / W14 had actually shipped. Code
halted at §6.1 alignment per the halt rule; the W12
report at `dr029/w12_balances/w12_balances_report.md`
surfaced 15 findings across 7 brief-spec deviations
and 7 load-bearing alignment misses.

S134 triaged the findings and locked the following
decisions. Each is referenced at the relevant build
section; named here in one place so the rationale is
discoverable without re-reading the report.

**Balance algorithm follows architecture.md §A.5 / §A.6
verbatim** (Finding-H). Cash returns from bet
settlements compute on read from the bet row
(`matched_stake × matched_price` against settlement
state), not from cash flow events. No `bet_won` /
`bet_lost` event type exists or will be added; bet
settlement remains a derived-on-read consequence of the
bet row's settlement state per DR-019.

**Read-side derivations may read directly from
`store.repositories.*` SQL paths** where the typed
workflow adapter exposes no matching read method
(Finding-C). Write paths always go through the typed
adapter surface. The asymmetry is intentional: adapters
exist to enforce payload contracts and supersession
discipline on the write side; read derivations under
DR-019 optimise differently and frequently read at the
SQL layer. Each W12 derivation that drops to SQL names
the read path and reason inline. Architecture.md §A.5
carries this as a design principle (added alongside
this brief revision).

**Location 2 is per account-holder, not per
custodian-as-bookmaker** (Finding-M). The W12 output
returns the holder's parked-pool balance, the list of
that holder's per-account-at-book balances (existing
Location 1 derivation filtered to this holder), the
total cash with the holder, and the cumulative
profit-share distributed to the holder. Aggregating
across account-holders at the same book is not
meaningful and not computed; those are separate
operational positions.

**FB inventory surfaces an enriched credit-source
label** (Finding-G). The shipped `FreeBetCreditSource`
enum is binary (`TRIGGERED` / `FREEBIE`); W12 keeps
that import unchanged and additionally derives a
`credit_source_label` field on the output model by
walking from the FB credit event's
`triggering_promo_instance_id` to the source promo's
template kind. Operationally rich labels (insurance
trigger, bonus-winnings trigger, goodwill) surface
without mutating the shipped enum or duplicating
linkage onto the FB credit event payload.

**Warning state walks raise-event-id linkages, not
warning-type tallies** (Finding-J + Finding-K).
`AccountCareWarningClearedPayload` references the
specific raise event ID it cancels, not the warning
type. The algorithm walks each raise and checks for a
clear event referencing its event ID. Severity comes
from `severity_at_raise` on every raise (the field is
mandatory; no catalogue-fallback path).

**Promo→bet linkage reads backwards via the promo
event log** (Finding-C Gap 2). The bet record does not
carry a `promo_template_id` field; the linkage exists
on the promo event side
(`FreeBetCreditedPayload.triggering_bet_id`,
`FreeBetDeployedPayload.deploying_bet_id`). The promo
journey derivation reads from this direction. No
substrate change to the bet record.

The remaining findings (B method names, F external-
payment classification, I net-flow window framing, L
FB expiry field rename, N slug-flip target count, O
slug semantics clarification, E `_ensure_adelaide_local`
duplication standing observation) land as Cat 5
mechanical applications in the relevant build sections.
```

---

## Change 2 — §5.3 Substrate read + Algorithm sections

**Edit anchor:** replace existing lines 608–657 of the
pre-revision brief (the "Substrate read" and "Algorithm
(plain language)" blocks under §5.3).

**Pre-revision text starts with:** "**Substrate read.**\n\n-
`CashFlowStoreAdapter.list_by_account_at_book("

**Pre-revision text ends with:** "...The pending bet stake
subtraction is the only \"live\" adjustment outside the cash
flow event log."

**New prose:**

```
**Substrate read.**

- `CashFlowStoreAdapter.list_by_account_at_book(
  account_at_book_id)` — all cash flow events for the
  account-at-book. The shipped event-type taxonomy
  carries no bet-settlement event; this read returns
  deposits, withdrawals, balance adjustments, and the
  account-at-book scoped subset of any external
  payment events. Per architecture.md §A.5, this is
  one of three reads feeding the cash balance.
- **Bet records for the account-at-book** — read
  directly via raw SQL against the `bets` table
  (`SELECT * FROM bets WHERE account_at_book_id = ?`).
  The W6/W6.5 bet storage class exposes no
  `list_by_account_at_book` method; per §3.1 the
  read-side may drop to `store/repositories/bets.py`
  patterns. The bet rows feed the cash stake
  subtraction and the computed cash return per
  architecture.md §A.6.
- `promo_cash_credited` events from
  `PromoStoreAdapter.list_by_account_at_book(
  account_at_book_id,
  event_type=PromoEventType.PROMO_CASH_CREDITED)` —
  the third leg of architecture.md §A.5. Only events
  with payload status `finalised` count.
- FB inventory (the §5.6 derivation, called
  internally) — for the separate `free_bet_balance`
  output field, not the cash balance.

**Algorithm (plain language).**

Per architecture.md §A.5, the per-account-at-book
cash balance is:

  + sum of `account_at_book_deposit` event amounts
  − sum of `account_at_book_withdrawal` event amounts
  ± sum of `account_at_book_balance_adjustment` signed amounts
  − sum of `bets.matched_stake` for rows where
    `is_free_bet = False` and the bet has been placed
    (any settlement state; the stake left the account
    at placement)
  + sum of computed cash return per bet row (see §A.6
    derivation: `matched_stake × matched_price` for won
    bets; zero for lost bets; refunded stake for
    pushed / scratched bets — the substrate's
    settlement-state field drives this)
  + sum of `promo_cash_credited` event amounts where
    payload status is `finalised`

Free-bet stakes (`is_free_bet = True`) do not subtract
from cash — the FB's face value was never cash to
begin with. Free-bet returns to a cash bet still
compute as cash (the FB conversion rate, if any, is
applied per the bet row's `free_bet_conversion_rate`
field).

**Pending-bet stake separation.** For the operator-
facing `pending_bet_stake_total` field on the output,
sum `matched_stake` only for cash bets in the
"placed-and-not-yet-settled" state (substrate's
settlement-state enum is the source of truth for
"placed"; check the live bet row, not the historical
state per DR-019).

Free bet balance = the §5.6 inventory derivation's
total face value across all available FBs.
```

---

## Change 3 — §5.4 full rewrite (title + body)

**Edit anchor:** replace existing section title at line 750
plus body through line 814.

**Pre-revision section title:** `### §5.4 — Per-custodian
cash holding (Location 2)`

**New section title:** `### §5.4 — Per-account-holder cash
holding (Location 2)`

**New body prose:**

```
**What it computes.** For a given `account_id` (the
account-holder, e.g. Sarie, Tim-self, partner-persona),
returns the total cash sitting with that holder across
the operation: parked-pool balance not yet deployed
to any book, plus per-account-at-book balances at each
book the holder holds an account at, plus the
cumulative profit share distributed to the holder
to date.

Aggregating cash across multiple holders at the same
book is not computed — those are separate operational
positions sharing only a bookmaker, not a meaningful
combined balance.

**Substrate read.**

- `CashFlowStoreAdapter.list_by_account(account_id)`
  — all cash flow events scoped to the
  account-holder. Feeds the parked-pool calculation.
- The §5.3 balance derivation, called once per
  account-at-book the holder holds. For the list of
  account-at-book IDs at the holder, raw SQL against
  the `accounts_at_book` table
  (`SELECT account_at_book_id, book_id FROM
  accounts_at_book WHERE account_id = ?`) per the
  §3.1 read-side asymmetry pattern.

**Algorithm (plain language).**

Parked-pool balance — cash sitting with the
account-holder but not deployed to any book — sums:

  + sum of `account_holder_funding` event amounts
    (inflow from Tim's bank to the holder)
  − sum of `account_holder_remittance` event amounts
    (outflow from the holder back to Tim's bank)
  − sum of `account_at_book_deposit` event amounts
    (outflow from the holder to a book)
  + sum of `account_at_book_withdrawal` event amounts
    (inflow from a book back to the holder)
  − sum of `profit_share_distribution` event amounts
    (outflow leaving the operation; both
    `funding_source` variants subtract from the
    parked pool — the money leaves the operation
    either way)
  ± sum of `account_holder_balance_adjustment` signed
    amounts (model-side corrections)

Per-account-at-book breakdown — for each of the
holder's account-at-book IDs, call
`compute_account_at_book_balance(conn,
account_at_book_id)` from §5.3. The breakdown is the
existing Location 1 derivation filtered to this
holder.

Total cash with holder = parked-pool balance + sum of
breakdown cash balances. This is the headline number.

Cumulative profit share distributed = sum of
`profit_share_distribution` event amounts at the
holder, both `funding_source` variants combined. Not
subtracted from the headline total (those amounts
left the operation; they're informational at this
holder view, separately from the parked-pool
calculation that already subtracts them).

**Pydantic output model.**

```python
class AccountHolderCashHolding(BaseModel):
    account_holder_id: UUID  # accounts.account_id
    parked_pool: Decimal
    at_book_balances: list[AccountAtBookBalance]
    total_with_holder: Decimal  # parked_pool + sum of breakdown cash
    total_profit_share_distributed: Decimal
    currency: str  # 'AUD'
    computed_at: datetime

    @field_validator('computed_at')
    @classmethod
    def _validate_adelaide_local(cls, v: datetime) -> datetime:
        return _ensure_adelaide_local(v)
```

**Edge cases.**

- **Holder with no events ever.** Returns zero
  parked-pool, empty breakdown, zero total, zero
  profit-share. Not an error.
- **Holder with parked cash but no book accounts.**
  Funding has landed but nothing's been deposited
  out yet. Breakdown is empty; total equals the
  parked-pool balance. Valid intermediate state.
- **Negative parked-pool.** Surfaces if withdrawals
  from books outpace deposits to books plus funding.
  Not an error — the derivation reports what events
  say. Operationally typically a data-flow issue.
- **Multi-currency.** AUD only at current scope per
  DR-022.
- **Profit-share semantics.** The
  `funding_source` field on `profit_share_distribution`
  events distinguishes whether the share funded
  directly from Tim's bank
  (`funding_source = 'tim_direct'`) or from the
  holder's existing parked-pool
  (`funding_source = 'account_holder_cash_holding'`).
  Both reduce parked-pool by the event amount; the
  distinction matters for operation-net-flow (§5.5),
  not for the holder view.

**File anchor:**
- Same module as §5.3:
  `workflows/balances/v1/balance_derivation.py`.
- Function: `compute_account_holder_cash_holding(conn:
  sqlite3.Connection, account_id: UUID)
  -> AccountHolderCashHolding`.

**lint-imports compliance.** Same as §5.3 — domain.cash_flow,
workflows.cash_flow.v1, plus raw SQL access via the shared
sqlite3.Connection per §3.1 read-side asymmetry.
```

---

## Change 4 — §5.6 algorithm step 2 + model

**Edit anchors:** two edits.

**Edit 4a — algorithm step 2** (replace existing step 2 at
approximately lines 950–966 of the pre-revision brief).

**Pre-revision step 2 starts with:** "2. For each FB whose
latest state is \"available,\" read"

**Pre-revision step 2 ends with:** "- Linked promo ID (the
`promo_id` payload field if present)."

**New algorithm step 2 prose:**

```
2. For each FB whose latest state is "available," read
   the credit event's payload to extract:
   - Face value (the `amount` payload field).
   - Expiry timestamp (the `face_value_expiry` payload
     field — name matches the W13 shipped payload, not
     the brief's earlier `expires_at`).
   - Triggering promo instance ID (the
     `triggering_promo_instance_id` payload field if
     present — null for goodwill FBs).
   - Credit source (the `credit_source` payload field
     — the W13 shipped binary enum: `TRIGGERED` or
     `FREEBIE`).

   For each FB with a non-null
   `triggering_promo_instance_id`, walk to the source
   promo via
   `PromoStoreAdapter.get_promo(triggering_promo_instance_id)`,
   then walk to the promo's template via
   `PromoStoreAdapter.get_template(promo.template_id)`,
   then read `template.kind` to derive the rich
   `credit_source_label`:
   - `INSURANCE` → `"insurance trigger"`
   - `BONUS_WINNINGS` → `"bonus-winnings trigger"`
   - `PRICE_BOOST` → `"price-boost trigger"`
   - `EW_CASHBACK` → `"each-way cashback trigger"`
   - `OTHER` → `"other trigger"`

   For FBs with a null
   `triggering_promo_instance_id` (i.e. `credit_source
   = FREEBIE`), `credit_source_label = "goodwill"`.
```

**Edit 4b — `AvailableFreeBet` Pydantic model** (replace
existing model at approximately lines 976–984).

**Pre-revision model starts with:** `class AvailableFreeBet(BaseModel):`
**Pre-revision model ends with:** `credit_source: FreeBetCreditSource  # the W13 enum`

**New model:**

```python
class AvailableFreeBet(BaseModel):
    credit_event_id: UUID
    face_value: Decimal
    currency: str  # 'AUD'
    credited_at: datetime
    face_value_expiry: datetime | None
    source_promo_instance_id: UUID | None
    source_template_id: UUID | None
    credit_source: FreeBetCreditSource  # W13 binary enum
    credit_source_label: str  # derived per algorithm step 2
```

---

## Change 5 — §5.7 algorithm rewrite

**Edit anchor:** replace algorithm block at approximately
lines 1066–1095 plus the "Catalogue severity changed after
raise" edge case at approximately lines 1136–1141.

**Pre-revision algorithm starts with:** `**Algorithm.**\n\nFor
each unique \`warning_type_id\` referenced`

**Pre-revision algorithm ends with:** `the underlying
event-log semantics from W13 are\n\`raised − cleared\` count.`

**New algorithm prose:**

```
**Algorithm.**

For each `accountcare_warning_raised` event at the
account_at_book (ordered by event timestamp ascending):

1. Check whether any subsequent
   `accountcare_warning_cleared` event has
   `cleared_warning_event_id == this raise event's
   event_id`.
2. If yes — this raise has been cleared. Skip.
3. If no — this raise is active.

Group active raises by `warning_type_id` (the field on
the raise payload). If a single warning type has
multiple unmatched raises (raised twice before any
clear), the most-recent active raise per warning_type
is the "current" raise for that type.

For each current active raise, build an
`ActiveWarning` model:

- `warning_type_id` (the slug; from the raise event's
  payload, which is the only payload carrying the
  field — clear events reference the raise event ID,
  not the warning type).
- `label` (from the catalogue lookup at
  `PromoStoreAdapter.get_warning_type(warning_type_id)`).
- `severity`: the `severity_at_raise` field on the
  raise event. The field is mandatory on the shipped
  W13 payload (not nullable); every raise carries an
  explicit severity. The catalogue's baseline
  `severity` is informational only at the warning-
  type-display layer and is not consulted by the
  active-warning derivation.
- `raised_at`: the timestamp of the raise.
- `raise_event_id`: the raise event's ID.

Sort: severity descending (`red` first, then `amber`,
then `yellow` per DR-015), then `raised_at`
descending within severity.

**Cleared-warnings handling.** Cleared warnings are NOT
in the active state output. A future "warning history"
derivation would surface them; the current state
surface is active-only by design.

**Multiple raises before clear.** If a warning type is
raised twice before either raise is cleared, both
raises are active until matched by their own clear
event. The clear events reference specific raise
event IDs (not the warning type), so one clear
cancels exactly one raise. The "current" active
raise displayed per warning type is the most recent
of the unmatched raises.
```

**Edge case replacement (the catalogue-severity-changed
case removed; new edge case in its place):**

```
- **Severity always from raise event.** The raise
  event's `severity_at_raise` is the operationally-
  binding severity. Catalogue severity exists for
  display-time defaulting at the warning-type label
  layer (out of W12 scope), not for active-warning
  derivation.
```

---

## Change 6 — §5.8 substrate read + algorithm step 2

**Edit anchors:** two edits.

**Edit 6a — substrate read bullet for bet records** (replace
existing "Bet records linked to the promo" bullet at
approximately lines 1207–1216).

**Pre-revision bullet starts with:** "- Bet records linked
to the promo — read via the bet-"

**Pre-revision bullet ends with:** "filter shape)."

**New prose for the bullet (becomes two bullets):**

```
- Bet records linked to the promo — read by walking
  the promo event log backwards. Specifically, the
  `FreeBetCreditedPayload.triggering_bet_id` field
  (on FB credit events at the account_at_book) and
  the `FreeBetDeployedPayload.deploying_bet_id` field
  (on FB deploy events at the account_at_book) carry
  bet IDs. To find bets linked to a given promo
  template, filter promo events for the
  `account_at_book_id` and read the bet IDs from
  matching credit / deploy event payloads. The bet
  record itself does not carry a forward
  `promo_template_id` field; the linkage exists only
  in the reverse direction on the promo event side.
- Bet records read by ID — once the bet IDs are
  collected from promo events, fetch each bet row
  directly via the bet storage class's
  `read_bet_record(bet_id)` method (this surface
  exists; only `list_by_account_at_book` is missing
  per Finding-C Gap 1).
```

**Edit 6b — algorithm step 2** (replace existing step 2 at
approximately lines 1235–1239).

**Pre-revision step 2 starts with:** "2. No bet placed (no
bet record links back to a"

**Pre-revision step 2 ends with:** "state is\n
`OBSERVED_NOT_TAKEN`. Stop."

**New prose:**

```
2. No bet placed against the promo — walk the promo
   event log for the account_at_book. If no
   `free_bet_credited` event references a bet_id via
   `triggering_bet_id` and no
   `promo_journey_annotation` event with `taken` tag
   exists for the promo_template_id, state is
   `OBSERVED_NOT_TAKEN`. Stop.
```

---

## Notes for S135 application

- Apply Changes 1–6 in order via `edit_block`.
- Pre-revision backup at
  `dr029/w12_balances/.pre_s134_revision/w12_balances_brief.md`
  is the diff-comparison source.
- After all six edits, sanity-check the brief end-to-end
  with `wc -l` and a section-header grep to confirm
  structure intact.
- Then proceed to Batch 2:
  - §3.1 read/write asymmetry framing add (~10 lines).
  - §5.1 slug-flip count three → two (drop the
    cleared-payload bullet).
  - §5.2 adapter method name fixes
    (`create_promo_template` → `create_template`,
    `create_warning_catalogue_entry` →
    `create_warning_type`, etc.).
  - §5.5 net-flow window clarification (~5 lines).
  - §7.3 scenarios — CASH-2 (remove bet-return cash
    flow event), CASH-4 step 4 (remove lay liability
    cash flow events; replace with bet-row-derived
    returns), CASH-5 (change `GOODWILL` → `FREEBIE`,
    add `credit_source_label: "goodwill"`).
- Then the architecture.md §A.5 paragraph
  (~15 lines) per Finding-C visibility lock + Finding-M
  Location 2 framing + profit-share funding-source
  variants.
- Then draft the Code opening prompt with the
  review-before-build shape.
