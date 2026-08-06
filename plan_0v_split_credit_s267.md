# PLAN — 0v: "Split this credit" + undo for account-anchored credits

**Status:** PLAN, for adversarial review. Nothing built.
**Session:** S267, 5 Aug 2026. Operator asked for the remaining builds today.

## The problem, in money terms

Books routinely issue one bonus as **N × $X** (Sarie/Ladbrokes: $150 as
5 × $30). BetHub can only record the lump. Two consequences:

1. **Deploying against a lump destroys inventory.** A deploy supersedes
   the WHOLE credit, so putting $30 against a $150 lump silently
   destroys $120 of free-bet stock and breaks the ledger cross-foot the
   S260 audit certified.
2. **Account-anchored credits have no undo in the UI at all.** The 0q
   *Undo credit…* action is gated on the credit being attached to a BET
   (`BetLog.tsx` ~line 679). Goodwill/deposit credits are anchored to an
   ACCOUNT, so they never render the control — even though the server
   door already accepts them.

A manual stopgap was run 31 Jul under operator authorisation (Sarie
$150 → 5 × $30, verified `free_bet_balance=150.00`, `free_bet_count=5`,
cash untouched). That is exactly the class the standing self-serve rule
says must become a button rather than a Claude hand-fix.

## What already exists (reuse, do not rebuild)

- `POST /api/v1/promos/credit-revocations` — supersedes a bonus credit
  with a revoke. **Refuses if already spent, already revoked, or not a
  bonus credit.** Append-only. Client wrapper `revokeCredit()` in
  `ui/web/src/api/promos.ts`.
- `POST /api/v1/promos/account-credits` — issues an account-anchored
  credit. Client wrapper exists.
- `compute_account_at_book_balance` — the verifier the 31 Jul stopgap
  was proven against (`free_bet_balance`, `free_bet_count`).

So both halves of a split already exist as sanctioned doors. **This
build is a caller and one new composite door, not new money logic.**

## The build

### V1 — surface the existing undo for account-anchored credits
Remove the bet-attachment gate on *Undo credit…* so it renders for
account-anchored credits too, on **Balances** as well as BetLog. No
server change: the door already accepts them. The server keeps every
refusal (spent / revoked / not-bonus) — the UI must surface those
verbatim, not pre-judge them.

### V2 — "Split this credit"
On a **live, wholly unspent** bonus credit, offer *Split this credit…*:
operator enters N (count) and the tool derives X = total / N, or enters
X and it derives N. Preview shows `$150 → 5 × $30` and the resulting
free-bet count/balance BEFORE anything is written.

Server: one new door `POST /api/v1/promos/credit-splits` that performs
**revoke + N re-issues in ONE transaction**, reusing the existing revoke
and account-credit paths internally. Refusals, all server-side:
- anything already deployed against the credit → refuse (this is the
  interlock that protects the $120)
- credit already revoked/superseded → refuse
- not a bonus credit → refuse (cash is a different shape; the
  promo-selection correction owns that)
- `N × X ≠ total` to the cent → refuse. No rounding, no remainder
  credit. If it does not divide exactly, the operator picks different
  numbers.
- N outside 2..20 → refuse (a typo'd N of 500 must not mint 500 rows)

### V3 — the cross-foot must not move
`free_bet_balance` before == after; `free_bet_count` goes 1 → N; cash
untouched. Assert this **inside the transaction** and roll back if it
moves. This is the single most important acceptance test: it is the
invariant the S260 ledger audit certified.

## Risk register

| risk | mitigation |
|---|---|
| Split destroys inventory if it fires on a partly-deployed credit | server-side refusal; the check lives in the door, not the UI |
| Undo becomes reachable on cash credits | keep the server's not-bonus refusal; the UI only stops hiding the button |
| Money moves during a split | balance/count/cash asserted inside the transaction, rollback on drift |
| Operator splits into the wrong N | preview before write, exact-division refusal, N bounded |
| Race-day exposure | this touches the credit ledger — **do not deploy mid-race-day** |

## Acceptance

1. Cross-foot: `free_bet_balance` identical before/after; count 1 → N;
   cash unchanged — asserted on a real credit in a DB copy.
2. Split refuses on a partly-deployed credit (constructed case).
3. Split refuses on non-exact division.
4. Undo renders and works for an account-anchored credit on both
   Balances and BetLog.
5. Undo still refuses (server verbatim) on spent / revoked / cash.
6. `uv run pytest` green; `npm run build` green (the frontend gate).
7. Backup taken before any live apply, named to the session.

## Explicitly out of scope

- Cash credits (promo-selection correction owns those).
- Merging credits back together (no operator demand).
- Changing the revoke door's own rules.

## Cost estimate

Server door + UI action + tests: **one sitting**. Lower risk than 0m —
it composes two already-live doors rather than repairing history.
