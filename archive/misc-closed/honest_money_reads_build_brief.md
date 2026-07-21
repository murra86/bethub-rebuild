# Honest money reads — build brief (B1, S244, Sun 19 Jul 2026)

**Commissioned:** operator, S244 ("Plan up build 1"). Sources:
`money_read_truncation_review_report.md` §4 (S243) + the S244 triage
findings (winnings-shape blind spot; placings-blind credit-gaps list).
**Grounded:** every anchor below re-verified against HEAD `53a8585` by a
6-agent grounding pass (S244) — the review report's anchors were 5
commits stale; where grounding changed the picture, this brief follows
the grounding, and divergences from the report's §4 are named.

**Theme:** money reads must be honest — no silent windows, no silent
caps, no promo shapes the doors can't see. One bounded Code session.

---

## Scope item 1 — kill the credit-guard event window (the HIGH fuse)

`find_existing_credit` (`workflows/promos/v1/fb_credit.py:106-117`)
scans `adapter.list_by_event_type(event_type)` bare → default
`limit=1000`, `ORDER BY recorded_at ASC` (`store/repositories/
promos.py:325-331`) → the guard sees only the OLDEST 1000 events per
credit type. Past event #1001: credit-in's dedupe goes blind (double-
credit writes through silently) and the credit-gaps detector re-lists
already-paid bets as owed. Both doors share this one helper
(`fb_credit.py:144`; `credit_gap.py:106`) — one fix covers both.

**Fix (O(1), no schema change):** rewrite `find_existing_credit` to use
the indexed correlation path — `adapter.list_by_correlation_id(
triggering_bet_id)` (`promo_store_adapter.py:226-232`; repo SQL
`promos.py:340-345`, unbounded, indexed by
`idx_promo_events_correlation`). `record_free_bet_credit` has stamped
`correlation_id = triggering_bet_uuid` on every triggered credit since
the original build (`fb_credit.py:195`), and the 17-Jul reset bounds
legacy exposure to zero.

Constraints the rewrite MUST keep (grounding caveats):
1. Filter results to `_CREDIT_EVENT_TYPES` AND keep the
   `payload.triggering_bet_id == X` check — correlation groups are
   shared (revokes stamp the credit's correlation, `fb_revoke.py:105`;
   deploys can carry operator correlations).
2. A REVOKED credit still answers "already credited" — no
   superseded-filtering (locked contract, `fb_revoke.py:13-17`).
3. Return shape stays `PromoEventBase | None` — callers consume
   `.event_id`, `.event_type.value`, `payload.amount`
   (`fb_credit.py:146-151`).
4. Restore-door corrective credits may carry a None correlation
   (`fb_restore.py:129`) — harmless: the original credit always exists
   and answers; state this in the function docstring.

**One-off data assertion (test, not migration):** every
`free_bet_credited`/`promo_cash_credited` row whose payload carries
`triggering_bet_id` has `correlation_id` equal to it (restore
correctives exempt).

## Scope item 2 — no silent defaults on promo money-event lists

Root class: `limit: int = 1000` silent defaults on the promo adapter +
repository list methods (`promo_store_adapter.py:213-218` by-type;
`_list_scoped` family `promos.py:443-475` with the same default).
After item 1 there are ZERO bare production callers — every remaining
caller already passes an explicit bound (burst_review 100k ×2;
promo_derivations 10k ×4; balance_derivation 100k).

**Fix:** make `limit` REQUIRED (no default) on the PROMO adapter's and
promo repository's list methods (`list_by_event_type`,
`list_rows_by_event_type`, the three scoped lists + `_list_scoped`).
Update the test call sites that relied on the default:
`tests/ui/api/test_promos_credit_in.py:174,201-203,244-246`;
`tests/workflows/promos/v1/test_fb_credit.py:153-154`;
`tests/workflows/promos/v1/test_promo_store_adapter.py:996`;
`tests/store/repositories/test_promos_repository.py:443-449`.
**Out of scope:** the three sibling adapters (bet_mutations / ops /
cash_flow) share the shape but have no bare money-path callers —
convention-wide change is named debt, not this brief.

