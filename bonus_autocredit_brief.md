# 1b — Bonus-winnings auto-calculation: build brief (S263, 1 Aug 2026)

Operator commission, verbatim: "This should all be automatically
calculated. It requires a permanent fix, not patches."

Status: PLANNED (sub-agent, S263 late eve) → adversarial review →
build. Plan produced with zero operator decisions required.

## The incident, corrected record

The five Bet365 bonus credits banked 23:07 1 Aug were NOT hand-typed —
all five carry credit_source='triggered': the operator tapped the
Burst Review credit-gaps "bank the credit" button five times and the
SERVER computed every amount. The defect is in
`workflows/promos/v1/credit_terms.py:52`: rounding is hardcoded
`whole_dollar` for every bonus_winnings template (TAB's rule,
ROUND_CEILING, calibrated on S244 $12.50→$13 and S250 Krasina
$11.25→$12). Applied to Bet365 (which pays exact cents, half-up) it
produced $57/$11/$26/$23 for true $56.25/$10.63/$25.50/$22.50 — the
$2.12 overstatement. `return_pct=0.25` was ALREADY stored on template
`a3d997f8-…` since 6 Jul and EV already values the promo at 25% — the
missing term is ROUNDING, not the percentage.

## Build shape (see sections below for detail)

(a) New per-template term `credit_rounding` ('cents' | 'whole_dollar',
    NULL = today's whole_dollar) — schema/domain/repo/adapter/door/
    gap-detector plumbing + a plain-language radio on the new-promo
    card. Bet365's template set to 'cents' as step 0 of the correction.
(b) BetLog manual-credit control prefills the computed amount
    (single-source input, S247 5b pattern, drift confirm on edit; kind
    defaults from the template's return_type).
(c) Auto-trigger on soft-settle WON (server-side, in the settle door +
    log-past-bet won-at-entry): shared evaluator extracted from the
    credit-in door's winnings arm; source='system'; non-fatal on
    failure (credit-gaps detector is the backstop); Burst Review
    "Banked automatically on Won" lane; cash extension of the
    revocation door so auto cash credits are undoable in-app (makes
    the reclass fence's cure message true).
(d) Correction CLI `ops/correct_credit_amount.py` (S259 verb shape:
    dry-run default, backup, one BEGIN IMMEDIATE txn, CAS re-checks,
    rejected-supersession + exact re-issue for the four events;
    acceptance: Tim/Bet365 derived balance = $859.38 + post-23:07
    activity; settlement_review clean).

Excluded: P&L strip relabel (0t-B), historical EV recompute (5e — note
its premise weakened: EV was already 25%), results-log full auto (1a).

## 1. Investigation findings (planner, verified against code + live store)

- Templates live in `promo_template` (catalogue-driven picker via
  GET /v1/promos/catalogue; presets.ts legacy). Additive-column
  migration pattern at `store/schema/promos.py:282-299`. Bets bind via
  `bets.promo_template_id`; the per-book `promo` instance table is
  EMPTY (unused). Template `a3d997f8-95ed-5916-a96d-dc61562c0019`
  "Bonus Winnings (Cash)" kind=bonus_winnings return_type=cash
  return_pct=0.25 cap=NULL, used by 11 bets ALL at Tim/Bet365 (5 won +
  credited, 6 lost — nothing owed). All other bonus_winnings templates
  are TAB-named and TAB-only-used → templates are de facto per-book;
  rounding binds to the template.
- Credit doors: auto `POST /v1/promos/credit-in` (promos.py:236-454;
  winnings arm :309-366 — settled_won ∧ BACK ∧ matched_price ∧ no
  dead-heat/removed; amount via credit_kwargs_for_kind →
  record_free_bet_credit with find_existing_credit idempotency under
  BEGIN IMMEDIATE, fb_credit.py:104-122,153-187). Callers:
  BetLog.tsx:731,760; LogPastBet.tsx:291; RaceActivityBoard.tsx:202;
  BurstReview.tsx:341,353. Manual `POST /v1/promos/manual-credits`
  (promos.py:478-564, operator amount + reason,
  credit_source='operator_manual_amount', listed by settlement_review
  :633-660); UI gate BetLog.tsx:650, form :1352-1399 (kind defaults
  free_bet — hazard). Gap detector `credit_gap.py` `_bonus_expected`
  :130-153 MIRRORS the door's ceiling arithmetic (lockstep required).
- Soft-settle: `POST /v1/bets/{id}/settle` (bets.py:2130-2199,
  _SETTLEABLE_STATES {None,'pending'} :2119); manual create
  settled-at-entry with §6b non-fatal warnings (bets.py:3214-3228);
  reclass fenced by `_linked_promo_blockers` (:2230-2327) — but its
  cure message names credit-revocations which REFUSES cash
  (fb_revoke.py:72-76): cash undo is ops-shell only today.
- Trigger precedent: the composed "Lost — insurance triggered?" tap =
  client-side settle→credit-in sequencing; the writer's idempotency
  guard dedupes. PromoEventSource.SYSTEM exists (domain :94-99, in DB
  CHECK) but record_free_bet_credit hardcodes OPERATOR (:303).
- EV: catalogue → presets.ts:254-276 (×100) → promoSpec.ts:35-55 →
  evEngine.ts:412-444. Already 25%. NO EV change in this build.
- Correction shapes: cash cancel = new promo_cash_credited
  status='rejected' + supersedes_event_id (S130 lock, domain :466-475;
  live precedent a1a86071 ⊃ b6d61729). Copy
  `ops/correct_promo_selection.py`: plan/refuse → backup → one
  BEGIN IMMEDIATE txn, PRAGMA foreign_keys=ON, domain events
  raw-inserted via _promo_event_to_row (no committing adapter — S254
  §3d), CAS under the lock, credit_source copied, reference = old id,
  correlation = qualifier UUID. Read sides supersession-aware in
  lockstep: balance_derivation.py:727-748, cash_flow.py:1013-1023,
  bets.py:832+, settlement_review :472-630;
  uq_promo_events_supersedes = single-supersession backstop.

## 2. File-by-file changes

(a) rounding term:
 1. store/schema/promos.py — _add_column_if_missing promo_template
    credit_rounding TEXT CHECK IN ('cents','whole_dollar'), nullable.
 2. domain/promos/__init__.py PromoTemplate (~:751) + field.
 3. store/repositories/promos.py PromoTemplateRow :75, create_row
    ~:552, _row_to_promo_template_row, update_row ~:601
    (None-keeps-existing).
 4. workflows/promos/v1/promo_store_adapter.py _row_to_template :747 /
    _template_to_row :795.
 5. workflows/promos/v1/credit_terms.py credit_kwargs_for_kind gains
    credit_rounding kw; bonus branch returns it or 'whole_dollar'.
    Callers updated: ui/api/routers/promos.py:361,
    ops/correct_promo_selection.py:231 (+ its template SELECT
    :167-170).
 6. workflows/promos/v1/credit_gap.py _bonus_expected :130 + bonus-arm
    SELECT :199 add the term (cents → 2dp half-up, no ceiling).
 7. ui/api/routers/promos.py PromoCatalogueItem :125 + _to_item :150 +
    create request :806/:835 (bonus_winnings only).
 8. ui/web/src/api/promos.ts types.
 9. ui/web/src/components/TopBar.tsx new-promo card ~:900-966: radio
    "Book rounds the bonus UP to the whole dollar (TAB)" (default) /
    "Book pays exact cents (Bet365)".
10. a3d997f8 → 'cents' happens in the (d) CLI, not code.

(b) computing credit control:
11. ui/web/src/routes/BetLog.tsx manual-credit: prefill computed
    min(matched_stake×(matched_price−1)×return_pct, cap) rounded per
    template term (integer-cents util, half-up; ceiling for
    whole_dollar); kind select defaults from template return_type;
    submit-time drift confirm naming both figures; non-bonus/NULL-pct
    byte-identical.
12. BurstReview "$X owed" fixed by item 6 (re-derives).

(c) auto-trigger + undo + lane:
13. NEW workflows/promos/v1/auto_credit.py — shared evaluator
    extracted from the credit-in winnings arm +
    try_auto_bonus_credit(conn, bet_id) → refusal=silent skip;
    source=SYSTEM.
14. fb_credit.py record_free_bet_credit gains
    source: PromoEventSource = OPERATOR (line 303 uses it) — additive.
15. promos.py credit_in winnings arm delegates to the evaluator
    (refusal wording verbatim; existing tests untouched-green).
16. bets.py settle_bet_endpoint :2135 — after state update, when
    to_state=='settled_won': db_path convention → connection →
    try_auto_bonus_credit → commit; ANY failure = parseable warning,
    settle stands (gap detector = backstop). Response row carries the
    fresh credit marker via _triggered_credits.
17. bets.py create_manual_bet_endpoint — same hook, §6b warnings
    contract.
18. Behaviours: won only; dead-heat/removed/LAY/no-price → skip (stays
    in gaps); duplicate settle 409 pre-hook + already_credited on
    re-invocation; reclass-to-won does NOT auto-fire (attended
    correction; fence + gaps cover); NO retroactive fire.
19. Cash undo: fb_revoke.py new record_promo_cash_reject (rejected-
    supersession composition); promos.py revoke_credit :1131 branches
    FB/cash; BetLog.tsx undoableCredit :693 extends to cash,
    creditIsCash note :1455 retired.
20. NEW GET /v1/promos/auto-credits (7-day window, source='system',
    non-superseded) + BurstReview lane "Banked automatically on Won"
    with plain undo guidance.

Untouched by design: balance_derivation, cash_flow, EV engine, P&L
strip, settlement worker, promo instance table.

## 3. Red-before test plan

credit_terms: cents kwargs (RED: no param). fb_credit: 42.50×0.25
cents → 10.63 (RED: 11.00); whole-dollar Krasina stays green
untouched + NULL-rounding still ceilings. credit-in endpoint: cents
template → "10.63" (RED "11.00"); existing whole-dollar test :318
untouched-green. credit_gap: cents expected "10.63" (RED "11.00").
schema: column added idempotently + CHECK (RED: none). settle
auto-trigger (real sqlite): won → one finalised system/triggered
credit 10.63 + response marker (RED: none); sabotaged hook → 200 +
warning + no credit; non-bonus / lost / void / dead-heat / LAY /
idempotent-second-call; manual-create won-at-entry (RED);
reclass-blocked-then-allowed-after-cash-reject. cash undo door:
rejected supersession + balance drops (RED: 422); already-superseded
refused. auto-credits read: lists system only, window (RED: 404).
ops CLI: dry-run writes nothing (RED: module absent); apply = 8
events + template UPDATE in one txn; sets rounding first; second run
refuses; CAS refusal; finalised sum flips by −2.12; coherence sweeps
clean on corrected fixture. Frontend (vitest + npm run build gate):
prefill 56.25 + kind cash (RED: empty + free_bet); drift confirm
names both; non-bonus unchanged; settle row reports auto amount;
BurstReview lane (RED: absent); rounding util unit tests incl.
float-hostile + ceiling mode.

## 4. Correction CLI — ops/correct_credit_amount.py

CLI: --credit-event ×4 --reason --db [--apply]. Targets:
5e28904f($57→$56.25), 8634615f($11→$10.63), e0a61c59($26→$25.50),
4d6f5f73($23→$22.50); 4b701aa6 ($35.00) untouched.
Plan phase: exists ∧ promo_cash_credited ∧ finalised ∧ unsuperseded;
qualifier bet resolves + template matches; recompute via the SHARED
credit_kwargs_for_kind (never a mirrored formula); refuse if rounding
won't be 'cents' after step 0; refuse if recomputed==stored. Print
table + verification queries.
Apply: apply_migrations on setup conn (idempotent — column exists
with or without app restart); online-backup API →
~/.bethub/backups/bethub-pre-1b-correction-<ts>.db; PRAGMA
foreign_keys=ON → BEGIN IMMEDIATE → (0) UPDATE a3d997f8 rounding=
'cents' raw SQL → per credit CAS re-check then rejection event (old
payload, status='rejected', supersedes=old, amount stays wrong figure
— a1a86071 precedent) + replacement event (finalised, exact amount,
credit_source='triggered' copied, reference=old id,
correlation=qualifier) → COMMIT. 8 events + 1 UPDATE; atomicity IS
the crash story (no journal at this size). No bets-table write.
Verification (auto-run): live finalised cash at 825fd0d3… == 149.88
(NOT-IN subquery filtered IS NOT NULL); each old event superseded
exactly once; one LIVE credit per qualifier;
compute_account_at_book_balance before/after delta == −2.12, final ==
859.38 + post-23:07:50 activity; settlement_review clean.

## 5. Deploy

uv run pytest → npm run build (the type gate) → app-down window
(never race hours; target = pre-racing morning) → confirm :8787 free
→ deploy + dist swap → start (migration adds column) → CLI dry-run →
eyeball table → --apply → acceptance (verification block, Balances
$859.38+, settlement_review, Burst gaps quiet, auto-lane empty) →
live smoke on the next real bonus win.

## 6. Risk register

TAB shift → NULL=whole_dollar + untouched-green Krasina/S244 tests.
Bad-shape auto-fire → single shared evaluator, refusal=skip+gaps.
Double-credit → find_existing_credit under BEGIN IMMEDIATE + 409 +
tests. Settle-lands-credit-fails → non-fatal + warning + gap detector
+ test. Half-written correction → single txn + unique index + CAS +
backup + dry-run. Balances/pnl drift → both already lockstep + self-
check + fixture test. Frontend float drift → integer-cents util +
server-computed auto path + drift confirm. Stranded wrong auto-credit
→ cash undo door + walk test. FB-kind mis-default → kind from
return_type. Future book rounds differently → per-template radio at
creation; unset term = today's behaviour + visible "$X owed".

## 7. Decisions

OPERATOR REQUIRED: none. (No other-book %s exist to ask about —
other bonus templates are TAB's, correct at 0.25 whole-dollar; the 6
remaining Bet365-template bets are settled_lost. Bet365 cents/half-up
taken from the verified $10.625→$10.63; if a statement ever
disagrees, manual door + cash undo handle it in-app.)
RESOLVED BY PLAN (rationales in the plan record): rounding is the
missing term, not the %; term lives on promo_template; values match
the existing CreditRounding literal; NULL default preserves behaviour;
one nullable column justified over inference-from-return_type;
server-side trigger in the settle door (one door, all surfaces);
source='system' provenance with credit_source unchanged; no auto-fire
on reclass; no retroactive fire; cash undo ships with (c); single-txn
CLI (no journal); rejection keeps the wrong amount (a1a86071
precedent); EV untouched.

## Review outcome (S263 adversarial pre-build review) — SAFE WITH FIXES; these amendments are NORMATIVE

All 8 load-bearing claims independently CONFIRMED (incl.: zero activity
at Tim/Bet365 after 23:07:50 — $859.38 stands exact; the settle door /
worker / idempotency attack lines all held; TAB regression tests exist
and are enforceable).

- **HIGH-1 (gate, adopted):** `_linked_promo_blockers` (bets.py
  :2280-2298) skips only superseded events, never payload
  status='rejected' — a rejected-cash event (from the cash undo OR the
  §4 CLI) would become a PERMANENT phantom reclass blocker with an
  unreachable cure. The fence gains a rejected-skip; ships WITH item 19
  and BEFORE/WITH the correction. Test: fence lists only live credits
  post-undo AND post-CLI. (`correct_promo_selection.py:194-198` and
  `_triggered_credits` :888-889 already treat rejected as terminal —
  the fence was the one reader left behind.)
- **MED-1 (adopted):** §7's "manual door + cash undo handle it in-app"
  is FALSE — `find_existing_credit` counts rejected as already-credited
  (LOCKED contract, deliberately untouched), so re-banking after an
  undo is refused in-app in both orders. The re-issue path is
  `ops/correct_credit_amount.py`. §7 reworded accordingly.
- **MED-2 (OPERATOR QUESTION, posed S263):** item (c) auto-BANKING
  reverses the standing decision at `credit_gap.py:9-11` ("the credit
  itself stays a MANUAL operator action"). The commission's
  "automatically calculated" is fully satisfied by (a)+(b)+(d).
  (a)/(b)/(d) + cash undo + fence fix BUILD NOW; (c) items 13-18 + 20
  are STAGED pending the operator's answer.
- LOW-1: second `credit_kwargs_for_kind` caller (promos.py:405
  insurance arm) — the new kwarg is optional-defaulted; no change there.
- LOW-2 (scope decided): manual-credit kind defaults from the
  template's return_type wherever non-NULL (bonus-cash→cash,
  insurance-cash→cash — banking a cash payout as FB corrupts FB
  inventory; TAB FB templates→free_bet unchanged); NULL
  (price_boost)→free_bet. Matrix test.
- LOW-3: the CLI sets busy_timeout (S254 precedent) AND the deploy
  order moves the CLI BEFORE app start inside the app-down window.
- LOW-4: Sunday-morning window sequencing: 1b dist swap + CLI + app
  start first (short); Phase 1's v3-side action (AU pin removal) rides
  the later capture-side deploy. Different boxes otherwise.
- LOW-5: `credit_gap.py:32` stale docstring (says HALF_UP, code is
  ceiling) fixed alongside item 6.
- Reviewer test additions: fence post-undo/post-CLI; kind-default
  matrix; CLI correlation stamped as BARE UUID + payload keeps
  triggering_promo_instance_id; gap-list convergence; pnl_dashboard
  self_check_ok explicit on the corrected fixture; CLI-under-contention
  (busy_timeout, never half-applied). The evaluator-DB-re-read test and
  the auto-lane tests travel with (c).

## Post-implementation review (S263, commit `d3583cf`) — SAFE-TO-DEPLOY

All 8 verdicts PASS; suites re-run independently (2002 / 510). The
verb was REHEARSED end-to-end on a scratch copy of the live DB:
dry-run table exact, apply → live finalised cash 149.88, every event
superseded exactly once, correlation/trigger fields verbatim,
post-balance **$859.38 exact**, coherence sweeps [], fence returns
exactly one live blocker on a corrected bet, second-run + fifth-event
refusals fire. Live state pinned at review time: derived Tim/Bet365
$861.50; four targets still live; zero activity after 23:07:50.

Findings: MED (live until restart, self-curing) — old backend + new
dist mismatch: new-promo create 422s, cash undo 422s, Bet365 prefill
falls back to whole-dollar; refusals only, no corruption path. LOW ×3
test-coverage gaps QUEUED (create-endpoint rounding validation test;
TopBar radio→body wiring test; kind-default matrix FB/NULL arms) —
verified functionally in the rehearsal, tests owed. Deploy runbook §8
of the review (CLI before app start, per LOW-3).

## Post-implementation review #2 (`bdadb8f` + `2daa17a`) — SAFE-TO-RESTART

All 8 items PASS; suites re-run independently (2011/518); gate wording
proven byte-identical by AST extraction; the race/double-fire attacks
held (BEGIN IMMEDIATE guard → already_credited; 409 pre-hook; reclass
deliberately unhooked with credit-gaps as backstop); dead-heat
pass-through verified against every other update_settlement_state
caller (the manual door was the only bare call); occurred_at readers
swept (recorded_at ordering everywhere; the strip window is the
intended consumer). Live numbers pinned by running the REAL endpoints
on a scratch copy: bets-only $3,636.05 + promo cash $149.88 = all-in
$3,785.93, Balances self-check 0.00. dist (built 06:50) carries both
commits — the earlier dist/backend mismatch self-cures at restart.
LOW findings (none blocking): (1) Log Past Bet has no dead-heat input
— a past dead-heat win logged Won auto-banks the FULL bonus; undo is
the cure (operator briefed); (2) theoretical status-default asymmetry,
zero live rows affected; (3) DST-edge listing cosmetics in October.
INFO: worker-settled Betfair bets never auto-bank (by design;
bonus promos are soft-book-only in practice).
Known one-off: yesterday's four corrected credits sit on 2 Aug in day
views ($114.88 today, $35.00 on 1 Aug, all-time $149.88 either way).
