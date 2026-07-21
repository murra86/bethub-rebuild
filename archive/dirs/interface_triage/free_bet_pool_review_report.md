# Free-bet pool review report (read-only source map)

**Run:** 2026-06-19 ACST (Session 168 follow-on, one bounded Code session).
**Scope:** read-only source map of v3's free-bet pool + settlement layer
against the brief at `interface_triage/free_bet_pool_review_brief.md`.
**Repo state:** `bethub-v3` left exactly as found. No edits, no build, no
git operations. The only file written is this report.
**Method:** source read of the files named in brief §5, plus targeted
repo-wide greps to confirm the negative findings (no false "not built").

> **Headline (read this first).** The free-bet **read** side (pooled
> balance, inventory, deploy events, deploy UI) is substantially built.
> The free-bet **write/credit** side is not: **no production code path
> creates a `free_bet_credited` event anywhere** — not at settlement,
> not via any API route, not via the seed script. The pool can be drawn
> *down* but nothing in the running application fills it *up*. This
> reframes both effort buckets and is detailed in §1, §2.2, and §4.1.

---

## 1 — Settlement-today map (brief §5.1)

### 1.1 What runs settlement

`domain/settlement/__init__.py` is confirmed **0 bytes** (empty stub) —
the real logic lives in `workflows/bet_entry/v1/settlement.py` (1,354
lines), with the manual-resolve surface in
`ui/api/routers/provisional.py`.

The settlement worker (`run_settlement_pass`, `settlement.py:698`) sweeps
bets in `SettlementState.PENDING` whose event has started, reads the
Betfair Win market via a `SettlementReader`, and resolves each bet through
`_resolve_settlement_for_bet` (`settlement.py:319`). A second pass,
`run_provisional_resolution_pass` (`settlement.py:914`), re-checks bets
already in `PROVISIONAL`.

### 1.2 What it does on each terminal state

`_resolve_settlement_for_bet` (`settlement.py:319-486`) is the state
machine. Per terminal outcome:

| Outcome | Trigger | New state | Reason code |
|---|---|---|---|
| Won | runner `WINNER` (`:449`) | `SETTLED_WON` | `settled_won` |
| Lost | runner `LOSER` (`:461`) | `SETTLED_LOST` | `settled_lost` |
| Voided | market voided (`:406`) / runner `REMOVED` (`:436`) | `VOIDED` | `voided_market_voided` / `voided_runner_removed` |
| Provisional | runner missing / unexpected status (`:424`, `:476`) | `PROVISIONAL` | `provisional_unexpected_state` |
| No-op | read failed / market not closed / not yet settled (`:363`, `:376`, `:388`) | stays `PENDING` | — |

`PROVISIONAL` bets route to the burst-review queue
(`ui/api/routers/provisional.py`) and are cleared by
`apply_manual_operator_resolution` (`settlement.py:1128`), which transitions
`PROVISIONAL → SETTLED_WON | SETTLED_LOST | VOIDED` on operator decision.

### 1.3 What settlement writes — and what it does not

On a state transition the worker writes **only**:

- `settlement_state` + the three race-count fields (`dead_heat_count`,
  `removed_runner_count`, `unexpected_state_count`) — via
  `storage.update_settlement_state` (`settlement.py:1193-1199`, and the
  auto path in `run_settlement_pass`).
- reconciliation bookkeeping `last_reconciled_at` /
  `reconciliation_attempts` — `_write_settlement_bookkeeping`
  (`settlement.py:852-870`).
- `last_read_market_state` (raw Betfair JSON, operator visibility) —
  `_persist_last_read_market_state` (`settlement.py:878-906`).

**Does a settled-as-won insurance qualifier auto-create the triggered
free-bet credit? No.** Evidence:

- `grep -niE "free_bet|credit|triggered|promo"` over the whole of
  `settlement.py` (1,354 lines) returns **nothing**. Confirmed — the
  brief's first-pass signal holds.
