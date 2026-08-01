# B2 build brief — money-safety doors (S246, 20 Jul 2026)

**Base:** bethub-v3 HEAD `f28a7ef`. **Design note:** `b2_money_doors_design_note.md`
(read it first — it carries the real-world rationale per item).
**Report to:** `bethub-rebuild/b2_build_report.md`.

**Decisions locked (operator walkthrough S246):** D1 any terminal→terminal;
D2 delete fence unchanged; D3 auto-restore on both void reasons; D4 Option A
(catalogue term + EV honesty); D5 judge against live ACTIVE runner count;
D6 Tim deposit = paired write in one door action; D7 expiry default per
template; D8 backfill deferred to triage (operator present — do NOT write
live promo events in this build); D9 manual credit door = general valve with
mandatory reason; D10 void-detector hits are operator-fixed via the new
re-class door (detector stays read-only).
**Item 8 ruling (operator):** go-live balances = money already in
circulation. The ledger correction pass is prepared separately by the main
session — NOT part of this build. Build the tripwire code; it ships
non-blocking so it may briefly flag until the pass lands.

## Fences

- This build IS allowed to touch money-path files — that is its purpose.
  Compensating rules:
  - Every new state/money write goes through a door with a mandatory
    operator reason, or is a system write that is idempotent + correlated
    + supersede-based (never destructive). No UPDATE-in-place on event
    tables; the promo/cash spines stay append-only.
  - Red-before/green-after tests for every behavioural change on
    settlement, credits, and EV arithmetic.
  - No silent caps anywhere; any truncation surfaces on the API response
    and the report.
- Do NOT write to the live DB (no seeding, no backfills, no ops scripts
  executed against `data/*.db`). Tests use their own fixtures.
- Do NOT start the app or workers. Frontend dist rebuild is fine (app is
  down).
- Capture VPS entirely out of scope.
- Schema changes: additive only, via the existing migration pattern in
  `store/schema/` (match how the promo terms columns were added
  additively — `store/schema/promos.py:261-269` is the exemplar).
- Commit per item (git autonomy: commit style matches recent history,
  e.g. "S246 B2 item 1: …"), push only when the full gate is green.

## Gates

- Backend: `uv run pytest` green (baseline 1530).
- Frontend: `cd ui/web && npm run build` (the typecheck gate — vitest
  does NOT typecheck) AND `npx vitest run` green (baseline 255).
- Report every item with: what it protects (one real-world line), what
  was built, file:line anchors, tests added (named), and any deviation
  from this brief with why. Honest-status section: what is
  implemented-not-live and what its first live confirmation will be.

## Build order and items

### Item 5 — FB expiry stamping (smallest first)
- New nullable promo_template column `fb_expiry_days INTEGER` (additive
  DDL next to the S244 term columns, `store/schema/promos.py:261-269`;
  domain field on `PromoTemplate`, `domain/promos/__init__.py:727-764`;
  exposed on `PromoCatalogueItem` and the create door
  `ui/api/routers/promos.py:556-608`).
- `record_free_bet_credit` (`workflows/promos/v1/fb_credit.py:144-243`)
  stamps `face_value_expiry = occurred_at + fb_expiry_days` when the
  triggering template carries the column (today it writes None —
  grounded). Cash credits (`PromoCashCreditedPayload`) stay expiry-less
  by design.
- The surfacing chain already exists end-to-end (inventory filter drops
  expired at read time and sorts earliest-first,
  `workflows/promos/v1/promo_derivations.py:163-241`; API field
  `AvailableFreeBet.face_value_expiry`). Verify with tests, do not
  rebuild it. Frontend: show the expiry date on the TopBar FB source
  panel rows (`ui/web/src/components/TopBar.tsx:321-465`) and the LPB
  FB list — date only, red when within 48h.
- Seed data: set `fb_expiry_days=7` on TAB templates in the catalogue
  create path defaults? NO — templates are operator-created; instead
  surface the field in the create door and report which existing
  templates would need it set at triage (read-only list in the report).

