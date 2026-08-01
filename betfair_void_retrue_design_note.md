# Betfair void gap — re-true from the account (design note, S246)

**Status: WALKTHROUGH COMPLETE S247 (Mon 20 Jul, evening) — design
LOCKED, nothing built yet. Build authorized AFTER the race-day
live-proof.** Worklist #1. Claims code-verified at HEAD `a195cf2`
(annex below).

**Operator decisions (S247):**
- **D1 = attended tap.** Nothing fires by itself; revisit automating
  after cutover mileage.
- **D2 = before/after confirm.** The confirm shows the row's P&L
  before and after in plain money, and notes the cycle's net will
  change, before the tap.
- **D3 = build after the race-day live-proof.** Stack stays frozen for
  its first real outing; the build is ~one sitting from this note
  (endpoint + reused VOIDED cleared-orders read + system-sourced audit
  write + three red-before tests + UI tap; constraints in annex items
  4–8).

## The gap (one paragraph, from the S246 adversarial review)

If Betfair voids a market AFTER the tool has settled one of your lays,
Betfair refunds your real account — but the tool's row keeps its wrong
verdict forever. No door touches Betfair bets (by design: never
hand-verdict money the account already decided), the worker never
revisits settled bets, and your derived Betfair balance drifts from the
real one permanently. The new watchdog flags it loudly and calls it an
expected discrepancy — but "expected" shouldn't mean "permanent".

## The fix in one sentence

When the watchdog flags a settled Betfair bet, the tool asks **your
Betfair account** ("cleared orders, status VOIDED" — an API read that
already exists in the client from the lapsed-orders work) whether
Betfair itself voided that bet — and only if the account says yes, the
tool re-trues the row to void. The verdict source is the account,
never a human keyboard: the hands-off rule stays absolute.

## How it would work

1. The hourly watchdog flags a settled Betfair bet (already built).
2. **You tap "Re-check from account"** on that flag (BetLog row / the
   daily check names it). Attended — nothing fires by itself.
