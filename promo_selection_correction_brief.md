# Promo-selection correction (wrong template picked at log time) — brief

Status: DRAFT → adversarial planning review → build → post-execution
review. Operator-commissioned S259 (30 Jul, race day) after a live
instance. Money path: red-before tests, backup taken
(`data/bethub.db.bak-s259-pre-cashcorrection-20260730-135352`).

## The live instance

Sarie/TAB, Albion Park R2 #1 My Names Bruce, $10 @ 4.40, Safety Net,
settled_lost, insurance triggered (2nd). Bet
`bet-bc1e2dd8-976b-533b-be8f-ff5a70e628ba` was logged against template
`a75946dd` "Ins $25 Cash 2nd" (return_type=cash) but the real promo is
`197815c8` "Ins $25 FB 2nd" (return_type=free_bet). Both templates are
CORRECT in the catalogue — the operator picked the wrong one at log
time. Consequence: `promo_cash_credited` $10.00 (event
`a4a92ee0-1091-4d88-afc5-e1c7f0a3a23b`) instead of `free_bet_credited`
$10.00 → tool overstates TAB cash by $10 and understates FB inventory
by $10. Second promo mis-pick in 3 days (S258 swapped two
bonus-winnings→Boosted Odds by hand-fix).

## Why no existing door fixes it (all three verified in code)

1. `fb_revoke.record_free_bet_revoke` refuses anything that is not
   `free_bet_credited` — a cash credit cannot be revoked at all.
2. `balance_derivation` sums EVERY finalised `promo_cash_credited`
   with no supersession check — so even a revoke would not remove the
   $10 from cash.
3. Re-crediting is a locked contract (`fb_credit.find_existing_credit`:
   "a REVOKED credit still answers already credited"); the sanctioned
   replacement path is `fb_correction.record_correction_credit`, which
   (a) refuses cash chains (v1 scope) and (b) copies the replaced
   credit's payload verbatim — right for an ACCOUNT move, wrong for a
   re-TYPE.

## Build

New ops verb + CLI `ops.correct_promo_selection` — "the logged promo
was the wrong template; re-point the bet and re-issue its credit under
the correct one". Also the engine a future BetLog "change promo"
button would call (operator's parked idea; this is its second sighting).

ONE atomic transaction (BEGIN IMMEDIATE), append-only, in order:
1. **Pre-flight refusals** (never guess):
   - bet must exist, carry a promo, and be settled (terminal);
   - target template must exist and be a DIFFERENT template;
   - every existing credit for the qualifier must be UNSPENT: refuse if
     any `free_bet_deployed` names any of its credits (an already-spent
     credit needs the spend corrected first — fb_restore's job);
   - refuse if any credit chain already terminates in a revoke without
     a replacement (ambiguous prior correction);
   - settlement-state guard asserted inside the lock (S254 pattern).
2. **Revoke** the existing credit(s) — extend `record_free_bet_revoke`
   to accept `promo_cash_credited` as well (it is a credit; refusing it
   was an oversight, not a rule). Revoke event type stays
   `free_bet_revoked` (no cash-revoke type exists and the schema CHECK
   is out of scope here — the `supersedes_event_id` link carries the
   meaning; recorded in the report).
3. **Re-point the bet**: `bets.promo_template_id` → target, written
   through the existing bet-mutation audit trail (`bet_mutation_events`)
   so the change is not a silent column edit.
4. **Re-issue the credit** computed FROM the target template
   (stake × return_pct, capped, template's return_type) —
   `free_bet_credited` or `promo_cash_credited` as the template says,
   `credit_source='correction'`, payload `reference` = the revoked
   credit's event id, notes = operator reason + correction marker.
   Deliberately bypasses `find_existing_credit` (it is a correction,
   the S254 precedent for a sanctioned replacement).

Enabling fix (required, and a real bug on its own):
5. **`balance_derivation`**: a `promo_cash_credited` superseded by a
   revoke must NOT count toward cash. Mirrors how FB inventory already
   honours supersession.

Explicitly OUT: the BetLog button (UI build, later — this verb is its
engine); changing `promo_ev_at_log` (historical stamp, stays);
schema/enum change for a cash-revoke event type; multi-bet batches.

## Tests (red-before at every layer)

- revoke accepts a cash credit; still refuses a non-credit; still
  refuses an already-superseded credit.
- derivation: a revoked cash credit drops out of cash balance; an
  un-revoked one still counts (regression).
- verb: cash→FB re-type moves $10 from cash to FB inventory and leaves
  the bet on the new template; FB→cash the other way; refusals
  (spent credit, missing template, same template, unsettled bet,
  settlement changed mid-flight); idempotency (re-run refuses, no
  double credit); atomicity (injected failure rolls the whole thing
  back — no half-corrected state).
- full suites: pytest + vitest green.

## Acceptance on the live instance

After the run: TAB/Sarie cash −$10, FB inventory +$10 ($10 free bet
listed), BetLog row shows "Ins $25 FB 2nd", the revoked cash credit
still visible in history as superseded, daily money check clean.

## Post-execution review + LIVE RUN (30 Jul, S259)

Review verdict FIX FIRST (2 items, both applied before the run):
- **F1** the docstring claimed a `bet_edited` audit row the code never
  wrote. FIXED properly: the audit row is now raw-inserted in the SAME
  transaction and fails CLOSED (reassign-door contract — a missing
  bet_mutations migration refuses the whole correction; regression test
  proves it).
- **F2** the two cash guards (`fb_correction`, `correct_promo_chain`)
  excluded superseded cash credits but not the REJECTED terminal this
  verb writes, so a corrected bet would be locked out of the
  wrong-account doors forever. FIXED with a status filter on both, plus
  the verb's own live-credit query (which also makes a SECOND
  correction possible — review finding 7).
Review also verified by rehearsal on a byte-exact snapshot: atomicity
real (traced statements: PRAGMA → BEGIN IMMEDIATE → 2 re-asserts →
INSERT/UPDATE/INSERT → COMMIT, no adapter, no intermediate commit),
crash-safe (hard kill mid-txn leaves the store untouched), door
refactor behaviour-identical, money-read lockstep holds
(self_check 0.00 before AND after).

**LIVE RUN APPLIED 30 Jul ~15:0x ACST** (backup
`bethub.db.bak-s259-pre-cashcorrection-20260730-135352`):
cancelled `a4a92ee0…` via rejected-cash terminal `3f56c253…`;
re-issued `3bc052e6…` free_bet_credited $10.00; bet re-pointed to
`197815c8` (Ins $25 FB 2nd); audit `bet_edited` written.
**Sarie/TAB cash 1163.90 → 1153.90; FB inventory 0 → $10.00; live
cash credits 0; daily money check clean (ledger coherence 0 lines,
Betfair watchdog matches).** Acceptance met in full.

Carried to the worklist (review findings 3-5, before this verb is used
for a CROSS-KIND re-type or wired to a button): settlement-state guard
under the lock; `face_value_expiry` ignores the template's
`fb_expiry_days` (harmless today — all templates NULL); the verb does
not re-apply the door's kind gates (settled_won for bonus-winnings,
LAY refusal, dead-heat/removed-runner, small-field void).
