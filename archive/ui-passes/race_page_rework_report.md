# Race-page rework — build report

**Session:** Claude Code build session against bethub-v3, executing
`race_page_rework_brief.md` (LOCKED, incl. Addendum B) end to end.
**Started:** 2026-07-09 09:42 ACST. **Finished:** 2026-07-09 10:26 ACST.
**Start state:** clean tree, `main` = `9de0609` = origin/main (as required).
**End state:** clean tree, `main` = `51b62f7`, pushed to origin. Dist rebuilt
(app confirmed down first — only an unrelated bethub-v2 vite process was
running). Live store untouched; no Betfair contact; workers OFF throughout;
all tests against tmp-path fixture stores.

---

## 1. Read-and-confirm (stated before the first edit)

**Money fence (§9 + B7 exceptions).** No edits to placement
(`clients/betfair_client/`, `orchestrator.py`, `record_builder.py`,
`staking.py`, `bet_store_adapter.py`, `place_lay`'s guards/order-construction/
Betfair interaction), reconciliation (`reconciliation.py`,
`reconciliation_worker.py`, match-status writers), settlement
(`settlement.py`, `settlement_worker.py`, `ops/settlement_review.py`,
`update_settlement_state` + siblings, the settle door's fencing
`ui/api/routers/bets.py:862-931`), or credit-engine maths (`fb_credit.py`,
`fb_deployment.py`, `promo_derivations.py`, `credit_gap.py` gate logic,
`promo_store_adapter.py`, `balance_derivation.py`, the credit-in gate
`promos.py:190-304`). Only the named plumbing exceptions were used:
(a) manual-bet endpoint gains `consumed_credit_event_ids` and CALLS the
existing `record_free_bet_deployment`; (b) additive read-only store queries;
(c) an additive `promo_journey_annotation` write path for dismissals;
(d) credit-gaps include/exclude-dismissed parameter; (e) UI composition of the
existing settle + credit-in endpoints; (f) an additive promo-template create
endpoint (catalogue INSERT through the existing template shape); (g)
burst-review read-side derivations. No cycle machinery, no schema changes /
new tables / migrations.

**Build order (B8):** 5.2 board read-path → B1 top-bar flow + confirm card →
B2 new-promo card → B3 FB pending-source → 5.4 modal hand-off → 5.3 picker
bypass → B4 settle-and-bank → B5 burst review → 5.5 Log Past Bet → 5.7
rounding → 5.8 invalidation audit → 5.9 error labels. Cuts only from the
tail (none were needed).

**Bet-safety:** no Betfair contact of any kind; both workers stay OFF; the
live store (`data/bethub.db`, `~/.bethub/`) read-only/no-touch; all testing
on fixture/scratch DBs; no app launch against the live store; no bets, no
real settlements, no money moved. All honoured — the session never launched
the app at all (UI verified through the test suites + `npm run build`).

**Baselines recorded before the first edit:** backend `uv run pytest -q` →
**1399 passed**; frontend `npx vitest run` → **134 passed (19 files)**;
clean tree at `9de0609`.

---

## 2. Per-item outcome

### 5.2 Race activity board — **BUILT**
- Store: `_bets_filter_sql` gains optional `betfair_market_id` via an
  `EXISTS` over `bet_legs` (one-row-per-bet under multi-leg);
  `list_bets`/`count_bets` thread it (`store/repositories/bets.py:1063-1180,
  1485+`). Read path only.
- API: `GET /api/v1/bets` gains `market_id` (`ui/api/routers/bets.py`,
  `list_bets_feed`).
- UI: `ui/web/src/components/RaceActivityBoard.tsx` — always-visible bottom
  panel where the log panel lived: one compact line per position (side,
  person@book, selection, stake@odds, promo shape, colour state), detail on
  tap (B4 refinement), 5s poll + invalidation-driven refresh.
  **Unpaired-lay flag** derived display-level only: a LAY whose
  market+selection has no BACK renders `⚠ unpaired lay`. Partial lays show
  `Partial $x.xx` / `Unmatched` from matched-vs-requested. No stored state,
  no cycle machinery.