- The `SettlementReasonCode` literal set (`settlement.py:122-132`)
  contains only settled/voided/provisional/read codes — no credit code.
- `realised_conversion_rate` is never written by settlement (consistent
  with the S167 records-look Finding 3: the column exists but is always
  NULL; `record_builder.py:315,394`).
- The cascade-credit trigger — the mechanism that *would* fire a credit
  off a settled qualifier — is explicitly **out of scope** in the credit
  model itself: `domain/promos/__init__.py:305-307` notes the cascade
  trigger "lives in the future burst-review workstream; W13 ships the
  WRITE surface so the trigger can land cleanly later."

**Answer:** settlement today is a pure bet-state machine. It touches the
promo layer in **zero** places. Free-bet crediting does not happen in the
settlement path, and (per §2.2 / §4.1) does not happen anywhere else in
production code either. Where it *would* hook in: a new credit-write call
inside the won/voided branches of `_resolve_settlement_for_bet`
(`settlement.py:449/406/436`) and/or the manual-resolve path
(`apply_manual_operator_resolution`, `settlement.py:1128`), gated on the
qualifier's promo instance being an insurance/bonus template.

---

## 2 — Pool-model wired-vs-missing (brief §5.2)

The promo layer is **event-sourced**, separate from the `bets` table:
`promo_events` rows carry a typed payload and a `supersedes_event_id`
chain (`domain/promos/__init__.py:75-92`, nine event types). Inventory and
balance are *derived* by walking that chain — there is no stored balance.

### 2.1 Wired-vs-missing table

| # | Pool-model piece | Verdict | Evidence |
|---|---|---|---|
| 1 | Pooled balance per account-at-book | **BUILT** | `compute_account_at_book_balance` (`balance_derivation.py:328`) sets `free_bet_balance = inventory.total_face_value` (`:401`), one pooled figure from `compute_free_bet_inventory` (`promo_derivations.py:153`). Also surfaced per-credit count `free_bet_count` (`balance_derivation.py:115`). |
| 2 | Credit→qualifier link | **PARTIAL** (modeled, unreachable) | Link fully modeled: `FreeBetCreditedPayload.triggering_bet_id` + `triggering_promo_instance_id` (`domain/promos:314-315`), validator forces both for `credit_source='triggered'` and forbids both for `freebie` (`:330-346`). **But no production code writes a credit** (see §2.2) — so the link has no creation path. |
| 3 | Oldest-first drawdown + auto cycle/parent attribution at commit | **MISSING** | Two distinct gaps — see §2.3. Confirms records-look Finding 2: deployed bet starts a **fresh** cycle. |
| 4 | Discrete-fenced flag | **MISSING** | `grep -rniE "discrete\|single.?unit\|fenced"` over `domain/ workflows/ store/ ui/` returns **zero** hits. `FreeBetCreditedPayload` (`domain/promos:310-321`) has no such field. |
| 5 | Operator deploy surface | **PARTIAL** | Deploys against pool inventory but operator ticks individual credits — see §2.4. |

### 2.2 The credit-write gap (underpins pieces 2 & 3)

The only production caller of `PromoStoreAdapter.append_event` anywhere in
the repo is `fb_deployment.py:166` — which writes **deploy** events.
Confirmed by:

- `grep -rn "\.append_event(" --include="*.py"` (excluding tests/.venv) →
  one hit: `fb_deployment.py:166`.
- `grep -rn "event_type=PromoEventType.FREE_BET_CREDITED"` (non-test) →
  only `promo_derivations.py:182,490`, both **reads** (inventory/journey
  walks), not writes.
- `grep -rn "FreeBetCreditedPayload("` (constructor, non-test) → none
  outside the class definition.
- `scripts/seed_promos.py` seeds `promo_template` + `warning_catalogue`
  reference rows only (its docstring, lines 1-9) — **not** credit events.
