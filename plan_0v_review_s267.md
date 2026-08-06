# ADVERSARIAL REVIEW — plan_0v_split_credit_s267.md (S267, 5 Aug 2026)

## VERDICT: NO-GO

The plan's central claim — *"a caller and one new composite door, not new
money logic"* — is false in three independent ways. The build as written
cannot be transactional, and on the only live credit in the store today it
would silently close a play as a loss and orphan the money.

## BLOCKING

**B1. "Revoke + N re-issues in ONE transaction" is not buildable from the
cited doors.** Every promo event write commits by itself
(`store/repositories/promos.py:271`). `record_account_credit` constructs a
fresh `PromoStoreAdapter` per call (`workflows/promos/v1/fb_credit.py:460`)
whose repository `__init__` runs `apply_migrations`
(`store/repositories/promos.py:210`), which commits. The existing
multi-write money module states the rule: *"No committing
repo/adapter/workflow object is ever constructed on a step's transaction
connection"* (`ops/correct_promo_chain.py:29-34`). So a split is N+1
separately-committed writes. If re-issue 3 of 5 fails, the $150 revoke has
already landed and $90 is destroyed with no marker and no resume path.
**V3 ("assert inside the transaction and roll back") cannot exist as
described.** The sanctioned pattern is the durable composition journal
(`store/schema/composition_journal.py:56`) with sweep (f) alarming on
unfinished compositions (`ops/settlement_review.py:580,697`) — unmentioned.

**B2. Same-key idempotency would silently swallow re-issues 2..N.**
`record_account_credit`'s replay guard returns the first credit in the
key's correlation group as `already_banked` without writing
(`fb_credit.py:463-472`). One key per submission ⇒ $150 revoked, $30
banked, success returned.

**B3. Splitting a TRIGGERED credit destroys cycle lineage and books the
play as a loss.**
- Freebie credits are forbidden from carrying trigger ids
  (`domain/promos/__init__.py:354-360`); `record_account_credit` hard-codes
  `FREEBIE` with no trigger fields (`fb_credit.py:482-486`).
- Cycle membership re-derives through `triggering_bet_id` → qualifier's
  `cycle_id` (`fb_credit.py:521-569`; `workflows/bet_entry/v1/cycle_audit.py:22-33`).
  With no trigger, a fresh cycle is classified CORRECT — **the audit still
  reports 308/308 clean** while the qualifier's stake and the bonus's
  return sit in different plays.
- The revoke terminal closes the qualifier's cycle
  (`cycle_audit.py:1286-1292`, marker `CLOSED_MARKER_REVOKED_UNUSED` at
  `:1136`), consumed by `derive_cycle_ledger` (`:1373-1425`). The play
  reads **"bonus revoked unused"** and `all_in_net` books the loss.
- The N parts belong to no play (`cycle_audit.py:1093`, `:1269`).
- The qualifier's BetLog row loses its credit
  (`ui/api/routers/bets.py:1094`) — `insurance_credit_amount` → `None`.
- Nothing catches it: coherence sweep (c) exempts revoked terminals
  (`ops/settlement_review.py:661-665`).

**B4. The lineage-preserving alternative is forbidden by a locked
invariant.** `record_correction_credit` is the only writer that copies
`credit_source`/trigger ids/expiry forward
(`workflows/promos/v1/fb_correction.py:222-227`), but ◆pin 4 enforces
**"at most one live credit per qualifier, ever"** (`:36-42`, enforced
`:334-346`). A triggered split into N live credits violates it and the
guard refuses the 2nd re-issue. **There is no sanctioned write shape for
what the plan proposes.** Changing that invariant is an architecture
decision, not a build task.

