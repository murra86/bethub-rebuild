# B2 build report — money-safety doors (S246, 20 Jul 2026)

**Base:** `f28a7ef` → **HEAD `a2fac2d`** (10 commits, pushed to origin/main).
**Brief:** `b2_build_brief.md` (items 5, 6, 2, 1, 7, 4, 3 + operator addenda 9, 10, 11).
**Gate: GREEN** — backend `uv run pytest` **1615 passed** (baseline 1530, +85);
frontend `npm run build` clean AND `npx vitest run` **280 passed** (baseline 255, +25).
No live DB writes; no app or worker started; promo/cash spines stayed append-only;
every settlement/credit/EV behaviour change carries a red-before/green-after test.

---

## Item 5 — FB expiry stamped at credit time

**What it protects:** Sarie's $13 nearly died silently — TAB bonuses expire in
7 days but the tool banked them immortal. Now a dying bonus is visible (and
eventually drops from the pool) instead of counting as ammunition you no
longer have.

**Built:** per-template `fb_expiry_days` column (additive DDL,
`store/schema/promos.py:266-270`; domain `domain/promos/__init__.py` on
`PromoTemplate`; row/adapter plumbing `store/repositories/promos.py`,
`workflows/promos/v1/promo_store_adapter.py`). The credit door stamps
`face_value_expiry = credit time + N days` on FB credits
(`workflows/promos/v1/fb_credit.py:157,229-236`); cash credits stay
expiry-less by design. Catalogue read + create door carry the field
(`ui/api/routers/promos.py`); credit-in passes the template's window through.
The existing surfacing chain (read-time drop + earliest-first sort) was
verified, not rebuilt. Frontend: new-promo card grows "bonus expires (days)"
(`ui/web/src/components/TopBar.tsx`); TopBar + Log Past Bet FB rows show the
date, red inside 48h (shared `fbExpiryInfo`, `ui/web/src/api/promos.ts`).

**Tests:** `test_fb_expiry_days_stamps_face_value_expiry` (red-before proven:
TypeError then None-stamp), `test_no_fb_expiry_days_keeps_expiry_none`,
`test_cash_credit_ignores_fb_expiry_days`,
`test_stamped_expiry_surfaces_in_inventory` (tests/workflows/promos/v1/
test_fb_credit.py); `test_credit_in_stamps_template_expiry_window`
(test_promos_credit_in.py); `test_template_create_round_trips_fb_expiry_days`
(test_promos_rework.py); frontend `promos.test.ts` (fbExpiryInfo 48h rule).

**Triage list (read-only, live DB):** existing templates that would need the
window set when you next touch them — `TAB Bonus Winnings 25% to $100 (FB)`
(= 7 days), and the FB-returning insurance templates if their book's terms
carry expiry: `Ins $25 FB 2+3`, `Ins $25 FB 2nd`, `Ins $50 FB 2+3`,
`Ins $50 FB 2nd`, `Ins 2nd Winnings FB $100`. No live write was made.

## Item 6 — manual-amount credit door (general valve, D9)

**What it protects:** dead-heat / removed-runner bonus wins had no in-app
home — the hand-computed credit lived outside the tool, exactly what v3
exists to end.

**Built:** `POST /v1/promos/manual-credits`
(`ui/api/routers/promos.py:479`) → `record_manual_amount_credit`
(`workflows/promos/v1/fb_credit.py:263`): operator amount + mandatory reason
+ triggering bet + bonus/cash + optional explicit expiry. Same
once-per-bet guard as credit-in — shared both ways (manual then auto =
already_credited; auto then manual = REFUSED naming the existing event).
Marked `credit_source='operator_manual_amount'` (new enum value,
`domain/promos/__init__.py`, with its own payload validation); shows as
"manual credit" on the board (`promo_derivations.py`); the daily money check
grows **MANUAL CREDITS TODAY** (`ops/settlement_review.py:305`). The auto
door's dead-heat / no-price 422s now point at the manual door. UI: settled
promo rows in BetLog grow "Manual credit…" (amount + kind + reason,
`ui/web/src/routes/BetLog.tsx`).