- Tests: `tests/ui/api/test_bets_market_scope.py` (exactness: exactly the
  market's bets, sibling exclusion, empty market, state-filter combination,
  unscoped feed unchanged); `RaceActivityBoard.test.tsx` (market-scoped
  call, compact lines, unpaired flag on the loner only, partial state).

### B1 Top-bar flow + confirm card — **BUILT**
- `ui/web/src/components/TopBar.tsx`: one bar — [person ▾][book ▾] │ promo
  rail │ [Free bet][No promo][+ new]. Book select shows only that person's
  account-at-books. Armed state lives in `Racing.tsx` state and persists
  across races; every element independently re-tappable.
- **Recency rail:** derived read-only from the existing bet feed
  (`fetchBetFeed({book_id, limit:200})`, key `['bets','promo-recency',book]`
  so every log refreshes it) — first appearance in the newest-first feed is
  the rank; unused promos follow in catalogue order.
- **Shape-first labels:** `ui/web/src/promos/shape.ts`
  (`promoShapeLabel`: `2nd → Bonus`, `2nd/3rd → Cash`,
  `Winnings → Bonus`), name secondary in small type.
- **Confirm card** (`ui/web/src/components/ConfirmCard.tsx`): runner-click
  (the LOG action on the odds row) opens it — runner, odds (editable),
  stake **pre-filled from the armed promo's cap and editable with a
  "(cap — check the slip)" hint**, promo shape, person@book, and the
  auto-set `safety_net` tag as a visible chip — single **Log** action. No
  logging path skips it. Two-click logging per the walkthrough.
- **safety_net auto-tag (§5.1(5)):** payload carries
  `strategy_tag:"safety_net"` iff the armed config is insurance-shaped
  (`promo_type === 'insurance'`, which catalogue insurance rows always
  produce); nothing else is tagged. The credit-in gate untouched.
- Idempotency key per submission (regenerated on success), same server
  mechanism as before. Success → persistent toast (`Logged: <runner> $X @
  Y · person@book · shape · safety_net`) above the board, until the next
  action. Saturday shape holds: promo + person@book stay armed; only the
  FB source resets after each log.
- Tests: `Racing.flow.test.tsx` rewritten end-to-end (tag lands on
  insurance, cap prefill `25`, no tag with no promo, soft odds persist,
  card closes, toast shows); `ConfirmCard.test.tsx`; `TopBar.test.tsx`
  (shape-first, recency ordering, toggle-off).

### B2 New-promo card — **BUILT**
- Backend: `POST /api/v1/promos/templates` (`ui/api/routers/promos.py`) —
  additive catalogue INSERT through the existing
  `PromoStoreAdapter.create_template` door; exactly two creatable kinds
  (`insurance` / `bonus_winnings`), insurance requires ≥1 refund position;
  `extra="forbid"`. No engine/maths edits.
- UI: `NewPromoCard` in `TopBar.tsx` — two-category radio, dials (refund
  positions 2nd/3rd/4th; returns bonus/cash; cap; bonus % for
  bonus-on-winnings), auto-generated name (`<book> — <shape> $<cap>`,
  editable), the day-1 nudge verbatim in spirit: *"Enter the terms as shown
  on THIS account's betslip — the same promo can differ per account at the
  same book."* Save creates the template, invalidates the catalogue, and
  **arms it immediately**.
- Tests: backend (create + appears in catalogue, insurance-needs-positions,
  bonus shape, free-form kinds rejected 422); frontend (dial→payload,
  immediate arming, exactly-two-categories).

