# Build plan — promo-selection correction verb hardening (worklist 0s)

S263, 2 Aug 2026. Plan only — no code changed. A reviewer follows.
Target: `bethub-v3/ops/correct_promo_selection.py`, before any cross-kind
run and before the BetLog "change promo" button (worklist 0x) wires to it.

## Operator summary

The "change promo" fixer has now corrected three mis-picked promos and
works exactly as built — for swaps between promos of the same family. Four
gaps would only bite when it's used across families (e.g. re-pointing a
cash promo to a bonus-on-winnings promo) or once it's behind a button:
it could pay a bonus on a LOSING bet, use stale numbers if the bet was
edited mid-correction, issue a bonus with no expiry date once TAB's 7-day
window is recorded, and put replaced money on the wrong day in daily
totals. One of the four originally-listed gaps (the paid-tick showing for
a cancelled credit) was already fixed and tested in yesterday's work —
verified, nothing to build there. The remaining three plus the date fix
are small, all inside one file, about half a sitting including tests.
Confidence: high — every rule being added already exists elsewhere in the
tool as the single source of truth; this work points the fixer at those
same rules instead of skipping them.

## 1. Verified current state (all cites checked 2 Aug)

**(a) Under-lock re-assertion is partial.** `apply_correction` re-checks
only (i) the credit's supersession and (ii) the bet's `promo_template_id`
(`correct_promo_selection.py:312-329`). `settlement_state`,
`matched_stake` and `matched_price` — the inputs the replacement AMOUNT
was computed from at plan time (lines 234-258) — are NOT re-compared, so
an edit landing between plan and apply commits a stale amount. The bet
row IS already re-read inside the transaction for the audit snapshot
(lines 375-381) — the fix is a comparison, not a new query. S254 pattern:
`ops/correct_promo_chain.py` runs a settlement re-check inside every
step's own `BEGIN IMMEDIATE` (module header, line 50).

**(b) Expiry hardcoded None.** The replacement FB stamps
`face_value_expiry: None` (lines 441-446) even though `plan()` already
fetches the target's `fb_expiry_days` (line 286). Confirmed harmless
TODAY — all 12 catalogue templates carry `fb_expiry_days = NULL` (DB
checked) — and confirmed divergent the day TAB's 7-day window is set:
the normal door stamps `occurred_at + days` (`fb_credit.py:283-289`).

**(c) No kind gates on re-point.** `plan()` allows `settled_won`,
`settled_lost` AND `voided` for any target kind (line 160); `side` is
selected and discarded (line 148); `dead_heat_count`,
`removed_runner_count`, `field_size_at_placement`, `strategy_tag` are
never consulted. The credit-in door's gates live at
`ui/api/routers/promos.py:316-390`:
- bonus_winnings arm → `bonus_winnings_gate_refusal`
  (`workflows/promos/v1/auto_credit.py:40-78` — the deliberate single
  copy: settled_won, not LAY, matched_price present, no
  dead-heat/removed-runner);
- insurance arm → `strategy_tag='safety_net'` + `settled_lost` +
  small-field void via `covered_insured_positions`.
Confirmed red: a cash→bonus_winnings re-point on a settled_lost bet
passes `plan()` today and would mint a credit the door itself refuses.

**(d) Paid-marker status filter — ALREADY DONE, verified, no build.**
`_triggered_credits` (`ui/api/routers/bets.py:843-963`) skips
`status='rejected'` credits (line 899) and credits superseded by a revoke
or a rejected-cash cancellation (lines 913-921); landed with `329c42f`
(S259) and extended by the 2 Aug work. The strip's bonus-cash line
filters `finalised` (lines 1162-1163) and the reclass fence skips
rejection terminals (1b HIGH-1, lines 2394-2401). Test coverage exists
for the exact worklist scenario:
`tests/ui/api/test_bets_reclass.py:607`
(`test_feed_ignores_a_rejected_cash_cancellation_terminal`) and `:668`
(fence), `tests/workflows/promos/v1/test_fb_revoke.py:233,:280`,
`tests/ui/api/test_bets.py` (strip window test). Item (d) closes as
verification-only.

**(e) occurred_at delta (folded in per commission).** The replacement
credit stamps `occurred_at=now` (line 454). The amount-correction verb
`ops/correct_credit_amount.py:360-369` carries the in-code operator
decision (2 Aug): a replacement keeps the ORIGINAL credit's economic
date so day-windowed views (BetLog strip bonus-cash line) don't shift
money onto the correction date; `recorded_at` stays now; the
cancellation terminal stays `occurred_at=now`. The selection verb's
credit SELECT doesn't fetch `occurred_at` at all (lines 189-204) — add.

## 2. Design

All changes inside `ops/correct_promo_selection.py`; the shared helpers
are imported, never mirrored (the ◆4 rule that already governs the file).

**(a) Re-assert under the lock.** `plan()` already returns
`settlement_state`; add `matched_stake` and `matched_price` to `plan_d`.
In `apply_correction`, the existing in-transaction bet re-read (lines
375-381) gains a comparison immediately after it: if `settlement_state`,
`matched_stake` or `matched_price` differ from the plan baselines →
`PromoSelectionError("bet changed since planning — re-plan")`, whole
transaction rolls back (the existing fail-closed path). Refuse-on-drift,
not recompute-under-lock: identical to the S254 posture, and the operator
simply re-runs plan.

**(b) Stamp the target template's expiry.** On the FB branch:
`face_value_expiry = replacement_occurred_at + timedelta(days=tpl_exp)`
when `plan_d["fb_expiry_days"]` is not None, else None. Anchoring on the
replacement's `occurred_at` — which after (e) is the ORIGINAL credit's
date — matches the book's reality (its clock started when it issued the
credit, not when we corrected our record) and keeps
`expiry = occurred_at + days` coherent with the normal door.