3. The tool reads YOUR account's cleared orders for that exact bet id
   with the VOIDED filter. Three honest outcomes:
   - **Account says voided** → the row flips to void, with a
     system-stamped reason (`exchange_account_void`) and an audit row —
     same trail shape as the re-class door, but the source recorded as
     the account read, not an operator verdict. Balances re-derive true.
   - **Account says settled (not voided)** → nothing changes; the flag
     is marked checked ("account confirms the verdict") — covers a
     Betfair market read glitch.
   - **Can't read** → nothing changes, plainly said, try again later.
     A failed read NEVER flips anything (the detector's own rule).
4. The daily check stops listing a flag once the account has answered,
   instead of repeating "expected discrepancy" forever.

## Fences (proposed)

- Only reachable FROM a watchdog flag — this is not a general door.
- Only flips TO void, only when the account's own record says VOIDED
  for that bet id. No other transition, no operator-typed state.
- Hand-logged Betfair bets (no Betfair bet id — none exist today) can't
  be account-read → they stay flagged for us to look at together.
- Red-before tests on all three outcomes; account-read mocked in tests,
  live-proven on the real API before trust (S189 as always).

## Decisions for the walkthrough

- **D1 — Attended tap (recommended) or automatic?** Automatic would fix
  the row within the hour with no action from you — but it's the first
  system write to a settled bet's verdict, and pre-cutover the
  attended-only habit has served us. Recommend: attended now,
  revisit automating after cutover mileage.
- **D2 — What happens to the money display?** A voided lay returns your
  liability; the row's P&L goes to $0.00 from whatever it was. The
  cycle containing it will change its net. Proposed: the confirm shows
  the before/after in plain money before you tap.
- **D3 — Build timing.** Small build (~one sitting: one endpoint, one
  account read reused, one audit write, three tests + UI tap). Options:
  fold into the next build session, or hold until after tomorrow's
  race-day live-proof so the stack stays frozen for its first real
  outing. Recommend: hold until after the live-proof.

## Verification annex (S247, code read at HEAD `a195cf2`)

Every operative claim above checked against the code. All hold.

1. **Account read exists.** `clients/betfair_client/v1/cleared_orders.py`
   — `list_cleared_orders(rest_client, bet_status=..., bet_id=?)`
   (`:124`); `ClearedBetStatus` includes `VOIDED` (`:42`). The record
   already parses `profit`, `bet_outcome`, `settled_date` (`:63-66`) —
   parsed today but consumed nowhere. "Cleared orders never source
   verdicts" confirmed: no code path maps them onto `settlement_state`;
   reconciliation reads only `matched_size`/`average_matched_price`
   (`workflows/bet_entry/v1/reconciliation.py:295-326`).
2. **The flag surface exists and already special-cases Betfair.**
   `workflows/bet_entry/v1/post_settlement_void.py` —
   `run_post_settlement_void_detection` (`:140`), read-only, hourly via
   `ui/api/settlement_worker.py:183`, flags `market_now_voided` /
   `settled_runner_now_removed` over SETTLED_WON/SETTLED_LOST bets
   placed in the last 24h (500-candidate cap, truncation honest). The
   Betfair branch (`:271-283`) currently renders "expected discrepancy —
   verify the real account"; the daily-check WATCH parses those log
   lines (`ops/settlement_review.py:497`). This fix upgrades that
   acceptance into a correction — detection is NOT new build.
3. **"Balances re-derive true" is literal.** There is no settled-amount
   column; money is derived on read
   (`workflows/balances/v1/balance_derivation.py:190`, lay branch
   `:223-245`: voided lay ⇒ liability returned). The re-true corrects
   `settlement_state` (+ counts) and emits an audit event — no money
   column exists to rewrite.
4. **Write path fence (build-brief constraint).** The operator doors'
   Betfair refusals (`ui/api/routers/bets.py:1116`, `:1320`, both 422)
   must stay untouched. The SYSTEM path writes through storage
   (`update_settlement_state`) + an append-only mutation event with
   `source=system` (`domain/bet_mutations/__init__.py:97`, supersede
   semantics `:346`) — never through `/settle` or `/reclass`. Event
   type: reuse `BET_RECLASSED` with `source=system` (no CHECK rebuild)
   or a new type (one-time CHECK rebuild, B2 pattern exists) — build
   brief decides, walkthrough doesn't need it.
5. **Consistency hook.** The worker's own PENDING→VOIDED transition
   auto-restores deployed free-bet credits
   (`settlement.py:1192`, called only at `:1383`). A re-true flip to
   VOIDED should run the same restore hook — normally vacuous for a
   Betfair lay (FBs deploy on soft-book backs) but keeps "VOIDED means
   the same thing everywhere" true, and it is already idempotent via
   supersession.
6. **Known inherited limit.** The detector only scans bets placed in
   the last 24h (worklist watch item #3). A re-true reachable only FROM
   a flag inherits that window. Fine for now — the window call is
   already queued post-mileage; the note's fence "only reachable from a
   watchdog flag" should be read as inheriting whatever window the
   detector has.
7. **Terminology guard.** `FINAL_PARTIAL`/`FAILED` are `MatchStatus`
   (how the lay matched), not settlement verdicts. The void gap is
   purely about the `SettlementState` terminal trio
   (SETTLED_WON/SETTLED_LOST/VOIDED, `domain/bets/__init__.py:107`).
   Docs and tests must keep the axes separate.
8. **Park valve confirmed wrong tool** (as the note assumes): terminal→
   PROVISIONAL would hand the bet to an operator forbidden from
   verdicting it; `post_settlement_void.py:14-16` already rules
   re-parking out of scope. (`ProvisionalTriggerSource
   .POST_SETTLEMENT_VOID` exists with zero firing sites — the build may
   delete or wire it; brief decides.)