### B3 Free-bet spend-now-file-later — **BUILT**
- TopBar FB mode lists the armed account-at-book's banked bonuses
  (log-context, multi-selectable) PLUS the standing **"bonus not banked
  yet"** option with a typed face value (+$25/$50/$100 quick buttons).
  Pending and banked are mutually exclusive. Selecting pending logs the bet
  `is_free_bet=true` with **no** `consumed_credit_event_ids` (representable
  today, no schema change); the confirm card shows a `source pending` chip
  and the success toast routes to the burst review. FB mode with no source
  is blocked — never a silent unfiled/cash log. A mid-burst spend never
  blocks on settlement or banking.
- Backend read side is B5's `source-pending-spends` derivation (below).
- Tests: `ConfirmCard.test.tsx` (banked → ids; pending → no ids + flag;
  no source → blocked), `TopBar.test.tsx` (mutual exclusion), backend
  `test_bets_manual_fb_drawdown.py::test_manual_fb_without_credits_is_source_pending`.

### 5.4 Modal hand-off — **BUILT**
- `Racing.tsx` `onPlaced`: modal closes (existing auto-close), the toast
  states matched/unmatched, and `invalidateBetSurfaces` refreshes the board
  immediately — the new lay appears with its matched/partial state. The
  frozen `HedgeHandoff` banner and its plumbing are **retired** (state,
  props, CSS removed). Partial wording stays plain. The modal still sends
  no `cycle_id`/`bet_id` (demotion direction respected — no link added).

### 5.3 Betfair picker bypass — **BUILT**
- `Racing.tsx` computes the Betfair AAB set from the page-level listing;
  exactly ONE → auto-selected via effect, ⚡ goes straight to the
  HedgeModal; ZERO → the picker renders (its existing red "none registered"
  message); TWO+ → the picker returns automatically. `BetfairAccountPicker`
  is bypassed, not deleted; `place_lay` untouched.
- Tests: `Racing.picker.test.tsx` — sole-AAB straight-to-modal (picker never
  shows) and two-AAB picker-returns, plus the original component tests.

### B4 One-tap settle-and-bank — **BUILT**
- Board rows (detail on tap) offer **Won / Lost** one-tap settles on pending
  soft-book bets and **"Lost — placed, bonus landed"** on the credit-in
  gate's own shape (pending soft-book + `safety_net` + promo attached):
  `settleBet(id,'lost')` then `creditIn(id)` — the two EXISTING doors in
  sequence, UI composition only. A credit-in failure after a landed settle
  still refreshes so the surface tells the truth.
- BetLog equivalent: same composed button in the settle group
  (`BetLog.tsx`), behind the page's usual `window.confirm` (consistent with
  its other money-moving settles — see design calls).
- Tests: compose-order asserted in `RaceActivityBoard.test.tsx`,
  `BetLog.test.tsx` (incl. not-offered without the shape), and
  `BurstReview.test.tsx`.

### B5 Burst review — **BUILT**
- Backend (`workflows/promos/v1/burst_review.py`, new, additive):
  `list_source_pending_spends` (free-bet BACKs minus `free_bet_deployed`
  events by `deploying_bet_id` — read-side only, B7(g));
  `list_dismissed_credit_gap_bet_ids`; `record_credit_gap_dismissal`
  (§9(c), below). Endpoints: `GET /v1/promos/source-pending-spends`,
  `POST /v1/promos/pair-spend` (validates bet exists / is a free bet / same
  account-at-book as the credit, then writes through the EXISTING
  `record_free_bet_deployment` — §9 exception (a) extended per B7).
- UI (`ui/web/src/routes/BurstReview.tsx`, new route `/burst-review`): four
  sections — (a) unsettled soft-book bets with Won/Lost/Void + the composed
  bonus-landed tap; (b) source-pending spends with **pairing**: exactly one
  matching-face credit at the same account-at-book → one-tap "Pair with
  $X credit"; multiple → "ambiguous — pick the credit:" with each candidate
  its own explicit tap (**never guessed**); none → "no matching credit yet"
  stays flagged; (c) banked-but-unspent credits (log-context fan-out over
  all registered AABs); (d) the credit-gaps backstop with per-item "Bonus
  landed → bank" (credit-in) + "Dismiss" and an include-dismissed toggle.
  Zero-flags state declared explicitly ("All clear — zero flags").