**(c) Re-apply the credit-in door's kind gates at plan time.** Extend the
`plan()` bet SELECT with `dead_heat_count`, `removed_runner_count`,
`field_size_at_placement` (side/strategy_tag are already selected). After
the target template is loaded, branch on `tpl_kind`:
- `bonus_winnings` → call `bonus_winnings_gate_refusal(...)` and refuse
  with its wording verbatim (the single copy stays single);
- insurance (and other computable kinds) → refuse unless
  `strategy_tag='safety_net'` and `settlement_state='settled_lost'`
  (the door's §5.3 pair), then apply `covered_insured_positions(
  refund_positions, position_min_field, field_size_at_placement)` and
  refuse when it returns an empty covered set (door wording).
Refusal messages append the route: "if the book genuinely paid, cancel
via the undo door and bank through the manual credit door instead."
Deliberate behaviour change: a VOIDED bet — allowed today — is now
refused on every arm (nothing is owed on a voided bet under any
computable template; the correct action is the undo door, which the
refusal names). No existing test asserts the voided path (suite checked:
`tests/ops/test_correct_promo_selection.py` uses settled_lost only), so
nothing flips silently.
Gate inputs are covered under the lock by (a)'s re-assert plus immutable
columns; the same-kind live path (insurance cash↔FB on a settled_lost
safety-net bet — all three real incidents) passes unchanged.

**(e) occurred_at.** Add `occurred_at` to the credit SELECT and
`plan_d["credit"]`; replacement `occurred_at =
datetime.fromisoformat(credit["occurred_at"])`; cancellation keeps
`occurred_at=now`. Byte-for-byte the `correct_credit_amount` pattern,
including its in-code comment convention.

**Optional, reviewer's call (not required by 0s):** default pre-write
online backup mirroring `correct_credit_amount` ◆5 (`--no-backup` for
tests). One helper, consistency between the two sibling verbs; becomes
moot per-click once 0x fronts the verb with an endpoint.

**0x readiness note:** with (a)-(c) in, the plan/apply pair is safe to
front with a `POST` endpoint for the BetLog button — plan = the preview
the button shows, apply = the confirm. Endpoint itself is 0x's scope,
not this work's.

## 3. Red-before tests

Extend `tests/ops/test_correct_promo_selection.py` (existing 20 tests
stay green; the fixture gains promo-kind knobs):

- (a) plan → mutate `matched_stake` (and, separately, `settlement_state`)
  → apply refuses "changed since planning", nothing written — RED today
  (commits the stale amount);
- (b) target template with `fb_expiry_days=7` → replacement FB stamps
  `face_value_expiry == original_credit.occurred_at + 7d` — RED today
  (None);
- (c) cash→bonus_winnings on a settled_lost bet → REFUSED at plan — RED
  today (mints). Plus: bonus target on a LAY / missing matched_price /
  `dead_heat_count=1` → refused with the door's wording; insurance
  target on a settled_won or non-safety_net bet → refused; insurance
  target whose `position_min_field` voids every position at the bet's
  field size → refused; voided bet → refused naming the undo door;
- (e) replacement carries the original credit's `occurred_at`;
  cancellation carries now — RED today (mirror
  `test_apply_supersedes_and_reissues_exact_in_one_txn`'s assertions in
  the amount-verb suite);
- keep-green: same-kind cash↔FB re-type on settled_lost safety_net (the
  live shape) still applies to the cent; second correction still
  possible; rollback and CAS suites unchanged.
- (d): no new build; if the reviewer wants belt-and-braces, the existing
  `test_feed_ignores_a_rejected_cash_cancellation_terminal` already pins
  the scenario — reference it in the session record rather than
  duplicating it.

## 4. Effort

All items are edits inside one verb + one test file: **~half a sitting**
including the red-before suite. No migration, no endpoint, no frontend,
no deploy-window exposure (an ops CLI; nothing imports it at runtime).
Suggested order: (e) → (a) → (b) → (c), each with its tests, since (c)'s
refusal tests lean on the fixture knobs (a)/(b) introduce.

## 5. Operator questions

None. The one behaviour change (voided bets now refused and routed to
the undo door) is documented in §2(c) with rationale; it tightens toward
the door the operator already uses, and no live correction has ever run
on a voided bet.

## Adversarial planning review (S263) — SAFE WITH FIXES; amendments NORMATIVE

Every line cite verified; item (d) confirmed genuinely closed by the
1b/2-Aug work; the voided-bet refusal blocks nothing in history
(zero voided bets ever carried a credit) and names its route — one
operator line at ship per the friction rule.
1. MEDIUM — EXTRACT `insurance_gate_refusal(...)` beside
   `bonus_winnings_gate_refusal` and call it from BOTH the credit-in
   router and the verb. The plan as written re-states the
   safety_net/settled_lost gates — the exact second-copy drift class
   1b part (c) just eliminated for the winnings arm.
2. MEDIUM-LOW — add `dead_heat_count`/`removed_runner_count` to the
   under-lock re-assert (operator-editable post-settlement — the S258
   deduction-edit path — and they change both gate outcome and
   amount through exactly the race window (a) closes).
3. LOW — template-terms drift between plan and apply is NOT covered:
   either re-read the template row under the lock or state the
   accepted exposure plainly (the sibling amount-verb accepts it too).
4. LOW — red-before additions: a matched_price-mutation case for (a);
   and a CLI WARNING when (b)'s expiry stamping produces an
   already-past `face_value_expiry` (replacement FB instantly
   invisible in inventory — economically honest, operationally
   surprising).
5. COSMETIC — "existing 20 tests" is 17.
