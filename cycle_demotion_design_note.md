# Cycle demotion — design note (derive-don't-store cycle groupings)

**Drafted:** 2026-07-08 20:03 ACST, Session 235 (headless runner, first action
auto-executed per S234 close).
**Status:** DRAFT — HELD for operator review. Nothing builds from this note
until the operator signs it off. No code was changed in drafting it.
**Substrate:** `sessions/SESSION_234.md` §12(a) (the operator-locked design
direction) + the S234 Findings. Every "already built" / "already linked" claim
below was grounded read-only against bethub-v3 at `9de0609` this session
(S178 rule).
**Governing DRs:** DR-019 (money derives on read — this note's core argument),
DR-027/028 (two-database boundary — the analytical-layer section respects
integration by reference), DR-032 (cycle_id as a plain column on bets, no
cycles table).

---

## 1. The call being proposed

Stop storing and regulating cycle groupings. Keep the promo-event chain the
store already writes (it carries every money-critical link), derive the
"cycle view" on read whenever someone wants to see a chain, and push deep
cycle profit-and-loss analytics to the analytical layer later. Delete the
regulation code that tries to keep a stored `cycle_id` stitched correctly —
the code that failed three different ways on conversion day.

In plain terms: today the tool tries to maintain a filing system that says
"these three bets belong together", and the filing system keeps missing
files. The proposal is to stop filing and instead answer "which bets belong
together?" by looking at the evidence every time — evidence the store
already keeps perfectly for money purposes.

## 2. Why — the day-2 evidence

Conversion day (S234) surfaced three failures of stored cycles in one
evening, none of which lost money but all of which needed Claude-supervised
corrections:

- **The lay modal orphans its cycle.** The HedgeModal never sends a cycle
  link with a lay (`PlaceLayRequest` accepts `cycle_id` but the modal omits
  it — `ui/web/src/components/HedgeModal.tsx:351-366`), so every lay starts
  its own one-bet cycle and the operator's conversions had to be joined by
  hand (3 manual joins on the day).
- **Log Past Bet can't link at all.** The manual-entry endpoint has no
  cycle field (`ui/api/routers/bets.py:1105-1243`) — a manually-logged
  free-bet back is always "its own cycle" by construction
  (`workflows/bet_entry/v1/record_builder.py:454`).
- **The stitching only covers one path.** The single piece of real
  inheritance logic (`resolve_inherited_cycle`,
  `workflows/promos/v1/fb_credit.py:206-254`) fires only on the race-page
  log flow when consumed credits are named. Every other door misses it.

Meanwhile the money was never at risk, because the money never depended on
`cycle_id` — see §3.

## 3. The grounding: the store already carries the real links

This is the load-bearing fact. The promo-event spine (one append-only
`promo_events` table, `store/schema/promos.py:99-136`) records the full
chain with hard references at every hop:

```
qualifier bet ──(credit payload triggering_bet_id)──▶ CREDIT event
CREDIT event ──(supersedes_event_id on the deploy)──▶ DEPLOYMENT event
DEPLOYMENT event ──(payload deploying_bet_id)──▶ free-bet back bet
free-bet back bet ──(same betfair market + selection, side=LAY)──▶ the lay
```

- Credit→qualifier: `fb_credit.py:140,167` writes the real qualifier bet
  UUID; the write **raises** rather than fabricate if it can't resolve it.
- Deployment→credit: `fb_deployment.py:161` sets
  `supersedes_event_id = credit_event_id` — the same mechanism that
  enforces single-spend (a spent credit vanishes from inventory the moment
  the deploy event lands; `promo_derivations.py:202-209`).
- Deployment→back bet: `fb_deployment.py:142` records the deploying bet.
- Back↔lay pairing: both legs store `betfair_market_id` /
  `betfair_selection_id` (`store/schema/bets.py:56-57`), and a store read
  for "other bets on this market" already exists
  (`store/repositories/bets.py:1009-1029`).

**Settlement never reads `cycle_id`** — confirmed by sweep: zero references
in `workflows/bet_entry/v1/settlement.py`. Balances never read it either
(`workflows/balances/v1/balance_derivation.py` works per-bet). The stored
cycle is bookkeeping decoration on top of money paths that are already
self-sufficient. Removing its regulation touches **no money maths**.

## 4. What the store KEEPS (unchanged — these are the money guards)

1. **The promo-event chain writes** exactly as they are: credit events with
   their qualifier reference, deployment events with their supersession +
   deploying-bet reference. These are DR-019-clean facts, not derived state.
2. **Free-bet inventory enforcement**: existence (a credit event must exist
   to spend), single-spend (supersession), and derived balances. Untouched.
3. **Promo attach on qualifiers** (`promo_template_id` on the bet) — this
   is what the credit gate and the watchdog key off, and what the race-page
   rework strengthens (shape-first picking, `safety_net` set at logging).

## 5. What DERIVES on read (the "chain view")

Wherever the operator wants to see a grouped cycle — BetLog's chain view,
the daily money check's "cycles touched today" rollup, the new race
activity board — the grouping is computed at read time from:

- **credit links**: qualifier → credit → deployment → free-bet back
  (walk the promo-event references in §3); plus
- **market/selection pairing**: a BACK and a LAY on the same
  `betfair_market_id` + `betfair_selection_id` for the same operator day
  pair as the conversion's two legs.

No new stored state, no cache (DR-028). A chain view computed this way
would have shown all four S234 conversions correctly with **zero** of the
manual joins the evening actually needed — the links it walks were all
present in the store before the joins were made.

## 6. What moves to the ANALYTICAL layer (via data capture)

Deep cycle economics — realised conversion rates across volume, cycle-level
P&L distributions, optimal odds bands for insurance cycles — belong to the
analytical layer (DR-027), fed by data capture, **integration by reference
only** (DR-028): the analytical side joins on the Betfair-side identifiers
the operational store already stamps on every bet, and on bet/event UUIDs.
Nothing is cached or denormalised across the boundary; no second
integration point.

Supporting fact: the operational store's own cycle-analytics hook is
already dead — `realised_conversion_rate` is structurally always NULL
(every write path inserts None; no settlement writer exists —
`record_builder.py:331,416,573`, zero UPDATE sites repo-wide). The
"analytics in the operational store" road was never actually driven.
Demotion makes that honest instead of latent.

## 7. What regulation is REMOVED (the code this retires)

The stored `cycle_id` column itself can stay in place, inert, per DR-032 —
removal is of the *regulation*: the code that generates, inherits, and
polices it. Grounded inventory of what retires or re-bases:

| Today | Under demotion |
|---|---|
| Cycle inheritance/stitching: `resolve_inherited_cycle` (`fb_credit.py:206-254`), hedge→soft-book copy (`orchestrator.py:529-536`), fresh-cycle minting at log/lay/manual doors | **Removed.** Nothing mints or stitches; chain views derive per §5 |
| The modal's missing-link problem (lay sent without `cycle_id`) | **Mooted** — there is no link to forget |
| Log Past Bet's inability to link | **Mooted** — same |
| BetLog `CycleChain` view keyed on stored `cycle_id` | **Re-based** onto the derived chain view |
| Daily money check "cycles touched today" rollup (`ops/settlement_review.py:209-224`) | **Re-based** onto the derived chain (read-only report; money figures unaffected) |
| Delete fence "has cycle siblings" check (`store/repositories/bets.py:1328-1341`) | **Re-based**: the fence's real protections (bet referenced by promo/ops events, settled bets) stay; the cycle-sibling test is replaced by a promo-event-reference test |
| Audit/ops events stamping a denormalised `cycle_id` scope | **Optional/inert** — kept for old rows, no longer load-bearing |

Named honestly: the delete fence and the money-check rollup are the two
consumers that need careful re-basing rather than deletion. Both are
read/report/guard paths, not money-write paths.

## 8. The two guards that STAY

1. **Unpaired-lay flag.** A LAY with no BACK on the same market/selection
   (or vice versa mid-conversion) is worth a visible flag — that is the
   real thing the "orphaned cycle" symptom was pointing at. Derived on
   read, surfaced on the race activity board and BetLog.
2. **Lost-qualifier watchdog** (`GET /v1/promos/credit-gaps`) — every lost
   safety-net qualifier with no credit event. Stays exactly as built,
   **plus a dismiss affordance** (it over-lists by design because it can't
   know finishing positions; today an item leaves the list only by being
   credited — `credit_gap.py:64-131` has no acknowledge mechanism).
   Dismissal is display-layer only and must never suppress the credit-in
   door itself.

## 9. Why free-form logging is safe (the operator framing)

The operator wants to log free-bet backs against any account /
account-at-book at will, without the tool demanding a ceremony that keeps
a grouping intact. That is safe because the real money guards don't care
about grouping:

- **Inventory existence** — you cannot deploy a free bet that was never
  credited;
- **Single-spend** — the deploy event supersedes the credit, so the same
  $50 can never be spent twice;
- **Derived balances** — cash and free-bet balances compute from events on
  read (DR-019), so no logging order or grouping mistake can corrupt them.

A mis-grouped chain view is a display inconvenience, corrected by better
derivation. A mis-spent free bet is impossible by construction. The
regulation being removed was defending the first thing while pretending to
defend the second.

## 10. What this note does NOT do, and what happens next

- **No build is commissioned here.** This is direction, not a spec. If the
  operator signs it off, the removal/re-base work becomes its own Code
  brief (it is deliberately NOT folded into `race_page_rework_brief.md` —
  that brief is fenced away from cycle machinery so the two can land
  independently).
- **Sequencing note:** the race-page rework does not depend on demotion.
  Its activity board and unpaired-lay flag derive from market/selection
  pairing either way. Demotion can follow whenever it suits.
- **Open question for the operator (the only one):** the BetLog chain view
  and daily money check will switch from "groups the tool stored" to
  "groups the tool derives". On day one after the switch, historical
  manually-joined cycles (S234's) should render identically — the derived
  walk reproduces them. If the operator wants a one-day side-by-side
  (stored vs derived) before the stored view retires, that is cheap to
  include in the eventual brief.

## 11. Cross-references

- `sessions/SESSION_234.md` §12(a), Findings (modal orphans, Log Past Bet
  gaps, `realised_conversion_rate` never populates).
- DR-019, DR-027, DR-028, DR-032.
- `race_page_rework_brief.md` (drafted same session — the companion
  artefact; fenced off cycle machinery).
- Parking-lot items mooted if this lands: hedge-link on manual entry;
  cycle-tag view; `realised_conversion_rate` watch item.

---

## Addendum A — S235 independent verification pass

_Added 2026-07-08 20:35 ACST, same session. An independent read-only sweep
of the same surface re-confirmed every load-bearing claim above, with one
honest refinement to §9:_

**Single-spend is enforced on read, not at the write door.**
`record_free_bet_deployment` (`fb_deployment.py:126-167`) checks the
referenced credit event exists and is of type `free_bet_credited` — it does
NOT check whether that credit is already superseded. A second deployment
against an already-spent credit would be accepted and written; the
inventory walk (`promo_derivations.py`) then simply hides the credit once.
So §9's "the same $50 can never be spent twice" holds **through the UI**
(the inventory picker only offers unspent credits) but is unguarded at the
API/script door itself.

Practical risk today: LOW — single attended operator, and a phantom second
deploy moves no money by itself (money rides on the bet, not the deploy
event). But this note's free-form-logging argument leans on single-spend,
so it should be watertight: **proposed follow-up (separate small item, NOT
in the race-page brief — `fb_deployment.py` is inside that brief's money
fence): reject a deployment whose credit already has a superseding event.**
One guard clause + tests; routes with the demotion build or as its own
micro-brief, operator's call.

---

## Addendum B — S235 walkthrough outcomes (2026-07-09 09:41 ACST)

Operator walked both drafts and **agreed the direction**. Three
resolutions recorded:

1. **§10's open question is dropped.** The operator elected a fresh data
   start once the model is right ("It's only a couple of days of data…
   start fresh when we're happy"), so no stored-vs-derived side-by-side
   day is needed and historical re-rendering carries no weight.
2. **Spend-now-file-later refinement to §9:** the "inventory existence"
   guard moves from a mid-burst gate to an end-of-session reconciliation
   check for *source-pending* free-bet spends (operator needs burst
   continuity — spend the bonus the book shows, pair it to its credit in
   the burst review after). A spend that never finds a source stays
   flagged — the guard is repositioned, not weakened. Single-spend and
   derived balances are unchanged. Build shape lives in
   `race_page_rework_brief.md` Addendum B (B3/B5).
3. **Addendum A's single-spend write-time hardening** rides with the
   demotion build (operator raised no objection; it strengthens the
   guard B5's pairing leans on).
