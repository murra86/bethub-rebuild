# PLAN — auto-bank insurance credits when the horse places

**Status:** PLAN, for adversarial review. Nothing built.
**Session:** S267, 5 Aug 2026. Operator asked directly: "are bonuses being
auto-banked for triggered insurance bets?" Answer today: **no.**

## The gap, in money terms

`try_auto_bonus_credit` (`workflows/promos/v1/auto_credit.py:132`) refuses
anything whose template is not `BONUS_WINNINGS` and whose bet is not
`settled_won`. So auto-banking covers **win-and-get-a-bonus only**.

Insurance — the arm that pays when the horse runs 2nd/3rd and the bet
LOSES — is still banked by hand. Insurance is the operator's dominant
promo type and it triggers ~52% of the time (S246 facts), so **the
majority of credits are still manual**. Nothing is lost: `credit_gap`
lists what is owed. But it is hand-work on a recurring error class, which
the standing self-serve rule says should become automatic.

## The dependency nobody had noticed, and why it is only now buildable

`insurance_gate_refusal` (`auto_credit.py:88`) checks `strategy_tag ==
safety_net` and `settlement_state == settled_lost`, then asks
`covered_insured_positions` (`credit_gap.py:99`) which positions the promo
still covers at that field size.

**None of that knows where the horse actually finished.** The credit-in
door leaves that to the operator's eyes — the docstring says a `covered`
of None "stays operator-judged".

To auto-bank, the system must know the runner placed. Finishing positions
come from The Racing API and, until today, were fetched **once a night at
05:30 Adelaide** — so on race day the fact needed to decide the credit did
not exist. S267's intraday results pass
(`deploy/systemd/racing-intraday-results.timer`, 15:00/19:00/22:30) is
what makes this buildable at all. **This plan is strictly downstream of
that timer proving itself.**

## The build

### A1 — extend the auto-credit gate to the insurance arm
`try_auto_bonus_credit` gains an insurance branch that fires on
`settled_lost` + `safety_net` + an attached insurance template. It reuses
`insurance_gate_refusal` verbatim — no second copy of the eligibility
rules, matching the 0s review's NORMATIVE single-copy amendment.

### A2 — the position fact, and its fail-safe
Read the bet's own runner finishing position through the existing results
path (`race_results` → `selection_position`, the read
`ui/api/routers/bets.py:3868` already uses). Then:

- position is **known AND inside** `covered_insured_positions` → bank,
  `source=SYSTEM`, exactly as the winnings arm does;
- position is **known and NOT covered** → silent skip, nothing owed;
- position is **unknown, stale, or the results read is unavailable** →
  **silent skip, leave it to `credit_gap`**.

The third branch is the whole safety design. **Never bank on an absent
fact.** A missed auto-bank costs nothing — the gaps lane already lists it
and the operator banks it as they do today. A wrongly-banked credit
corrupts a ledger certified defect-free on 2 Aug.

### A3 — dead heats and scratchings are refused, not guessed
If the results carry a dead heat at the insured position, or the runner
is flagged scratched, refuse to auto-bank and leave it to the operator.
The winnings arm already refuses on `dead_heat_count` /
`removed_runner_count` (`auto_credit.py:170`); the insurance arm must be
at least as conservative, because a dead heat changes what the book pays.

### A4 — trigger point
Bank at the same place the winnings arm does — the settlement path that
already calls `try_auto_bonus_credit` (`ui/api/routers/bets.py:2860`,
`:4099`). No new worker, no new timer. A bet settled before its placings
land simply skips and is picked up by the operator or a later pass.

## Risk register

| risk | mitigation |
|---|---|
| Banks a credit the book never pays | only banks when the position is KNOWN and inside the covered set; unknown → skip |
| Results arrive late or wrong → wrong credit | fail-safe skip on absent/stale facts; `credit_gap` remains the backstop |
| Dead heat pays differently | refuse, operator-judged |
| Cycle lineage damage (the 0v lesson) | this ISSUES a credit on its qualifier exactly as the manual door does — it does not revoke, split or re-point anything. Lineage is created, not rewritten. |
| Double-banking | the credit-in writer's existing idempotency/replay guard is the single authority; no new key scheme |
| Silently changes P&L | acceptance requires cycle-audit before/after unchanged in defect count |

## Acceptance

1. `ops.cycle_audit` before/after: **zero defects**, cycle count moves only
   by genuinely new credits.
2. A settled_lost safety_net bet whose runner placed 2nd, inside cover →
   banked once, `source=SYSTEM`, attached to the qualifier's cycle.
3. The same bet with the position UNKNOWN → not banked, appears in
   `credit_gap`.
4. The same bet, position 5th → not banked, nothing in `credit_gap`.
5. Dead heat at the insured position → not banked, operator-judged.
6. Re-running settlement does not double-bank.
7. `uv run pytest` green; `npm run build` green.
8. Live proof on ONE real insurance trigger before it is trusted —
   compare against what the book actually paid.

## Explicitly out of scope

- Cash-arm promos (a different shape; promo-selection correction owns it).
- Changing `insurance_gate_refusal`'s rules.
- Any revoke, split or re-point of an existing credit — the 0v lesson.