**Tests:** `test_manual_credit_banks_operator_amount_with_reason`,
`test_manual_credit_second_attempt_refused_naming_existing`,
`test_manual_credit_shares_guard_with_auto_door`,
`test_manual_credit_honours_explicit_expiry_on_fb`,
`test_manual_credit_refuses_bad_input` (4 shapes),
`test_dead_heat_refusal_points_at_manual_door` (test_promos_credit_in.py);
`test_build_report_lists_manual_credits` (+quiet twin,
tests/ops/test_settlement_review.py); frontend BetLog manual-credit pair.

**Deviation:** a second credit is REFUSED (422, existing event named), not
silently returned as already_credited — an operator-typed amount that
differs from an existing credit must never look banked.

## Item 2 — auto-restore on void (D3: both reasons)

**What it protects:** a book voids your FB bet (scratched runner / market
void) and hands the free bet back — the tool's pool now gets it back too,
without you remembering the manual restore door.

**Built:** both resolvers' VOIDED writes call
`_auto_restore_free_bets_on_void`
(`workflows/bet_entry/v1/settlement.py:1192`, hooks at `:1383` and `:1669`):
each `free_bet_deployed` event the voided bet wrote is superseded by a
corrective credit through the EXISTING restore primitive — SYSTEM source,
reason `auto_restore_on_void: <reason>`, idempotent via a new
`FreeBetAlreadySupersededError` split (`workflows/promos/v1/fb_restore.py`;
`record_free_bet_restore` gained a `source` param, manual door unchanged at
OPERATOR). Non-blocking by contract: a failure logs a parseable
`FB_AUTO_RESTORE_FAILED` warning (which the daily check's problems section
surfaces) and never blocks the void — the FB_DEPLOY_EVENT_WRITE_FAILED
pattern.

**Tests (red-before proven — the pass left the pool drained $0):**
`test_void_restores_consumed_fb_to_inventory`,
`test_provisional_void_also_restores`, `test_restore_is_idempotent_on_repeat`,
`test_void_without_fb_writes_nothing`,
`test_restore_failure_never_blocks_the_void`
(tests/workflows/bet_entry/v1/test_settlement_auto_restore.py).

**Note:** the operator settle door's manual Void (BetLog) does NOT
auto-restore — you're present and the restore door is one tap away; only the
worker's void paths are coupled (the brief named "both resolvers").

## Item 1 — re-class door (keystone)

**What it protects:** the BetRight phantom — a bogus terminal verdict sat in
your P&L forever because no door could change won/lost/void to anything else.