### Item 6 — Manual-amount credit door (general valve, D9)
- New door `POST /v1/promos/manual-credits` beside `credit_in`
  (`ui/api/routers/promos.py:221-404`): operator-supplied `amount`,
  mandatory `reason` (min_length 1), `triggering_bet_id`, optional
  explicit `face_value_expiry`, `return_type` free_bet|cash.
- Same idempotency guard (`find_existing_credit`,
  `workflows/promos/v1/fb_credit.py:107-141`) keyed on the triggering
  bet's correlation group; refuse a second credit with the existing-
  credit reason (mirror the auto door's refusal shape).
- Trail: OPERATOR source, reason into notes; marked distinguishably
  (e.g. `credit_source="operator_manual_amount"` in the payload) so
  `ops.settlement_review` can list manual credits in the daily check —
  add that daily-check line.
- The dead-heat/removed-runner shapes the auto door 422-refuses
  (`promos.py:294-346`) are the primary use; door is general (D9), the
  422 message should now point at the manual door.

### Item 2 — Auto-restore-on-void (D3: both void reasons)
- In `workflows/bet_entry/v1/settlement.py`, both resolvers' VOIDED
  writes (market void 747-753/1011-1018; runner removed
  830-832/1100-1102): after the bet flips VOIDED, if the bet consumed
  FB credits (its `free_bet_deployed` events — locate via the promo
  spine, correlation `triggering_bet_id`/consumed ids, see
  `workflows/promos/v1/fb_deployment.py:120-230`), write the corrective
  credit via `record_free_bet_restore` (`fb_restore.py:53-133`),
  SYSTEM source, reason naming the void (`auto_restore_on_void:
  <void reason>`), correlated to the bet.
- Idempotent by the existing supersession guard (a deploy already
  superseded is refused — treat that refusal as success/no-op).
- Non-blocking: a restore failure must NEVER block or roll back the
  void. Mirror the FB_DEPLOY_EVENT_WRITE_FAILED pattern
  (`ui/api/routers/racing.py:545`) — log a parseable warning line and
  add a daily-check line in `ops.settlement_review` ("FB auto-restore
  failed — restore manually via deployment-corrections").
- Red-before: a test proving today's behaviour (void leaves the FB
  consumed) then green with the restore visible in
  `compute_free_bet_inventory`.

### Item 1 — Re-class door + audit migration (keystone)
- Additive migration extending the bet-mutation audit CHECK to include
  `BET_RECLASSED` (the parked follow-up noted at
  `ui/api/routers/bets.py:973-975`; delete-audit exemplar at
  `bets.py:1099-1117` writes on an FK-less connection — reuse the
  pattern).
- New door `POST /v1/bets/{bet_id}/reclass`: allowed FROM any terminal
  state (`settled_won|settled_lost|voided`) TO any other terminal state
  (D1), mandatory `operator_reason`. Refused for pending/provisional
  (those have their own doors) and for Betfair-settled bets (same
  worker's-lane 422 as the settle door, `bets.py:1013`).
- Linked-promo fence: before re-classing, read the bet's promo events
  (credits triggered by it / deployments consuming FBs). If any
  NON-SUPERSEDED credit or deployment hangs off the bet in a way the
  new state contradicts (e.g. won→void with a banked bonus-winnings
  credit), REFUSE with a list of the linked event ids and the door that
  fixes each (revoke door `promos.py:844`, restore door `promos.py:782`)
  — refuse-with-list, exactly like the credit-in gate's refusal shape.
  Do not auto-cascade (attended-only).
- Writes: `update_settlement_state` + the `BET_RECLASSED` audit row
  (old state, new state, reason, timestamp) + the same parseable log
  line shape the settle door emits so `ops.settlement_review` counts
  re-classes.
- Frontend: BetLog row action (expanded tuck-in) "Re-class…" with
  reason field; plain-language confirm listing money consequences.
  P&L invalidation via existing keys.

### Item 7 — Void-detector wiring (D10: report-only, fix via Item 1)
- `run_post_settlement_void_detection`
  (`workflows/bet_entry/v1/post_settlement_void.py:134`) gets a caller:
  a third pass in `settlement_worker_cycle`
  (`ui/api/settlement_worker.py:74`), throttled to once per hour
  (in-process timestamp; first cycle after start runs it). Detector
  stays read-only — no state transitions (D10).
- Hits surface three ways: (a) parseable log line per hit; (b) a
  money-health field on `GET /api/health/workers`
  (`ui/api/routers/health.py:142-170`, response model 95-101) rendered
  by a new `problemsFrom` branch
  (`ui/web/src/components/HealthBanner.tsx:35-68`) — non-blocking
  banner: "N settled bets look voided at Betfair — review in BetLog";
  (c) a daily-check section in `ops.settlement_review` listing each
  flagged bet and pointing at the re-class door. `truncated=True` must
  appear in all three surfaces ("checked 500 of N").

### Item 4 — Deposit-source door + negative-float tripwire (D6 paired)
- Movements door (`ui/api/routers/cash_flow.py:188-331`): a deposit to
  a **Tim** account-at-book defaults to the paired write — one door
  action creating `account_holder_funding` + `account_at_book_deposit`
  (linked via `parent_event_id`, source note "fresh bank money —
  standing rule S244"), so Tim's float nets zero. Other holders default
  to plain deposit ("from float"). An explicit override field
  (`source: bank|float`) lets either be chosen; the chosen source lands
  in notes. Frontend movements form: source selector pre-set by holder,
  one save.
- Reversal door (`cash_flow.py:462-585`) must reverse the PAIR when
  given either member (refuse-with-pointer or cascade both — pick
  refuse-with-pointer listing the sibling, attended-only, and say so in
  the report).
- Negative-float tripwire (non-blocking): per-holder `parked_pool`
  (`workflows/balances/v1/balance_derivation.py:514-568`) < 0 →
  (a) a line in `ops.settlement_review`'s NEEDS-YOUR-EYES block;
  (b) the same money-health banner surface as Item 7 ("Sarie's float
  reads −$X — a movement is missing its source"). Note in the report
  that it may flag until the Item 8 ledger pass lands (expected,
  operator-known).

### Item 3 — Small-field insurance honesty (Option A, largest — last)
- New nullable promo_template column `position_min_field TEXT` (JSON
  object mapping insured position → minimum field size, e.g.
  `{"3": 8}` for the BetRight variant), additive DDL + domain field +
  catalogue create/list surface, same path as Item 5's column.
- Frontend mapping: `buildConfigFromCatalogue`
  (`ui/web/src/promos/presets.ts:248-268`) carries it into the EV
  promo spec; `evInsurance` (`ui/web/src/ev/evEngine.ts:311-340`)
  drops an insured position when `fieldSize` (already computed from
  ACTIVE runners — D5) is below that position's minimum. EV output
  should expose which positions were dropped so the picker can say
  "3rd not covered — 7 runners" (plain chip near the promo EV, not a
  modal).
- Settlement parity: `credit_gap.py` expected-amount arithmetic
  (`workflows/promos/v1/credit_gap.py`, door-parity helper :94-102)
  and the credit-in insurance arm (`promos.py:350-363`) honour the same
  rule — a lost bet whose finish position's insurance was voided by
  field size must NOT be creditable, and the credit-gap detector must
  not list it as owed. Use the bet's stored field/runner facts at
  settlement time; if the needed field-size-at-jump fact is not
  persisted on the bet, persist it additively at placement
  (`workflows/bet_entry/v1/record_builder.py`) — note this in the
  report as the one placement-path touch, with its red-before test.
- Red-before on both sides: EV (7-runner field shows 3rd-insured EV
  today → drops it after) and credit-gap (owed today → not owed after).

### Addendum item 9 — shield "insurance triggered" state (operator, S246)
Operator feedback on UI pass #3: the 🛡 shows on every insurance bet;
he wants to see where the insurance actually TRIGGERED.
- Truth source: a non-superseded insurance credit (`free_bet_credited`
  or `promo_cash_credited`) whose triggering bet is this bet — the same
  correlation-group read `find_existing_credit` uses
  (`workflows/promos/v1/fb_credit.py:107-141`). Banked credit = the
  net caught the fall; do NOT infer from finish positions.
- Backend: additive read-only field on the bet feed items (e.g.
  `insurance_credit_amount: str | null`) derived at feed time; respect
  the list-limit rules (no silent caps).
- Frontend BetLog: plain shield = insurance riding (unchanged rule,
  `isInsuranceBet`); when `insurance_credit_amount` is set, render the
  distinct triggered state (filled/green shield) with hover
  "insurance paid — $X banked". Tests: riding vs triggered vs
  non-insurance.
- Display-only + one additive feed field; no money-path writes.

### Addendum item 10 — quick-lay joins its cycle at placement (operator, S246)
Operator priority: the insurance → FB → Betfair-lay chain must be linked
in the tool. FB→qualifier cycle inheritance already exists
(`resolve_inherited_cycle`, racing.py ~1028-1037) and the historical data
was backfilled in-session (see `cycle_linking_backfill_record.md`). The
missing forward piece: the race-page quick-lay never passes
`parent_cycle_id` (the lay door already accepts it — orchestrator
`HedgeRecordInputs(cycle_id=request.parent_cycle_id, …)`), so every lay
lands in a fresh cycle.
- At quick-lay time, resolve the candidate parent cycle server-side:
  bets on the same (betfair_market_id, betfair_selection_id) via
  bet_legs, placed within the last 24h, whose cycle does not already
  contain a LAY on that selection; prefer is_free_bet bets, then most
  recent. Unique candidate → pass its cycle_id as parent_cycle_id.
- Visible, not silent: the lay ConfirmCard shows the pairing in plain
  words ("pairs with your $50 FB on 4. Supernatural") with a way to
  decline (fresh cycle). Multiple candidates → show the choices, no
  default guess. Zero candidates → fresh cycle exactly as today; the
  existing unpaired-lay flag on the activity board remains the net.
- Tests: unique-match auto-pair, multi-candidate no-guess, zero-match
  fresh cycle, decline path. Display/grouping only — cycle_id is not a
  money field; placement money path otherwise untouched.

### Addendum item 11 — burst-review lay pairing + cycle-integrity watchdog (operator, S246)
Operator workflow (his words): he flags the trigger manually at credit-in;
the hedge lay follows the FB within ~5–20 seconds; anything that doesn't
match up must go to burst review for manual matching. Item 10 covers
placement time; this item is the catch-all and the tripwire.
- **Burst-review lay pairing:** unpaired lays (a Betfair LAY whose cycle
  contains no back bet) appear in the burst-review screen
  (`ui/web/src/routes/BurstReview.tsx`) with candidate cycles resolved
  the same way as item 10 (market+selection via bet_legs, recency
  ordered, FB backs first). Operator picks one → a small door
  (e.g. `POST /v1/bets/{bet_id}/assign-cycle`) sets the lay's cycle_id.
  Door rules: only LAY bets; target cycle must contain a back bet;
  refused otherwise with a plain reason. cycle_id is grouping metadata,
  not a money field — but log a parseable line for the daily check.
  An "unpair / fresh cycle" action for a wrong pairing (same door,
  target=new) keeps it reversible in-app.
- **Cycle-integrity watchdog (non-blocking):** a daily-check section in
  `ops.settlement_review`: (a) any Betfair LAY alone in its cycle
  ("unpaired lay — match it in burst review"); (b) any settled FB
  conversion bet (is_free_bet, settled) whose cycle contains no LAY,
  older than 30 minutes ("FB conversion unhedged or lay unlinked").
  Both listed with bet ids + selections. No banner for these (daily
  check only) — they are workflow nudges, not faults.
- Tests: pairing door happy/refusal paths, watchdog line shapes.

## Not in this build (stay out)
- The Item 8 ledger correction pass (main session, operator sign-off).
- FB expiry backfill on the two live banked credits (triage, operator
  present).
- Any change to the hard-delete fence (D2).
- Dogs/harness TAB coverage, watcher bands, race-page work — different
  workstreams.