**B5. The only live splittable credit today is exactly the dangerous
class, and the cited precedent never tested it.** Live unspent FB credit
`db668ddc`, $24.00, `credit_source=triggered`, qualifier `6edbfcfb`. The
31 Jul stopgap was `54905e90` $150 **`credit_source=freebie`** ("Sign up
bonus") → 5 × $30 freebie. Freebie → freebie loses nothing because there
was no cycle, no qualifier and no P&L attribution to lose. **The stopgap
validates only the goodwill case; the plan generalises it to the case it
never touched.**

## NON-BLOCKING

- **Expiry silently dropped.** `compute_free_bet_inventory` filters/sorts
  on `face_value_expiry` (`promo_derivations.py:232-256`); the plan never
  carries it forward. Parts become never-expiring and the cross-foot at
  t=0 still passes. TAB = 7 days by design.
- **Provenance label loss.** Parts lose `source_promo_instance_id` /
  `source_template_id`, read as "goodwill" in the FB picker, and move into
  the daily check's GOODWILL CREDITS section (`ops/settlement_review.py:1089`).
- **No way back.** A split cannot be undone: original revoked, correction
  door refuses non-revoked terminals, re-crediting after revoke is a
  locked non-path (`fb_revoke.py:13-16`).
- Plan premise 1 **is correct**: `fb_deployment.py:216-222` records
  `amount_drawn` but `:243` supersedes the whole credit — $30 against $150
  does destroy $120. The interlock also already exists
  (`fb_revoke.py:81-90` + DB backstop `store/repositories/promos.py:262-268`).
  The problem is real; the fix shape is wrong.

## FACTUALLY WRONG IN THE PLAN

| Plan says | Reality |
|---|---|
| Revoke door "refuses if not a bonus credit"; acceptance 5 "Undo still refuses on cash" | **No such refusal.** `ui/api/routers/promos.py:1349-1357` routes `promo_cash_credited` to `record_promo_cash_reject`; 1b deliberately made the door cover both kinds (`:1339-1341`). UI already offers Undo on cash (`BetLog.tsx:801`). Acceptance 5 fails against shipped behaviour. |
| Undo gated on bet-attachment at `BetLog.tsx ~679` | 679 is the unrelated S247 "Re-check from account" block. The gate is `BetLog.tsx:794-803`. |
| "Remove the bet-attachment gate so it renders for account-anchored credits" | Not a removable gate. BetLog renders per-**bet** rows; the id comes from `bet.insurance_credit_event_id` (`ui/api/routers/bets.py:814`). An account-anchored credit has no bet row. Removing the condition yields nothing. |
| "…on Balances as well" | Balances renders aggregates only (`Balances.tsx:326-327`) from `compute_account_at_book_balance`, which returns totals with **no credit ids** (`balance_derivation.py:916-924`). **There is no credit list on Balances to attach a button to.** A new read surface is required. |
| "Both halves already exist as sanctioned doors" | Only for freebie→freebie. For triggered credits the second half does not exist and is affirmatively blocked (B4). |

## MISSING

1. **The crux decision the plan never names:** triggered vs freebie split.
2. Journalled composition + resume (`ops/correct_promo_chain.py`,
   `store/schema/composition_journal.py`) + sweep (f) coverage.
3. **Cycle-accounting acceptance test** — `ops.cycle_audit` before/after on
   the real triggered case. The current acceptance list passes on a store
   where the play has been silently closed as a loss.
4. Cycle-ledger before/after: `all_in_net`, `close_date`, `closed_marker`.
5. BetLog regression: the qualifier row must still show its credit.
6. Expiry carry-forward; per-part idempotency keys.
7. A reversal path for a split gone wrong.

**Acceptance sufficiency:** No. Criteria 1–7 all pass on a store where the
play has been silently closed as "bonus revoked unused", the money
orphaned into goodwill, and the qualifier's BetLog row stripped.

**"One sitting":** not credible. Journalled composition runner + a new
per-account credit read surface + new UI + a locked-invariant decision
that belongs to the operator.

**Build/deploy today:** **No.** Live race day; the store is live; the only
live credit that could exercise the feature is the triggered one; anything
merged rides tomorrow's 04:40 window. Item is operator-flagged "explicitly
NOT urgent" (`worklist.md:96`).

**Recommended next step:** re-scope to the *goodwill/freebie* split only —
the case the 31 Jul stopgap genuinely proved — and put the triggered case
to the operator as a design question ("can one qualifier hold five live
bonuses?"), since answering yes rewrites a locked invariant.