- No promo router exists (`ui/api/routers/` = accounts, health,
  provisional, racing); none of them expose a credit-write endpoint.

**Consequence:** in production the FB inventory the operator deploys from
(`LogBetPanel` → `free_bets`) is only ever populated by test fixtures /
manual DB seeding. Piece 1's pooled balance is real machinery reading an
event stream that nothing currently fills. This is the single biggest
finding and the true precondition for both effort buckets (§4.1).

### 2.3 Piece 3 — the two MISSING sub-gaps

**(a) Oldest-first drawdown — not enforced.**
`record_free_bet_deployment` (`fb_deployment.py:82-169`) iterates
`consumed_credit_event_ids` in the **operator-supplied order** (`:126`) —
no FIFO/oldest-first sort. The inventory it draws from is sorted
**earliest-expiry-first**, not oldest-credited-first
(`promo_derivations.py:171,231-237`). So neither the deploy path nor the
inventory implements the §2 "oldest unspent free bet first" rule.

**(b) Automatic cycle/parent attribution at commit — not wired.**
At bet-log, `cycle_id = body.cycle_id or str(uuid4())`
(`racing.py:892`) — a fresh cycle when the UI sends none, which it does
not (records-look Finding 2). The deploy event's `correlation_id` is set
to the **deployed bet's own** cycle (`racing.py:935`,
`_safe_uuid(result.bet_record.cycle_id)`), **not** the qualifier's. The
qualifier is reachable in principle — each consumed credit carries
`triggering_bet_id` (`domain/promos:314`) — but `log_bet` never reads it
to derive the cycle. **The exact missing propagation point is
`racing.py` `log_bet` (`racing.py:853-911`):** it would need to resolve
the oldest consumed credit → its `triggering_bet_id` → that qualifier's
`cycle_id`, and pass that as the deployed bet's `cycle_id` instead of
minting a fresh one.

### 2.4 Piece 5 — deploy surface detail

`LogBetPanel.tsx` has an `isFreeBet` toggle (`:82,327`) and, when on,
renders the inventory as a **per-credit checkbox list keyed on
`credit_event_id`** (`:410-423`, `toggleFb` / `selectedFb`), posting
`consumed_credit_event_ids: Array.from(selectedFb)` (`:217`). So it draws
from the pool inventory (good) but the operator **selects individual free
bets** — it is not an amount-driven automatic pool draw. Matches the
brief's expectation. (Contract types in `api/racing.ts:137,156,228,230`.)

---

## 3 — (intentionally folded into §2) 

*Section retained for the brief's numbering; pool detail is in §2.*

---

## 4 — Effort estimate (brief §5.3)

> Sizing only — no code written. Confidence stated per bucket. **Both
> buckets share a hidden prerequisite (§4.1); read it before the bucket
> sizes.**

### 4.1 Prerequisite ("Bucket 0") — a credit-write surface