- **Acceptance (brief §7/B5) — PASSED:**
  `tests/ui/api/test_promos_rework.py::test_conversion_day_reconciles_to_zero_flags_in_one_pass`
  builds the full conversion-day shape on a fixture store (two pending
  safety-net qualifiers, one mid-burst FB spend with no source), runs ONE
  pass (settle ×2 → credit-in → pair-spend → dismiss), and asserts zero
  flags: pending feed empty, source-pending empty, credit-gaps empty,
  inventory 0.

### 5.6 Credit-gaps dismiss — **BUILT** (folded into B5 as the backstop)
- Dismissal = one additive `promo_journey_annotation` event
  (`record_credit_gap_dismissal`): `book_id` required / `account_id` None
  per the FK matrix, tags `['credit_gap_dismissed', 'bet:<bet_id>']`,
  confidence CONFIRMED — durable across restarts, no new table, no schema
  change. `GET /credit-gaps` gains `include_dismissed` (default false
  excludes; true returns items marked `dismissed: true` via the additive
  `CreditGapItem` response model). `credit_gap.py` untouched.
- **Eligibility proof:** `test_dismiss_does_not_touch_credit_in_eligibility`
  — a dismissed qualifier still credits 201 through the untouched gate.
  Hide/persist/retrieve proven across fresh per-request connections.

### 5.5 Log Past Bet — **BUILT**
- Backend: `ManualBetCreateRequest` gains
  `consumed_credit_event_ids: list[UUID]` and, after the bet write, calls
  the EXISTING `record_free_bet_deployment` with the racing route's
  non-fatal contract (failure → `FB_DEPLOY_EVENT_WRITE_FAILED`, bet never
  rolled back). `BetFeedItem` gains an additive `warnings` field (empty on
  feed reads) to carry it. Draw-down proven via
  `compute_free_bet_inventory` before (1 FB) / after (0 FB) on a fixture
  store; the bad-credit path proven warning-not-rollback with inventory
  untouched.
- UI: persistent **"✓ Bet saved"** panel naming the bet (id, selection,
  stake, outcome, + credit/draw-down/source-pending lines), surviving until
  the next action; FB inventory checkboxes from the same log-context source
  as the race page; the B3 pending option; blocked when FB with no source.
  Double-submit guard: disabled-while-pending + field reset on success (see
  design calls for why not a server key). Invalidation after save and after
  the credit-in side-effect.

### 5.7 Display rounding — **BUILT**
- BetLog: `@ price` → 2dp (`price2dp`), FB conversion → 2dp (`rate2dp`) —
  the `10.000000000000002` artifact class closed; HedgeModal confirmation
  line price → 2dp; board/burst-review/confirm-card/Log-Past-Bet money all
  `toFixed(2)`; OddsTable keeps its conventional tiered odds precision.
- **Display-only proven:** BetLog test feeds `matched_price
  10.000000000000002` → renders `@ 10.00` while the edit input still
  carries the exact stored value. No write-path rounding anywhere.

### 5.8 Invalidation audit — **BUILT** (after-matrix in §3)
- Central sweep `ui/web/src/hooks/invalidations.ts`; every mutation on the
  logging/promo surface routes through it. The provisional manual-queue
  resolution — previously refreshing only its own key — now sweeps the
  family too (a manual resolution IS a settlement).

### 5.9 Error labels — **BUILT**
- `ui/web/src/api/errors.ts`: prices/feed 5xx → "Prices are unavailable —
  the app can't reach its data feed right now. (…)"; lay 503 with
  `betfair_streaming_disconnected` → "Placement refused — the live Betfair
  feed is down, so the safety interlock blocked this lay. (…)"; other lay
  503s truthfully "Betfair is unreachable", 409s "Betfair rejected the
  lay (reason)"; general 5xx/4xx mapping leads with the server's
  operator-meaningful detail. Technical detail kept secondarily in
  parentheses. Wired to the prices banner, HedgeModal, board, BetLog,
  Log Past Bet, burst review. Unit tests pin both named cases.