## Sequencing

**Do not build before** the intraday results timer has demonstrably filled
placings on a race day. Everything here rests on that fact being present
and correct at settlement time. If placings prove unreliable intraday, the
honest outcome is to leave insurance banking manual and say so.

---

# ADVERSARIAL REVIEW — VERDICT: NO-GO (S267, 5 Aug 2026)

**Operator shelved this item before the review returned ("I don't want
auto-settle or auto-trigger yet"). The review vindicates that decision
and is filed here for whenever it is revisited.**

Not rejected for the 0v reason — issuing IS safer than revoking, and the
lineage claim HOLDS: a SYSTEM insurance credit is byte-identical in shape
to the manual door's (`fb_credit.py:266-271` stamps `credit_source=
TRIGGERED` + `triggering_bet_id` regardless of `source`). It fails on its
own central mechanism.

## BLOCKING

**B1 — the covered-set is the wrong function, and undefined for 173 of
173 real qualifiers.** `covered_insured_positions` returns `None` unless
the template has BOTH `refund_positions` AND `position_min_field` AND the
bet has `field_size_at_placement` (`credit_gap.py:115-121`). Only 1 of 8
live insurance templates carries `position_min_field`, and **zero**
settled-lost safety_net bets use it. So `covered` is `None` for every bet
this would ever see, and both readings are bad: skip → banks nothing,
ever; unrestricted → **every settled-lost safety_net bet mints a free bet
regardless of where the horse finished (~$5k of phantom inventory in one
pass)**. The needed fact is `refund_positions`; `covered_insured_positions`
is only the field-size filter on top.

**B2 — the trigger cannot see the fact it depends on.** Both callers gate
on `settled_won` (`bets.py:2855`, `:4092`) and nothing retries. The
operator settles within minutes of the jump; the intraday timer runs
15:00/19:00/22:30. At settle time the position is essentially never
present, and A4's "a later pass" does not exist in the codebase.

**B3 — the dead-heat safeguard has no data.** The cited read computes
dead heat as `winner_count > 1` over WINNER rows only
(`clients/vps_client/v1/results.py:177`), so **a dead heat at 2nd or 3rd
— the insured position — is invisible**. Acceptance 5 is undemonstrable.

**B4 — field degradation.** The gate judges `field_size_at_placement`;
scratchings after placement can drop the actual field below the
template's minimum, so the book pays nothing while the gate passes. The
1a plan makes this an explicit rule (`results_log_plan_s263.md:316-321`);
this plan dropped it. 51 of 173 qualifiers have the field NULL anyway.

**B5 — the "stale" fail-safe branch is unimplementable.** `finalised_at`
is always None, `stewards_status` hard-coded OFFICIAL. Nothing
distinguishes a provisional position from the authoritative one, and once
banked `credit_gap` stops listing the qualifier (`credit_gap.py:248`) —
**the backstop goes blind exactly on the bets the gate got wrong**.

## FACTUALLY WRONG IN THE PLAN

- Acceptance 4 ("5th → nothing in credit_gap") is false: the detector's
  insurance arm has **no position filter** (`credit_gap.py:191-209`).
- A1 alone is inert — both call sites gate on `settled_won`.
- The cited read (`bets.py:3856` → `race_results`) is the pre-0l row-id
  route; `race_results_by_market` is the fixed one. *(S267 note: the
  Results page already uses the correct route — `racing.py:955`.)*
- "Cycle-audit defect count unchanged" ≠ P&L unchanged. Banking a live
  credit **re-opens the qualifier's play and nulls `close_date`**
  (`cycle_audit.py:1026-1032`, `:1398-1402`).

**Verified sound in the plan:** the description of the current refusal
behaviour; that `insurance_gate_refusal` does not know the finishing
position; and that **double-banking is genuinely not a risk** — the
idempotency guard uses `BEGIN IMMEDIATE` before the guard read
(`fb_credit.py:104-121`).

## THE FINDING THAT MATTERS MOST

**This already exists as an operator-CONFIRMED design and is SHIPPED:**
1a Phase 3, "Settle lost + bank $X" — a one-tap composing settle +
credit-in in the settle-up lane (`results_log_plan_s263.md:294-330`;
shipped S265 `88d3f39`). The plan silently converted an operator-confirmed
**one-tap** into an **unattended write**. That is an operator decision
reversal, not a build detail.

## IF REVISITED — minimum changes

1. Start the verdict from `refund_positions`; apply
   `covered_insured_positions` only as the field-size filter; refuse when
   the field is NULL or the actual finishing field is below `min_field`.
2. Read via `race_results_by_market` — union-guarded, carries
   `result_status`, `scratched`, `dead_heat_confirmed`, `winner_conflict`.
   Detect a dead heat at the insured position by duplicate
   `finish_position`, not the WINNER-only flag.
3. Keep it as the 1a Phase 3 one-tap. If any automatic arm survives, scope
   it to the Log-Past-Bet path where positions genuinely exist by then.
4. Publish the same-day placings probe first (S267's place-market work
   `026477b` is the fallback the 1a plan anticipated and nobody built).
5. Dry-run the gate over the 173 historical qualifiers and reconcile
   against what the books actually paid, before a single write.