Neither bucket is reachable until *something* writes `free_bet_credited`
events in production (§2.2). The brief's Bucket A explicitly assumes "the
qualifier's credit already exists in the tool" — today nothing makes that
true outside tests. This is flagged as a finding, not sized as a decision
(per the brief, sequencing is Chat's call), but it gates ordering: a
credit-write path (operator-entry and/or settlement-cascade) must precede
Bucket A having any effect. **Scale of the prerequisite alone: M** (one
event-write call + an operator entry surface; storage/payload already
exist). Confidence: medium.

### 4.2 Bucket A — clean cycle attribution

Wire a deployed free bet to inherit its qualifier's cycle (oldest-first),
assuming the credit exists.

- **Effort:** **S–M**, ~1 session (after Bucket 0).
- **Files that would change:**
  - `ui/api/routers/racing.py` — `log_bet` (`:853-911`): derive the
    deployed bet's `cycle_id` from the oldest consumed credit's
    `triggering_bet_id` → qualifier `cycle_id`, instead of `uuid4()`
    (`:892`).
  - `workflows/promos/v1/fb_deployment.py` — order
    `consumed_credit_event_ids` oldest-first (or have the route resolve
    the oldest) to make attribution deterministic.
  - `ui/web/src/components/LogBetPanel.tsx` + `api/racing.ts` — only if
    the cycle is chosen client-side; the cleaner path keeps it
    server-derived and needs no UI change.
  - **No storage change** — `cycle_id` already exists and is NOT NULL
    (records-look Finding 1; `store/schema/bets.py:21`).
- **Risk:** moderate. It reaches the **bet-record write** (`cycle_id` is
  set at record creation in `log_bet`). It does *not* touch the
  settlement path. `cycle_id` is an existing first-class field, so the
  blast radius is the attribution value, not the write mechanics —
  contain with the existing idempotency/duplicate guard
  (`racing.py:877-890`).
- **Confidence:** medium-high. The mechanism is well understood and the
  storage is ready; the only soft spot is choosing *which* credit defines
  the cycle when multiple are consumed (resolved by the oldest-first rule).

### 4.3 Bucket B — timing-tolerance reconciliation

Allow a deploy *before* the credit exists in-tool: provisional pool
(can read negative), drawdown recorded, back-attribution once the
qualifier settles and the credit lands.

- **Effort:** **M–L**, ~2–3 sessions.
- **Files that would change:**
  - `workflows/promos/v1/fb_deployment.py` — today it **hard-requires**
    the credit to exist and raises `FreeBetDeploymentError` if not
    (`:127-139`). Bucket B must relax this to record a drawdown with no
    credit to supersede yet.
  - `workflows/promos/v1/promo_derivations.py` /
    `workflows/balances/v1/balance_derivation.py` — the pool is a sum of
    **positive** available credits (`total_face_value`); it cannot
    represent a negative/provisional balance today
    (`balance_derivation.py:401`). Needs a representation for "drawn but
    not yet credited."
  - A back-attribution hook — most naturally fired when the qualifier
    settles in-tool, i.e. near `settlement.py` won/voided branches or the
    manual-resolve path. **This is the part that reaches the
    settlement path** and is the highest-risk element.
- **Reuse available (meaningful):**
  - **Bet-side provisional machinery** is proven: `SettlementState.PROVISIONAL`
    + the burst-review queue (`ui/api/routers/provisional.py`) +
    `apply_manual_operator_resolution` (`settlement.py:1128`) is exactly
    the "hold provisional, resolve/attribute later" shape Bucket B needs,
    re-applied to credits.
  - **Promo-side status already models the lifecycle:** `CreditStatus`
    has `PROVISIONAL | FINALISED | REJECTED` (`domain/promos:144-149`)
    and `FreeBetCreditedPayload.status` carries it (`:313`). A provisional
    credit → finalised-on-settlement transition has schema support
    already — though `compute_free_bet_inventory` does **not** currently
    filter or special-case on `status` (`promo_derivations.py:201-217`),
    so the derivation would need to learn it.
- **Risk:** **HIGH.** Touches the deploy-event write, balance derivation,
  *and* a back-attribution trigger that lives next to settlement — the
  bet-safety-sensitive zone the brief rings off. Negative-balance
  semantics also ripple into any UI reading `free_bet_balance`.
- **Confidence:** lower (medium-low). The reuse lowers the unknowns but
  the back-attribution trigger and negative-pool representation are
  genuinely new and settlement-adjacent.

### 4.4 Dependencies / ordering

`Bucket 0 (credit-write) → Bucket A (cycle attribution) → Bucket B
(timing tolerance)`. A is meaningless without 0 (no credit to inherit
from). B subsumes part of 0 (it introduces credits that arrive late) but
is far heavier; doing A first on the simple "credit-already-exists" path
de-risks B. Whether B ships pre-cutover or as its own slice is the
operator's call next session (per brief §10) — this report sizes, it does
not decide.

---

## 5 — Findings / surprises (outside the three questions)

1. **No production credit-creation path at all** (§2.2). The pool is
   drawable but not fillable by the running app. Headline; reframes the
   whole effort as "build the credit-in side," not "wire a link."
2. **`consumed_credit_event_ids` is not stored on the bet row.** There is
   no such column in `bets` (`store/schema/bets.py:17-47`); the field only
   drives deploy-event writes at POST time (`racing.py:929-935`). The
   bet↔credit link lives entirely in `promo_events` (deploy event's
   `source_credit_event_ids` + `correlation_id`), not on the bet record.
3. **Whole-credit consumption only.** `record_free_bet_deployment` draws
   each credit's **full** `amount` (`fb_deployment.py:145-151`, docstring
   `:101-103`); partial draw-down is explicitly deferred. The §2 model's
   "draw the balance down" by an arbitrary amount is therefore not
   supported — deploys consume entire credits.