**Built:** `POST /v1/bets/{bet_id}/reclass`
(`ui/api/routers/bets.py:1306`): any terminal → any other terminal (D1),
mandatory reason; refused for pending/provisional (own doors) and Betfair
bets (worker's lane, same 422 as the settle door); the row is never deleted
(D2 — delete fence untouched). Audit: `BET_RECLASSED` added to the domain
enum + payload (from/to/reason/snapshot, `domain/bet_mutations/__init__.py`)
and the store CHECK extended via a one-time table rebuild that preserves
every row (`store/schema/bet_mutations.py:136` — SQLite can't ALTER a
CHECK). Same parseable log shape as the settle door
(`reason=operator_reclass`) so the daily check counts re-classes with no new
parser. **Linked-promo fence** (`bets.py:1198`): any non-superseded credit
triggered by the bet blocks EVERY flip (its amount was computed off the old
outcome); an FB deployment blocks a flip TO void (the spend gets its face
back) — refuse-with-list naming each event id and its fixing door
(credit-revocations / deployment-corrections), no auto-cascade. Won↔lost
flips leave deployments standing. Settlement facts (dead-heat counts) are
carried forward on the write, not NULLed. Frontend: BetLog "Re-class…" with
verdict picker + reason + plain-language money consequence; P&L invalidates
via the existing sweep.

**Tests:** tests/ui/api/test_bets_reclass.py (14 — terminal↔terminal ×4,
audit row content, log line parses with the review's own regex, Betfair /
non-terminal / same-state / no-reason / unknown fences, credit-blocks-then-
revoke-then-succeeds, deployment-blocks-void-but-not-flip);
`test_reclass_check_migration_rebuilds_old_table` (red-before: the old CHECK
refuses `bet_reclassed`; rows survive the rebuild) + fresh-store twin
(tests/store/repositories/test_bet_mutations_repository.py); frontend
BetLog re-class trio (happy path, hidden on Betfair/pending, refuse-with-list
message surfaces).

## Item 9 (addendum) — shield shows where insurance TRIGGERED

**What it protects:** the 🛡 marked every insurance bet the same; you
couldn't see at a glance where the net actually caught the fall.

**Built:** additive read-only feed field `insurance_credit_amount`
(`ui/api/routers/bets.py` BetFeedItem; derivation
`_triggered_credit_amounts` at `bets.py:676` — one indexed promo-spine read
per page over the credit-in guard's own correlation key, never inferred from
finish positions; clawed-back credits excluded — a revoke, or a rejected
cash credit; a SPENT credit still counts as paid; guarded so a promo failure
never breaks the feed, no caps). Frontend: riding = muted shield; triggered
= filled/green shield with hover "insurance paid — $X banked"
(`ui/web/src/routes/BetLog.tsx` + module CSS).

**Tests:** `test_feed_carries_triggered_credit_amount`,
`test_feed_credit_amount_cleared_by_revoke` (test_bets_reclass.py);
frontend `shows a plain shield while insurance rides and the paid state…`.

## Item 7 — void-detector wired (D10: report-only)

**What it protects:** a race that voids AFTER we settled it no longer sits
wrong silently — the tool tells you which settled bets Betfair now reads as
voided, and the fix is your re-class door.

**Built:** hourly throttled third pass in the settlement worker cycle
(`ui/api/settlement_worker.py:68,80` — in-process timestamp, first cycle
after start runs it; a sweep failure never breaks the cycle). Hits surface
three ways: (a) the detector's parseable per-hit WARNING lines (unchanged);
(b) a `money_health` block on `GET /api/health/workers`
(`ui/api/routers/health.py:95,200`, fed via the worker-health registry,
`ui/api/worker_health.py`) rendered by the banner — "N settled bets look
voided at Betfair — review in BetLog (Re-class…)"
(`ui/web/src/components/HealthBanner.tsx`); (c) a **SETTLED-THEN-VOIDED
WATCH** section in the daily check pointing each hit at the re-class door
(`ops/settlement_review.py:72,484`). Truncation honesty ("checked N of M —
more may exist") appears on all three surfaces.

**Tests:** `test_cycle_runs_void_sweep_on_first_cycle_and_throttles`,
`test_void_sweep_failure_never_breaks_the_cycle`
(test_settlement_worker.py); `test_void_flags_surface_and_flip_unhealthy`,
`test_clean_void_sweep_reports_healthy`,
`test_money_health_absent_before_first_void_sweep` (test_worker_health.py);
`test_void_detector_lines_get_their_own_section` (+quiet twin, tests/ops);
frontend `reports settled-then-voided flags and the truncation honesty`.

## Item 4 — deposit source door + negative-float tripwire (D6)

**What it protects:** "any Tim deposit at a book = fresh bank money" lived
only in memory — get it wrong and floats drift (the Sarie $300 class). And
nothing anywhere flagged a float below zero.

**Built:** the movements door takes `source: bank|float` on deposits
(`ui/api/routers/cash_flow.py:149`): **bank** = ONE save writes the
funding + deposit pair (float nets zero; both events validated before
either is appended; both carry "source: fresh bank money — standing rule
S244" in notes; response returns `paired_funding_event_id`); **float** =
today's single event, noted. The form pre-sets bank for Tim (`is_self`),
float for other holders, override visible
(`ui/web/src/routes/Balances.tsx`). Reversal door: a pair member
refuses-with-pointer naming its sibling; `?include_sibling=true` reverses
BOTH in one attended action (`cash_flow.py:577`+). Tripwire:
`ui/api/money_health.py` derives per-holder floats (read-only, `mode=ro`);
computed worker-side on the same hourly throttle (never a live-store read on
a health poll) into the banner's money-health block, and directly in the
daily check's NEEDS-YOUR-EYES (`ops/settlement_review.py:246`) — "Sarie's
float reads −$X — a movement is missing its source (bank vs float)."

**Tests:** `test_bank_sourced_deposit_writes_pair_and_float_nets_zero`
(red-before = the existing `test_deposit_moves_both_locations` pinning
−325), `test_float_sourced_deposit_stays_single_but_noted`,
`test_source_is_deposit_only`,
`test_pair_member_reversal_refuses_with_pointer_then_reverses_both`,
`test_plain_deposit_reversal_needs_no_pair_confirm`,
`test_negative_float_tripwire_flags_and_clears`
(test_cash_flow_movements.py); `test_negative_float_lands_in_needs_your_eyes`
(tests/ops); `test_negative_floats_surface_through_money_health` (+healthy
twin, test_worker_health.py); frontend banner negative-float line test.

**Deviations (both attended-safety calls, say-so required by the brief):**
1. The pair links via a **shared `correlation_id`**, not `parent_event_id`
   as the brief sketched — that pointer is the ledger's established
   reversal link; reusing it would have marked the deposit itself as a
   reversal (breaking the movements list and its own reversibility).
2. Refuse-with-pointer chosen for pair reversal per the brief — but a pure
   refusal would deadlock (both members refuse each other), so the refusal
   names the sibling AND the explicit `include_sibling=true` confirmation
   that reverses both together. Attended, never silent cascade.

**Expected noise:** the tripwire WILL flag until the item-8 opening-balance
funding pass lands (floats currently read drained by seed money) —
operator-known, ships non-blocking by design.

## Item 3 — small-field insurance honesty (Option A, end-to-end)

**What it protects:** BetRight pays nothing for 3rd at ≤7 runners (standing
lesson, 19 Jul). The picker used to show insured-for-3rd EV on a 6-runner
field — you bet thinking you were covered when you weren't; and the tool
would happily bank (and chase) a credit the book will never pay.

**Built:**
- Catalogue term `position_min_field` (JSON position→min field, e.g.
  `{"3": 8}`): additive DDL (`store/schema/promos.py`), domain field,
  row/adapter plumbing, catalogue read + create door
  (`ui/api/routers/promos.py:145,710`); new-promo card grows "3rd needs ≥
  runners" when 3rd is insured (`TopBar.tsx`).
- EV honesty: `droppedInsuredPositions` + `evInsurance(..., fieldSize)`
  (`ui/web/src/ev/evEngine.ts:324,354`); `promoEV` feeds the ACTIVE runner
  count (D5 — scratchings degrade terms live). The race screen shows a plain
  chip: "3rd not covered — 7 runners… Promo EV already excludes it"
  (`OddsTable.tsx`, testid `insurance-position-dropped`).
- Settlement parity through ONE shared rule `covered_insured_positions`
  (`workflows/promos/v1/credit_gap.py:91`): credit-in REFUSES a qualifier
  whose EVERY insured position is voided at the bet's field size
  (`promos.py:386`), and the credit-gap detector no longer lists it as owed.
  Partial voids (2nd still covered) and pre-B2 bets (no field fact) stay
  operator-judged — never a silent drop of possibly-owed money.
- **The one placement-path touch** (as the brief anticipated):
  `field_size_at_placement` persisted at log — additive bets column
  (`store/schema/bets.py`), BetRow/BetRecord/adapters, request field
  `field_size_at_log` through racing route → orchestrator → record builder
  (`ui/api/routers/racing.py`, `workflows/bet_entry/v1/orchestrator.py`,
  `record_builder.py`); the race screen sends its active-runner count via
  the confirm snapshot (`Racing.tsx`, `ConfirmCard.tsx`). Grouped display
  metadata + a settlement input; no money arithmetic touched at placement.

**Tests (red-before proven on BOTH sides):** EV —
`2nd_3rd at 7 runners with 3rd min-8 prices like 2nd-only` (+helper, +inert
clause, +promoEV D5 wiring; evEngine.test.ts; failed before the engine
change); door —
`test_credit_in_refuses_when_field_size_voids_every_insured_position`
(failed 201-paying before the fix), `…pays_when_field_size_meets_the_minimum`,
`…stays_operator_judged_without_field_fact`, `…partial_void_still_pays`
(test_promos_credit_in.py); detector —
`test_fully_voided_insurance_is_not_listed_as_owed`,
`test_covered_field_size_stays_owed`, `test_partial_void_stays_listed`,
`test_missing_field_fact_stays_listed` (test_credit_gap.py); chip —
OddsTable `position_min_field chip` pair.

## Item 10 (addendum) — quick-lay joins its cycle at placement

**What it protects:** the insurance → FB → Betfair-lay chain finally links
in the tool — every lay used to land in a fresh cycle, so the chain's story
was invisible.

**Built:** shared candidate resolution
`workflows/bet_entry/v1/cycle_pairing.py:85` (backs on the same
market+selection within 24h whose cycle holds no lay on that selection;
FB backs first, then most recent; one per cycle) served by
`GET /v1/racing/lay-cycle-candidates` (`ui/api/routers/racing.py`). The
quick-lay modal (`HedgeModal.tsx`): unique candidate auto-pairs VISIBLY
("pairs with your $50 FB on 4. Supernatural") with a decline path; multiple
candidates present choices with NO default; zero = fresh cycle exactly as
today (the activity board's unpaired-lay flag stays the net). The chosen
cycle rides the existing `cycle_id` field on the lay request — the lay door
itself is untouched.

**Tests:** resolution — test_cycle_pairing.py (unique / zero / multi-with-
preference-order / cycle-with-lay excluded / 24h window / exclude_bet_id);
endpoint pair in test_bets_assign_cycle.py; UI — HedgeModal item-10 five
(auto-pair sends cycle_id; decline sends null; multi never guesses; picked
choice sends it; zero shows nothing).

**Note:** the historical cycle links were backfilled by the main session in
the live DB this session (`cycle_linking_backfill_record.md`); this build
touched no live data.

## Item 11 (addendum) — burst-review pairing + cycle-integrity watchdog

**What it protects:** when the auto-pair is declined or missed, the unpaired
lay would drift silently — now the burst review catches it and the daily
check says so.

**Built:** `GET /v1/bets/unpaired-lays` (`ui/api/routers/bets.py:1435`,
via `cycle_pairing.list_unpaired_lays:170` — lays in a back-less cycle, 24h
window, each with candidates) + `POST /v1/bets/{bet_id}/assign-cycle`
(`bets.py:1472`; storage write `update_cycle_id`,
`store/repositories/bets.py` — the only field it can move is `cycle_id`).
Fences: LAY-only; target must hold a back; one lay per selection per cycle;
`cycle_id: null` = unpair to a fresh cycle (reversible in-app — the burst
review's success note offers "Undo pairing"). Parseable line
`cycle assigned bet_id=…: old -> new (reason=operator_pair|operator_unpair)`.
Burst review grows "Lays not paired with a back" with per-candidate pair
buttons. Watchdog: **CYCLE PAIRING WATCH** in the daily check
(`ops/settlement_review.py:275`) — unpaired lays + settled FB conversions
with no lay linked 30+ minutes after placement
(`cycle_pairing.list_fb_conversions_missing_lay:247`). Daily check only, no
banner, as specified.

**Tests:** test_bets_assign_cycle.py (11 — pair happy path + log line,
unpair-to-fresh, non-LAY / back-less target / second-lay-on-selection /
unknown-bet+cycle refusals, unpaired-lays read, watchdog listing + quiet
twin); watchdog shapes also in test_cycle_pairing.py; UI — BurstReview
item-11 pair (pair on tap + undo affordance; no-candidate message).

---

## Suites and gate

- Backend: `uv run pytest` — **1615 passed** (baseline 1530; +85 new).
- Frontend: `npm run build` clean (the typecheck gate; dist on disk rebuilt,
  app down) and `npx vitest run` — **280 passed** (baseline 255; +25 new).
- HEAD **`a2fac2d`**, 10 commits `f28a7ef..a2fac2d`, **pushed to
  origin/main** with the full gate green.
- Fences honoured: no `data/*.db` write (the two live-DB touches are
  read-only `mode=ro` reads: the item-5 triage list and the standing
  correlation-stamp data assertion); no app/worker started; append-only
  spines (every promo/cash correction is a supersede or a linked opposite
  event); no silent caps (truncation surfaces on the void sweep's three
  surfaces; the feed's len-vs-total rule untouched).

## Needs an operator decision

> **S246 triage outcomes:** #1 RESOLVED — the operator's read was right:
> it was a wrong signpost, not a fence conflict. Soft-book bets (settled
> off the Betfair race result) re-class through the door; exchange bets
> are account-truth and the door stays shut for them — the watchdog now
> words the fix per venue (`22e3764`). #2 RESOLVED — the item-8 ledger
> pass landed mid-build; tripwire verified quiet. #3 CLOSED — both FBs
> already consumed; expiry is forward-only. #4 → operator worklist, set
> per template as they come up operationally (CrownBet + TAB first).
> Plus one triage hardening: the float tripwire now says could-not-run
> on a failed read instead of all-clear (`3a4a68e`).

1. **Betfair bets and the re-class door (fence conflict, not improvised).**
   The brief locks BOTH "re-class refuses Betfair-settled bets (worker's
   lane)" (item 1) AND "void-detector hits are fixed via the re-class door"
   (item 7/D10) — but the detector's hits can BE settled Betfair bets. As
   built, the lock wins: a flagged Betfair bet cannot pass the re-class
   door; its money fields remain editable (S237) but its verdict is stuck.
   Decide: allow Betfair terminal→VOID only (the detector's exact case), or
   keep the fence and handle the (rare) hit by hand. One-line change either
   way; I did not improvise around the lock.
2. **Item-8 ledger pass timing.** The negative-float tripwire is live in
   code and WILL flag current floats until your opening-balance funding pass
   lands. Expected and non-blocking — but the banner will carry the lines
   from the first hourly sweep after the workers next run.
3. **Item 5 backfill (D8, deferred to triage as locked):** Sarie $13
   (~25 Jul) and Leigh $33 are still expiry-less in the live spine. The
   supersede-correct pattern works when you want them stamped; and the
   triage list above names the templates to set `fb_expiry_days` on.
4. **BetRight templates need the new term set** (at triage, operator
   present): `position_min_field {"3": 8}` on the BetRight-variant insurance
   rows — the honesty rule only fires where the term is present.

## Honest status (S189) — implemented, not live

Everything in this build is **code + tests only; nothing has run against
live money yet.** First live confirmations to watch for:

- **Item 5:** first TAB credit through a template with `fb_expiry_days=7` →
  the FB row shows its expiry date in the TopBar panel.
- **Item 6:** first dead-heat bonus banked via "Manual credit…" → the line
  appears in that evening's MANUAL CREDITS TODAY.
- **Item 2:** first live scratched-runner/market void on an FB spend → pool
  refills automatically; look for the `FB auto-restore on void` log line
  (and no FB_AUTO_RESTORE_FAILED).
- **Item 1:** first real wrong verdict re-classed → BET_RECLASSED audit row
  + the day's review counting it under `reason=operator_reclass`. The CHECK
  rebuild migration runs once on first app start against the live store.
- **Item 9:** first insurance trigger after go-live shows the green shield
  with the banked amount on hover.
- **Item 7:** first worker session runs the void sweep within a minute of
  start, then hourly; a clean sweep = no banner, `money_health.healthy`.
- **Item 4:** first Tim deposit through the form defaults to "fresh bank
  money" and the float stays put; the tripwire lines appear until the
  item-8 pass lands (expected).
- **Item 3:** needs the BetRight term seeded (decision 4) AND bets placed
  after this build (older bets carry no field-size fact and stay
  operator-judged) — then a ≤7-runner BetRight race shows the "3rd not
  covered" chip and a lower promo EV.
- **Items 10/11:** first quick-lay after an FB back shows the visible
  pairing line; the first declined/missed pair appears in the burst
  review's new section and, if left, in CYCLE PAIRING WATCH that night.