## Scope item 3 — bets-API read honesty (consumer side)

Grounding CHANGED the report's picture: the wrapper is `fetchBetFeed`
(`ui/web/src/api/bets.ts:160`), and NO production caller omits `limit`
today — all 7 pass one explicitly. The residual traps are (a) callers
that never read `total` (six of seven — only BetLog does), and (b)
ad-hoc/external consumers (the S243 incident class: HTTP 200 + newest
50). **Divergence from report §4.3:** no fetch-all API form — after
grounding, the endpoint is honest and bounded (default 50, `le=500` at
`bets.py:694`, honest `total`); an unbounded form would reintroduce
the class on a growing table. Honesty lands consumer-side:

1. **TS type honesty:** make `limit` REQUIRED in `BetFeedFilters`
   (`bets.ts:119`) — tsc then forces every future frontend caller to
   choose a bound consciously. (All current callers already comply.)
2. **BurstReview truncation cue** (the one real >cap risk: `limit: 500`
   over ALL pending, `BurstReview.tsx:87`): read `total`; when
   `total > bets.length`, render a plain warning strip ("showing 500
   of N pending — oldest not shown").
3. **Standing rule, written where it bites:** one-paragraph
   "len-vs-total" rule (any sum over the bets API must reconcile
   `len(bets)` against `total`, and page by offset; note `len < total`
   also occurs via the malformed-row skip, `bets.py:728-733`) in:
   `ops/READS.md` (new, short), the `bets.py` module docstring
   (:1-33), and a JSDoc on `fetchBetFeed`.

## Scope item 4 — Balances movements fold-out honesty

`Balances.tsx:145-148` fetches `fetchMovements(30)`; fold-out
(`:462-537`) renders every returned row with no count, no cue; backend
returns a bare array, no total, clamp 200 (`cash_flow.py:359-432`,
clamp at `:391`).

**Fix:** envelope the endpoint — `{items: [...], total: N}` (COUNT(*)
inside the same try, before the `finally` close at `:431-432`;
`response_model` at `:361`). Frontend: summary line becomes
"Money movements (latest 30 of N)" when `N > items.length`, with a
"show all" toggle refetching at `limit=200` ("latest 200 of N" cue if
still short). Keep the `['racing','log-context', …]` queryKey prefix —
it rides the mutation invalidation sweep (`:154-156`, `:237-239`).
Update the two `fetchMovements` mocks in `Balances.test.tsx:104,251`
and `tests/ui/api/test_cash_flow_movements.py`.

## Scope item 5 — void detector: count-checked paging BEFORE wiring

`post_settlement_void.py:139-143`: single `list_bets(..., limit=100)`
read, newest-first → >100 terminal bets in the 24h window silently
drops the oldest; report saturates at `swept=100` with no signal.
Zero production callers today (grounding-confirmed) — fix the shape so
it can never be wired as-is. Storage already has everything:
`count_bets` shares `_bets_filter_sql` with `list_bets`
(`store/repositories/bets.py:1136-1171`).

**Fix (this file only):** `total = count_bets(settlement_states=
TERMINAL_NON_VOIDED_STATES, placed_from=floor)`; page by offset with a
hard overall cap (500 candidates/run — each candidate costs a Betfair
read via `settlement_reader.read`, `:154`); report gains
`window_total: int` + `truncated: bool` set at `:221-229`; correct the
now-false docstrings (`:23-26` "nothing is silently dropped", `:30-34`
"only existing read"). Wiring the detector stays OUT of scope (B2).

## Scope item 6 — sweep-slot hardening (manual resolution)

`apply_manual_operator_resolution` (`settlement.py:1828-1927`) writes
`settlement_state` only; reconciliation's sweep selects on
`match_status` alone, oldest-first, 100/pass (`reconciliation.py:
583-590`; SQL `bets.py:791-794`) — a terminally-resolved bet whose
match_status is stuck PROVISIONAL* occupies a front slot forever
(1 Betfair read + 1 bookkeeping write per 60s pass; at 100 stuck rows,
fresh bets are never swept — starvation, not just waste).

**Fix:** after the successful state write (insert between `:1904` and
`_write_settlement_bookkeeping` at `:1906`), when
`record.match_status` is in `_UNTRUSTWORTHY_MATCH_STATUSES`
(`settlement.py:106-109`): call `storage.update_match_status(bet_id,
status=..., matched_stake=record.matched_stake, unmatched_stake=
record.unmatched_stake, matched_price=record.matched_price)` — the
impl updates all four columns unconditionally (`bets.py:719-756`), so
current money values MUST be passed back (record already loaded at
`:1877-1880`). Status choice: `FAILED` when `matched_stake == 0`,
else `FINAL_PARTIAL` (`FINAL_FULL` when `unmatched_stake == 0`). Bets
already carrying a terminal match_status are untouched. Red-before:
a manually-resolved parked bet stays in `list_unreconciled_bets`
output; green-after: excluded.

## Scope item 7 — winnings-shape credit coverage (the S244 blind spot)

Tonight's facts: a WON bonus-winnings bet (Sarie $13, Leigh $33) is
invisible to BOTH doors — the credit-in gate requires
`safety_net ∧ settled_lost` (`promos.py:77-78, 243-257`) and the
detector mirrors it in SQL (`credit_gap.py:78-89`). Bonus-winnings
bets carry NULL `strategy_tag` by design (`ConfirmCard.tsx:121,153`;
there is no bonus_winnings StrategyTag) — kind must come from
`promo_template.kind`, which is a first-class enum value
(`domain/promos/__init__.py:102-109`).

**7a — credit-in door gains a kind-aware gate arm**
(`ui/api/routers/promos.py` credit_in): fetch bets row + template
FIRST (extend `_read_qualifier` SELECT `:209-214` with
`matched_price, side, is_free_bet, dead_heat_count,
removed_runner_count`; note the gate must now branch AFTER
`get_template` — reorder, or read bets+template in one joined query),
then:
- `kind == insurance` → existing gate unchanged.
- `kind == bonus_winnings` → require `settlement_state='settled_won'`
  ∧ (`side='BACK'` OR side IS NULL — a LAY "won" means the runner
  LOST; formula invalid, `settlement.py:616-625`) ∧ `matched_price`
  NOT NULL (422 parallel to the return_pct-None 422 at `:287-294`)
  ∧ NOT (`dead_heat_count > 0` OR `removed_runner_count > 0`) — a
  reduced payout is not quantified anywhere on the row
  (`bets.py:848-886` never stores an effective price), so refuse
  auto-compute with a plain "settle this one by hand" 422.
- Amount: `winnings = matched_stake × (matched_price − 1)`;
  `amount = min(winnings × return_pct, cap)` (skip min when cap NULL;
  `return_pct` is a FRACTION at this layer — never ×100). Free-bet
  qualifiers (SNR) need no exclusion — winnings formula identical.
- **Rounding (operator-ratified S244):** bonus_winnings credits
  quantize ROUND_HALF_UP to the WHOLE DOLLAR — matches TAB's observed
  behaviour ($50 winnings → $13; $130 → $33). Insurance credits keep
  cents. Implement by extending `record_free_bet_credit` with optional
  `cap: Decimal | None` and a rounding mode — pass winnings as the
  `stake` multiplicand; idempotency, payload validators, cash/FB
  branch (`return_type == "cash"` → `PROMO_CASH_CREDITED`,
  `fb_credit.py:170-177`) are all inherited unchanged.

**7b — detector gains the same arm** (`credit_gap.py`): second SQL
branch — `settled_won` bets JOIN `promo_template` ON
`kind='bonus_winnings'` (side/price guards mirrored; dead-heat rows
still listed but marked hand-settle). Output extends
`UncreditedQualifier` with `expected_amount: str | None` and
`promo_kind: str` (subclass-field pattern; `CreditGapItem` at
`promos.py:339-344` passes new fields explicitly at `:383-388`).
Frontend `api/promos.ts:57-63` interface + burst-review rows show the
computed owed amount; "Bonus landed → bank" wires to the same
credit-in door (now accepting the shape). Red-before fixtures = the
real Sarie/Leigh shapes (settled_won bonus_winnings, no credit →
listed with expected $13/$33; after credit-in → gone).

**7c — cash variant:** one test proving the `return_type='cash'`
winnings arm writes `PROMO_CASH_CREDITED` (payload shape
`domain/promos/__init__.py:450-507`).

## Scope item 8 — placings on the credit-gaps list

The list is placings-blind, so 23 of 23 entries tonight were also-rans
needing manual SSH archaeology. The per-bet endpoint ALREADY exists:
`GET /api/v1/bets/{bet_id}/race-result` (`bets.py:1258-1338`,
DR-028-clean via vps_client resolve→results, soft-unavailable never
500) — gap rows are bet ids.

**Fix:**
1. **Backend (small):** extend `BetRaceResultResponse` (`bets.py:
   1244-1255`) with the BET's own runner: `selection_position:
   int | None` + `selection_scratched: bool` — looked up in the FULL
   `results.runners` list (the `placings` field caps at 4, `:1336`,
   so an outside-top-4 runner is otherwise position-less). Keep the
   `win_market_id == leg.betfair_market_id` integrity check
   (`:1300-1306`).
2. **Frontend:** burst-review gap rows fetch it per-row (copy BetLog's
   `SettleDoorResult` pattern — `['bets', betId, 'race-result']`,
   staleTime 60s, retry:false, `BetLog.tsx:342-372`) and render a
   verdict chip vs the template's `refund_positions` (already on the
   catalogue client-side, `api/promos.ts:17`):
   - position ∈ refund_positions → **"ran 2nd — CHECK BOOK"** (amber);
   - known position outside (or absent from full results with results
     available) → "ran 5th — outside" (grey);
   - unavailable / voided / dead-heat / scratched → "?" (no verdict).
   Exception (Cat-4 lesson): a 3rd-place verdict at a BetRight
   account-at-book renders "ran 3rd — check terms (≤7 field pays
   nothing)" — never auto-classed owed or outside.
3. **One-tap sweep:** "Dismiss N ran-outside" button — frontend loop
   over the existing single-bet dismiss POST (idempotent,
   per-call-committed; no bulk endpoint needed at this scale). Only
   rows with a confident grey verdict are included.
4. **Cost honesty:** ~3 tunnel GETs per row, paid lazily per-row with
   the soft-miss pattern — the gaps list itself never blocks on VPS
   availability. DR-028: no caching, no second integration point.

## Test plan + gates

Red-before/green-after on items 1 (guard blind past window — fixture
with >window events or a shrunk window seam), 5 (105-bet window),
6 (slot occupancy), 7a/7b (Sarie/Leigh shapes), 8.1 (outside-top-4
position). Suites: `uv run pytest` (backend, from 1481) + `cd ui/web
&& npx vitest run` (from 215) + `npm run build` (tsc gate; dist
rebuild only app-down per S232). Commit+push per git autonomy;
report to `bethub-rebuild/honest_money_reads_build_report.md` —
inventory-first (deviations/opens classified operator-relevant or
not), live-integration bucket stated per feature (implemented-not-live
until the next app bounce).

## Hard limits

- Money-path fences: no settlement/resolver logic changes beyond the
  named `apply_manual_operator_resolution` insertion; no bet-row money
  fields written anywhere (item 6 passes existing values through).
- No promo EVENT semantics changes: append-only spine untouched; no
  new event types.
- No app restart / no dist deploy inside the session; flag the pending
  bounce in the report.
- Out of scope: sibling-adapter defaults (named debt), void-detector
  WIRING, auto-restore-on-void + void/delete door + BetRight ≤7
  catalogue conditional (all B2), bets-API fetch-all endpoint
  (divergence recorded above), v2, VPS capture side.

## Sequencing note

Order within the session: 1 → 2 (same surface) → 7 (door+detector
while promo context is loaded) → 8 → 6 → 5 → 3 → 4. Items 3, 4, 8 are
frontend-heavy; batch their `npm run build` once at the end.