4. **Inventory ordering is earliest-expiry, not oldest-credited**
   (`promo_derivations.py:171,231-237`). Semantic mismatch with the §2
   "oldest-first" rule even before attribution is wired — worth an
   explicit decision (expiry-first is arguably better operationally, but
   it is *not* what the locked model says).
5. **`deploying_bet_id` soft-coupling.** `_coerce_uuid`
   (`fb_deployment.py:59-79`) falls back to a *fresh* UUID for any bet id
   not matching the `bet-<uuid>` convention, so the deploy event's
   `deploying_bet_id` is not guaranteed to be the real bet's UUID in that
   edge case. Minor data-integrity note for any future bet↔deploy join.
6. **Cascade-credit trigger is a named-but-deferred successor**
   (`domain/promos:305-307`) — the intended home for settlement-driven
   auto-crediting already has a documented landing spot, which lowers
   Bucket 0's design risk.

---

## 6 — Self-assessment

- **Coverage:** all three brief areas answered with file/line evidence.
  Every BUILT/PARTIAL/MISSING call in §2.1 carries a citation; both effort
  buckets carry a scale + confidence, plus a flagged prerequisite.
- **Confidence:** high on §5.1 (settlement does nothing to the promo
  layer — backed by a whole-file grep plus the write-list at
  `settlement.py:1193-1210`/`852-906`). High on the §5.2 verdicts. Medium
  on §5.3 sizing; lower on Bucket B specifically, as noted.
- **Left partial / not traced exhaustively:** I did not read
  `promo_store_adapter.py` in full (785 lines) — I confirmed its
  `append_event` is called only by `fb_deployment` and relied on its
  serialization role; a generic promo-event ingest route was ruled out by
  searching `ui/api/routers/` directly, but I did not exhaustively prove
  no other module constructs+persists a credit (the greps are strong but
  not a formal proof). I did not open `orchestrator.py` (1,547 lines) end
  to end — I confirmed via grep that its only free-bet handling is the
  `is_free_bet` / `free_bet_conversion_rate` placement flags
  (`orchestrator.py:414,490,1382-1468`), not crediting.
- **The brief's "report partial and stop" clause was not needed** — the
  map completed in one session.
- **Length:** ~300 lines, within the 250–450 target.
- **Repo integrity:** no file in `bethub-v3` was created, edited, moved,
  or deleted; no git operation was run; the dirty working tree was left
  untouched. The only file written is this report, in the rebuild folder.

### Open questions for Chat triage (not chased into code)

- Q1. Where should credit creation live — operator manual entry, a
  settlement-cascade trigger, or both? (Determines whether Bucket 0 is a
  UI slice, a settlement slice, or both.)
- Q2. Oldest-credited vs earliest-expiry as the drawdown order — confirm
  which the locked model intends now that the code does expiry-first.
- Q3. Is whole-credit-only consumption acceptable for cutover, or is
  partial draw-down in scope? (Affects Bucket A/B shape.)