---

## 3. §5.8 mutation → invalidation after-matrix

`invalidateBetSurfaces` ≡ `invalidatePromoSurfaces` ≡ invalidate
`['bets']` (activity board + recency rail + review-pending + provisional
queue), `['betlog']`, `['racing','log-context']` (balances + FB inventory),
`['accounts']`, `['registrations']`, `['review']` (burst-review listing +
credits), `['promos']` (catalogue + credit-gaps + source-pending).

| # | Mutation | Call site | After state |
|---|---|---|---|
| 1 | Race-page log bet (confirm card) | `Racing.tsx handleLogged` | full sweep + toast; FB selection reset |
| 2 | HedgeModal lay placement | `Racing.tsx onPlaced` | full sweep (was: **nothing**) |
| 3 | New-promo template create | `TopBar NewPromoCard` | `['promos','catalogue']` (only the catalogue changes) + immediate arm |
| 4 | BetLog edit | `BetLog invalidate()` | full sweep (was: `['betlog']` only) |
| 5 | BetLog delete | same | full sweep |
| 6 | BetLog settle (won/lost/void) | same | full sweep (settle-lost now surfaces on credit-gaps immediately) |
| 7 | BetLog credit-in ("Placed?") | same | full sweep |
| 8 | BetLog "Lost — bonus landed" (B4) | same | full sweep, incl. on partial failure |
| 9 | Board settle / bonus-landed (B4) | `RaceActivityBoard` | full sweep, incl. on partial failure |
| 10 | Log Past Bet create (+ credit-in side-effect) | `LogPastBet onSuccess` | full sweep (was: **nothing** — the S234 silent-save class) |
| 11 | Burst review settle / bonus-landed / bank / dismiss / pair | `BurstReview` | full sweep, incl. on error (partial composes stay honest) |
| 12 | Provisional manual-queue resolution | `Provisional handleResolved` | full sweep (was: own key only) |

Reads are namespaced to be swept: board `['bets','market',id]`, recency
`['bets','promo-recency',book]`, review-pending `['bets','review-pending']`,
credit-gaps `['promos','credit-gaps',flag]`, source-pending
`['promos','source-pending']`, review credits/listing `['review',…]`,
log-context `['racing','log-context',aab]`. Regression guards where the
harness supports them: the S234 classes are covered behaviourally (board
refresh assertions ride the mocked-fetch call counts; the matrix itself is
enforced structurally by every call site using the one helper — grep-able).

---

## 4. Design calls made

1. **"Burst review" naming collision resolved by renaming the old page.**
   The W8 provisional queue held the nav label "Burst review" but is
   operationally the settlement worker's **manual park queue** (the
   operator's standing vocabulary since S227). New screen takes the "Burst
   review" label at `/burst-review`; the queue page is relabelled "Manual
   queue" (route `/provisional` unchanged).
2. **Recency derived client-side from the existing feed** (per-book,
   `limit:200`) rather than a new store query — the brief explicitly allowed
   either; zero new read surface was the smaller footprint, and the
   `['bets']` namespace makes it self-refreshing.
3. **safety_net trigger = armed `promo_type === 'insurance'`** (catalogue
   insurance rows and hand-dialled insurance configs both produce it), which
   is exactly "insured positions present" for every catalogue row, and also
   covers a manually-dialled insurance config.
4. **Manual-create FB deploy connection derives from the bet storage's own
   `_db_path`** (the same co-location rule the bet-mutation audit emit uses)
   rather than a new DI dependency — the events land in the store the bet
   was written to, in production and tests alike, and no scratch connection
   opens when there is nothing to deploy.
