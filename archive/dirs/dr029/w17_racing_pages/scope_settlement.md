# W17 (racing market pages) — scope settlement

**Locked:** Session 145, 2026-06-10 15:58 ACST close.
**Status:** operator-confirmed scope. Session 146 drafts the
W17 brief from this file. This file is the canonical record
of the S145 scope decisions; the brief expands it, it does
not re-open it.

---

## 1. Design posture

**W17 is a first functional cut, not a final design.** The
brief scopes firmly what the pages *surface* (data, EV maths,
new indicators, bet tools) and deliberately leaves layout as
refine-in-use. Operator context: just back from a month
abroad, hasn't bet in ~a month, will refine from real burst
use. Layout refinements come as small fast follow-up briefs
post-W17, driven by daily use. The brief must state this
posture explicitly so Code builds component structure that
keeps layout changes cheap (clean data/presentation
separation).

## 2. Density as a stated design principle

Operator's primary v2 gripe: screen-width efficiency on the
race screen. Many columns, more features proposed (price
indicators), a lot to ingest mid-burst. The brief names
density as a design principle: compact, burst-readable,
every column earning its width. Applies to all pages,
strongest on the race screen.

Operator forward-flag (not W17 scope): columns may
eventually be defined by which promo is active. Refine-in-use
bucket; note in brief's future-work section.

## 3. Calculator — CUT from W17

Operator has never really used v2's calculator popout (used
separate Excel instead). The calculator does not port. The ▶
send-to-calculator button goes from the odds table. The ⚡
quick-lay (HedgeModal) and LOG bet (LogBetFromRacePage) tools
carry — they are the daily-use load. A calculator rethink
shaped around the operator's actual Excel workflow is a
separate future item, post-W17, when the operator is ready —
NOT part of this brief.

## 4. Betfair price-movement indicator — simple version in W17

Mechanism: keep a short rolling in-session memory of recent
prices from the existing ~1s live polling (held in the app
while a race is open; nothing persisted to the database).
Surface per runner:

- Direction + size: ↑↓ arrow with % change over the window
  (drifters light up — Strategy 2 relevance).
- Optionally a small sparkline of the last few minutes.
- Same rolling memory may flag sudden money piling onto a
  runner (matched-amount spike) — cheap to add, Claude's
  call at drafting time.

Window: default ~5 minutes (burst-relevant horizon),
implemented as a tunable setting, not hard-coded. Claude owns
the detail.

**Sophisticated version deferred to the analytical arc (P2)**
— operator-confirmed. capture.db's full price history enables
e.g. drift-profile-vs-typical-pre-jump-pattern work there.
Noted against P2 in the build picture.

## 5. v3 data on the race page — lean first cut

Operator-confirmed proposal:

1. **Free-bet inventory in the bet-logging panel** — when
   logging a bet, show usable free bets at the selected
   bookmaker (W13 derivation). Actionable at log time.
2. **Balance at the selected bookmaker, same spot** — W12
   read-derivation visible at log time, not a standing
   column.
3. **Nothing new on the odds table itself** — table stays
   price/EV territory.

Operator: "Let's do that for now I think. I need to use it a
bit before I can know." Lean cut confirmed; refinements from
use.

**Per-bookmaker cross-account spot-check view** (one book
across Tim/Kate/Sarie at a glance): parked as its own small
later item — NOT folded into W17. Remove from the
"carries alongside W17" framing in current_state; it is now
a standalone parking-lot item.

## 6. What ports from v2 (baseline, redesign-where-needed)

Grounding reads done S145 (read-only): v2
`frontend/src/components/RacingPage.jsx` (632), 
`OddsComparisonTable.jsx` (692), `TodaysRacing.jsx`,
`useRacingData.js`, `usePromoConfig.js`, `utils/commission.js`,
`src/api/racing.py` (502). v3 scaffold: FastAPI `ui/api/`
(health + provisional/burst-review routers only) + Vite/React
TS `ui/web/` (Health + Provisional routes).

Ports (subject to redesign-where-new-features-land):

- Race sidebar: Betfair-catalogue race list, type/venue
  filters, time-to-jump colouring, liquidity, completed-race
  LOG affordance.
- Odds table: BF back/lay/matched, raw EV% + promo EV%
  (midpoint field probabilities / Harville-based engine),
  manual odds entry with soft-ladder stepper,
  confidence-tiered EV display, overround row, small-field
  warning, results mode with placings.
- Promo machinery: preset selector, config bar, per-runner
  overrides (persisted per-market), guidance banner.
- Bet tools: ⚡ quick-lay modal + LOG bet inline panel
  (extended per §5). Calculator cut per §3.
- Live polling indicator / data-age surfaces.

v2 receives no modifications (standing rule). v3 page talks
to v3's FastAPI surface; required new API routes (racing
catalogue/live-odds proxy, etc.) are W17 brief scope —
drafting decides shape against DR-030 module boundaries and
the existing clients/workflows.

## 7. Adjacent routing locked at S145

- **Alembic (DR-031 deferral): adopt now, but NOT inside
  W17.** Racing pages are read-heavy; W17 doesn't need it.
  Adoption bundles into the maintenance micro-brief.
- **Maintenance micro-brief: confirmed worth doing.** The
  five small items (FB-inventory test clock-freeze, two
  stale _COMMISSION_TABLE docstrings, bets row-factory
  asymmetry, .importlinter doc note) + betfair_adapter mypy
  cleanup + Alembic adoption. One light Code session,
  independent of W17, runs whenever convenient. Drafting
  this micro-brief is a separate (small) deliverable —
  S146 if budget allows after W17 drafting progress, else
  S147.

## 8. Session 146 shape

Primary: W17 brief drafting proper. Open with the remaining
grounding reads not yet done (LogBetFromRacePage.jsx,
HedgeModal.jsx, evEngine.js, promoPresets.js,
softOddsLadder.js, v3 contracts/ + workflows read-surfaces
for balances/promos), then section-by-section drafting per
the brief-drafting skill, call-driven surfacing. W17 brief
may span more than one session — it is the largest remaining
pre-cutover workstream.