5. **Log Past Bet double-submit guard is UI-shaped** (disabled while
   pending; success clears stake/price/runner so `guard()` blocks an
   identical resubmit; the persistent panel removes the "did it save?"
   doubt that caused S234's duplicate). A server-side idempotency key would
   require `build_manual_bet_record`/`record_builder.py` — inside the §9
   placement fence — so it was not attempted. Recorded as a residual (F3).
6. **Pair-spend endpoint pairs exactly the named pair**; ambiguity handling
   lives in the UI (single match → one tap; multiple → each candidate an
   explicit tap; none → flag stays), per "listed, never guessed".
7. **B4 on BetLog keeps `window.confirm`** (consistency with its existing
   settle doors); the board and burst review are true one-tap (their
   detail-on-tap/table context is already a deliberate step).
8. **TopBar retains compact EV dials** (cap / return % / insured / return
   type) for the armed promo — the EV columns still need their knobs; the
   slip-confirmed stake lives on the confirm card as specified.
9. **`invalidateBetSurfaces` sweeps `['promos']` too** — settling a
   qualifier lost puts it ON the credit-gaps list, so bet mutations move
   promo reads; one class-wide sweep beats a divergence-prone split.
10. **Dismissal↔bet linkage rides the annotation's open tag vocabulary**
    (`bet:<bet_id>`) — annotations reference events, not bets, and the brief
    barred new tables; the payload's `promo_template_id` keeps the
    adapter-side reference validation honest.

## 5. Suite counts

| Suite | Baseline (`9de0609`) | Final (`51b62f7`) |
|---|---|---|
| Backend `uv run pytest -q` | 1399 passed | **1418 passed** (+19) |
| Frontend `npx vitest run` | 134 passed (19 files) | **160 passed (22 files)** (+26 net; LogBetPanel/PromoBar suites retired with their components, coverage re-homed) |

Both suites were green at every commit. `npm run build` (tsc -b + vite)
passes; dist rebuilt with the app down.

## 6. Commits (all on `main`, pushed to origin)

1. `c4af385` — backend: market-scoped feed, promo-template create,
   credit-gaps dismiss, burst-review reads, manual FB draw-down (+ B5
   acceptance test).
2. `87a66ec` — UI core: top-bar flow, confirm card, activity board, FB
   pending-source, modal hand-off, picker bypass (LogBetPanel + PromoBar
   retired).
3. `cd21314` — B4 + BetLog sweep: composed 'Lost — bonus landed', 2dp
   rounding, class-wide invalidation.
4. `c32537b` — B5: burst-review screen at `/burst-review`; manual-queue nav
   rename.
5. `3161c01` — 5.5: Log Past Bet confirmation, FB draw-down, B3 pending
   source, invalidations.
6. `ff542d3` — 5.7/5.8/5.9 sweep: rounding, invalidation audit (incl.
   provisional queue), plain-language errors + tests.
7. `51b62f7` — fix: TS types for `consumed_credit_event_ids`/`warnings`
   (caught by the dist build's project-wide tsc).

## 7. Findings & surprises

- **F1 — `vitest` does not typecheck and a bare `npx tsc --noEmit` mid-run
  gave a false clean:** the missed TS type additions surfaced only at
  `npm run build` (tsc -b). Nothing shipped broken (caught in-session,
  commit 7), but future briefs should treat `npm run build` as the
  frontend's real gate, not vitest alone.
- **F2 — credit-gaps response shape gained a field:** `CreditGapItem`
  subclasses `UncreditedQualifier` with `dismissed: bool`. Additive (all old
  fields intact); any external consumer of the bare list shape sees one new
  key.
- **F3 (residual, LOW) — Log Past Bet has no server-side idempotency key**
  (see design call 5); the S234 duplicate shape is guarded at the UI. A
  server key needs a `record_builder.py` touch → fenced; route it with a
  future money-path-adjacent brief if wanted.
- **F4 (residual, LOW) — burst-review credits section fans out one
  log-context request per registered account-at-book** (13 pairings today).
  Fine at this scale; an aggregate endpoint is a later nicety.
- **F5 — the W8 "Burst review" nav label was already taken** by the
  provisional park queue; resolved by rename (design call 1). The operator
  should be told the queue now reads "Manual queue".
- **F6 — pair-spend inherits Addendum-A's known write-door softness**
  (`record_free_bet_deployment` does not check the credit is already
  superseded; single-spend is enforced on read). The UI only offers
  *available* credits so the exposure is unchanged from the race-page path;
  the write-time hardening rides the demotion build as already agreed.
- **F7 — `LogContextResponse`/log-context endpoint untouched** — B3/B5
  needed nothing new from it; banked-credit reads reuse it verbatim.
- No fence pressure was encountered anywhere: no §5 item required crossing
  §9 (nothing was stopped/blocked).

## 8. Live-integration classification (S189 honesty)

Everything below is **implemented-not-live** until the operator's next
racing day (which is also the standing tick-1 attempt). What the live look
must confirm, per item:

- **5.2 board:** real bets on a real race appear within a poll/mutation
  beat; the unpaired-lay flag fires on a genuinely unpaired lay and clears
  once the back is logged; partial lays show live matched figures.
- **B1:** the Saturday shape — one rail tap then runner-click + confirm per
  bet — holds up at burst pace; the cap prefill matches real betslips and
  the slip-override habit sticks; `safety_net` visibly on the card and on
  the logged row (BetLog tag column).
- **B2:** a real new promo entered from a real betslip lands in the
  catalogue, arms, EVs sensibly, and its credit later banks through the
  gate (return_pct semantics on a non-100% promo deserve one live check).
- **B3:** a mid-burst unbanked-bonus spend logs without friction and shows
  up as source-pending in the burst review the same evening.
- **5.4:** a real lay drops onto the board immediately with its true
  matched state (no stale board — the four-times-bitten class).
- **5.3:** ⚡ goes straight to the modal on the sole Tim@Betfair reality.
- **B4:** a real lost qualifier settles+banks in one tap and the money-check
  lens shows `reason=operator_manual` + the credit event.
- **B5:** the end-of-day pass reaches "All clear — zero flags" on a real
  conversion day without Claude-supervised corrections — this is the tick-1
  evidence itself.
- **5.5:** a real after-the-fact entry produces the unmistakable panel (no
  double entry), and a real FB draw-down drops the credit from inventory.
- **5.7:** no float artifacts on real settled rows.
- **5.8:** no stale page anywhere across a full live day.
- **5.9:** if the interlock trips live, the wording matches the truth of
  the refusal.

## 9. Self-assessment against §9

Files inside the fence: **zero edits**. `git diff 9de0609..51b62f7
--name-only` touches: `store/repositories/bets.py` (additive read-only
filter param only — the file's writers untouched), `ui/api/routers/bets.py`
(feed param; manual-create field + call to the existing deployment writer;
additive `warnings` field — the settle door's fencing at `:862-931`
byte-identical), `ui/api/routers/promos.py` (new endpoints + include-
dismissed; the credit-in gate block `:190-304` untouched),
`workflows/promos/v1/burst_review.py` (new file: reads + the permitted
annotation write), tests, and `ui/web/**`. Not touched: any
`clients/betfair_client/` file, `orchestrator.py`, `record_builder.py`,
`staking.py`, `bet_store_adapter.py`, `reconciliation.py`, both workers,
`settlement.py`, `ops/settlement_review.py`, `fb_credit.py`,
`fb_deployment.py`, `promo_derivations.py`, `credit_gap.py`,
`promo_store_adapter.py`, `balance_derivation.py`, `place_lay` internals.
No cycle wiring added or removed (the modal still sends no cycle link; no
new `cycle_id` senders). No schema change, no migration, no new table
(dismissals are events; source-pending is derived). Workers stayed OFF;
no Betfair contact; live store untouched; no bets placed; nothing real
settled; no money moved. Git: descriptive commits with the co-author
trailer, pushed to origin main, no DBs or secrets committed, no history
rewritten.

All twelve B8 items built; nothing cut; no fence findings.

<!-- RACE PAGE REWORK COMPLETE -->
