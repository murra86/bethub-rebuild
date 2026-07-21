# Promo-on-bet + free-bet credit-in — read-only review brief

**Status:** locked draft (Session 178). Read-only Claude Code codebase
review. Builds nothing.
**Output:** `interface_triage/promo_attach_credit_in_review_report.md`
**Repo (read-only):** `/Users/tim/Desktop/Projects/bethub-v3`
**v2 (read-only, requirements only):** `/Users/tim/Desktop/Projects/bethub-v2`
**Tests:** v3 baseline is `uv run pytest` (not bare python3) — reference
only; this review runs none.

---

## §1 — What this review is, and is not

- A read-only map of the v3 codebase — plus a v2 read for *requirements
  only* — commissioned to size what exists vs what's needed to: (a)
  **persist the selected promo onto each bet at log time**, and (b)
  **create the free-bet credit when an insurance qualifier places**.
  Single bounded Code session.
- **Builds nothing. Edits nothing.** No migration, no DB writes, no git
  state-changing operations. The only file written is the review report.
- **Surprises become findings**, not detours. No fixes, no remediation,
  no next brief — those route to the next operator-Claude triage session.
- **Keep an open mind (operator-requested).** Areas 1–6 are the locked
  scope, but if Code spots anything else that should need attention —
  adjacent risk, debt, coupling, a cleaner seam, a landmine, a scope
  question — flag it under Area 7 (open findings). The locked areas are
  the floor, not the ceiling.
- **v2 is read ONLY to lift requirements** — the promo term-set and the
  "placed in the insured spots → refund this" rule that worked in
  production. **Not** to copy v2's engineering: v3 is native by design,
  and the bet schema + promo vocabulary were named as v2's worst
  structural debt (the reason for the rebuild). v2 answers *what*; v3
  decides *how*.

## §2 — Why this work exists

v3's free-bet pool can be drawn down but nothing in the running app fills
it up (S168 pool review): no production path creates a free-bet credit.
So v3 cannot run a full Strategy 1 (Safety Net) cycle — an insurance
qualifier settles and the tool has no way to know a free bet was earned.

The S168 design (`free_bet_credit_in_design.md`) assumed the qualifier is
"logged with its promo attached — mostly already built." Grounding at
S178 showed that isn't true: the race-screen promo buttons are **EV
presets** (display + pre-fill only); a logged bet persists a
`strategy_tag` (4-value) + a single `promo_ev_at_log` number, but **not
which specific promo** (insured spots, FB-vs-cash, cap). The DR-032
`bets.promo_instance_id` link is documented but unbuilt.

Operator's call (S178): build the **full** promo-on-bet attachment (the
v2-proven pattern), **single-level** — one promo-type reference table,
each row a serial with its terms; the bet stores the serial; settlement
reads it back. (No separate promo *instance*: book is already on the bet,
and promos mature at the event — there's no run-window to model.) This
review sizes that build before any design is locked — the BetLog de-risk
pattern (S170): review read-only, size, then draft the build off grounded
findings.

## §3 — Pre-reads

Required, in order:

1. `interface_triage/free_bet_credit_in_design.md` — the locked S168
   credit-in design (Piece 0 credit-in + Piece A cycle attribution).
2. `interface_triage/free_bet_pool_review_report.md` — the S168 read-only
   pool map (credit / deploy / settlement anchors).
3. `interface_triage/manual_entry_build_report.md` — the Brief 2 build
   (the Log Past Bet settle-at-entry path).
4. `interface_triage/betlog_build_report.md` (§5.8) — the inert "Placed?"
   scaffold seam.

Reference-only (on demand, not required): `data_sources.md` (the
placings / finish-position picture, DR-033); `audit_landscape.md` (the
per-domain event-log spine).

## §4 — System access

- **v3 read-only**, Mac filesystem direct at `/Users/tim/Desktop/Projects/bethub-v3`.
  Source reads + targeted greps only.
- **v2 read-only**, `/Users/tim/Desktop/Projects/bethub-v2` — requirements
  lift only (promo term-set + refund rule). Do not port code.
- **No database access** — neither v3's operational store nor capture.db
  is read or written. The placings dependency is assessed from source +
  `data_sources.md`, not by querying.
- **No git state-changing operations** — read-only `git status` / `grep`
  fine; no add/commit/stash/restore/checkout/reset.
- Adelaide local timestamps (ACST/ACDT) per DR-021 for every time
  reference in the report.

## §5 — Review areas

Areas 1–6 are locked scope. Each names where to look and what to answer;
file/line anchors are starting points (verify against the live tree —
captured S168/S171/S176, the tree is in-flight).

### Area 1 — Promo reference table (the "single page of serials")

**Look at:** `domain/promos/__init__.py` (`Promo`, `PromoTemplate`,
`PromoTemplateKind` = insurance / bonus_winnings / price_boost /
ew_cashback / other; `create_promo` / `get_promo` / `list_promos`);
`workflows/promos/v1/promo_store_adapter.py`; `scripts/seed_promos.py`;
the presets `ui/web/src/promos/presets.ts` (`PROMO_PRESETS`, 10) +
`ui/web/src/components/PromoBar.tsx`. **v2:** the promo-terms source the
presets were ported from (`frontend/src/utils/promoPresets.js` per the
v3 presets header) + wherever v2 stored the refund terms it settled on.

**Answer:** What of a single-level promo-type table is already built vs
only documented? Can the ten preset buttons seed it with **structured**
terms a settlement read-back needs — insured spots (2nd / 2+3),
free-bet-vs-cash, cap amount? What's the gap between the presets' current
shape (EV config) and a persisted, settlement-readable term-set? Book +
run-window are deliberately **out** of scope.

### Area 2 — Writing the promo onto the bet at log

**Look at:** race screen — `ui/api/routers/racing.py` `log_bet`
(~:853–911; `cycle_id` :892; `strategy_tag` + `promo_ev_at_log`
persisted), `ui/web/src/components/LogBetPanel.tsx` +
`ui/web/src/api/racing.ts` (what the panel sends today). Log Past Bet —
`ui/api/routers/bets.py` `create_manual_bet_endpoint` (:742) +
`ManualBetCreateRequest` (:218), `workflows/bet_entry/v1/record_builder.py`
`build_manual_bet_record` (:498), `ui/web/src/routes/LogPastBet.tsx`.
Schema — `store/schema/bets.py` (the `_add_column_if_missing` additive
pattern, e.g. `settlement_state` :120), `domain/bets/__init__.py`.

**Answer:** What does it take to carry the selected promo's serial from
the picker through to a persisted field on the bet, on **both** entry
paths? Is the bet-schema change a clean additive column (the existing
pattern) or heavier? This is the first touch of the bet's own schema in a
while — size it honestly, name any risk.

### Area 3 — Reading it back at settlement (the delicate seam)

**Look at:** `workflows/bet_entry/v1/settlement.py` —
`_resolve_settlement_for_bet` (:319–486; won :449 / lost :461 / voided
:406,436), `apply_manual_operator_resolution` (:1128);
`ui/api/routers/provisional.py` (manual-resolve surface); the placings
picture in `data_sources.md` + the finish-position gap (DR-033).

**Answer:** Where would the tool check "this Safety Net bet under {promo}
finished in the insured spots → a refund is earned"? Crucially: how is
that done **strictly off** the live bet-settlement write path — the
safety seam: credit-in must never wire into `settlement.py` internals
(reads settled qualifiers, doesn't touch the settlement transition). And
how does it depend on the pending placings / finish-position backfill —
is the read-back inert until that data flows, a hard blocker or a
graceful "earned credits appear once placings land"? Name the dependency
precisely.

### Area 4 — Credit-in write + cycle link

**Look at:** `workflows/promos/v1/fb_deployment.py` (:82–169;
`append_event` :166; whole-credit consume; operator-supplied order, not
FIFO); `domain/promos/__init__.py` `FreeBetCreditedPayload` (:293–346;
`credit_source` triggered/freebie; **both** `triggering_bet_id` +
`triggering_promo_instance_id` required for `triggered`; `CreditStatus`);
`ui/api/routers/racing.py` `log_bet` cycle derivation (:892 fresh uuid;
deploy `correlation_id` :935).

**Answer:** Where does the `free_bet_credited` write land (the
promo-event write zone, **not** settlement)? Given the single-level model
(no separate promo *instance*), what satisfies the payload's
`triggering_promo_instance_id` requirement — relax the validator to
bet-linked-only, or have the promo serial double as the reference? And
the cycle link (Piece A): what's needed for a deployed free bet to
inherit its qualifier's cycle (oldest-credited FIFO → `triggering_bet_id`
→ qualifier `cycle_id`)?

### Area 5 — The two "placed?" confirm surfaces

**Look at:** `ui/web/src/routes/BetLog.tsx` (the inert
`placed-confirm-scaffold`, "coming soon — brief 3");
`ui/web/src/routes/LogPastBet.tsx` (the won/lost/void settle-at-entry
toggle) + the create-endpoint settle path.

**Answer:** What does it take to make both surfaces ask the one
settlement-time question — "placed in the insured spots?" — and fire the
**single** credit-in write (not two)? Gate: show it only for a
non-winning insurance qualifier (`strategy_tag` = safety_net +
settled-lost + a promo attached).

### Area 6 — Overall buildable read

Effort per area (S/M/L + confidence). Does the build split cleanly into
two (promo-attach foundation, then credit-in + cycle link), or is it one?
Single-session feasibility per piece. Named risks front-and-centre: the
bet-schema touch, the settlement read-back seam, the placings-data
dependency, the validator change.

### Area 7 — Open findings (operator-requested latitude)

Anything else Code spots that should need attention and isn't in Areas
1–6 — adjacent debt, coupling, a cleaner approach, a landmine, a scope
question. Flag it; don't chase it into a fix.

## §6 — Sequencing within session

Suggested order: Area 1 (table) → 2 (write-on) → 4 (credit-in) → 3
(read-back) → 5 (confirm surfaces) → 6 (overall) → 7 (open). A cleaner
order is Code's to take — say so in the report. If the review needs more
than one session, that's a finding: partial-but-coherent beats
complete-but-lost-coherence — stop and report where it got to.

## §7 — What a good report looks like

Per area: a built-vs-needed verdict with file/line evidence, an effort
size + confidence, and named dependencies/risks. Negative findings cited
(a grep that proves "not built"). No build, no recommendation-as-decision
— size and map; the operator-Claude triage decides scope and sequence.

## §8 — Output spec

- Single file: `interface_triage/promo_attach_credit_in_review_report.md`.
- Sections mirror the seven areas, plus a §0 baseline (repo state, what
  was read) and a closing self-assessment (coverage, confidence, what
  wasn't traced).
- Length: ~250–450 lines. Over is fine if an area earns it (flag in
  self-assessment); don't pad.
- Does **not** contain: any code change, a migration, a build plan locked
  as decisions, a "next brief," or v2 code ported across. Findings and
  sizing only.

## §9 — Hard limits (non-negotiable)

- Read-only. No file in either repo created, edited, moved, or deleted
  except the one report. No DB read or write. No git state-changing ops.
- No build, no migration, no schema change, no test additions.
- v2 read for requirements only — no code ported.
- No remediation, no fixes, no next-brief authoring.
- Single bounded session; if it won't fit, report partial-but-coherent
  and stop.
- The settlement / placement seam is a **read** target (Area 3), never an
  edit target — do not touch it in any way.

## §10 — What happens after Code's session

The next operator-Claude session reads the report, triages the seven
areas, and **scopes the build** — confirming the single-level promo-table
model, deciding one-build-vs-two (likely promo-attach foundation, then
credit-in + cycle link), and sequencing against the placings-data fix.
Code does not write that build brief; this review feeds it.

## §11 — Cross-references

- **Design:** `free_bet_credit_in_design.md` (S168, Piece 0 + A).
- **Prior reports:** `free_bet_pool_review_report.md` (S168),
  `manual_entry_build_report.md` (Brief 2), `betlog_build_report.md`
  (§5.8 scaffold).
- **DRs:** DR-032 (Betfair canonical / the `promo_instance_id`-on-bet
  link), DR-019 (derived P&L on read), DR-030 (module layering),
  DR-027/028 (cross-DB boundary — the placings/capture.db read), DR-021
  (Adelaide timestamps), DR-033 (data-source roles — placings from the
  Racing API analytical line).
- **Dependency:** the pending Racing-API placings backfill + nightly
  results-sync fix (own brief) — Area 3's read-back leans on it.
- **Excluded (parking-lot):** Piece B (settlement-cascade auto-crediting,
  provisional / negative pool, deploy-before-credit timing) — post-cutover;
  partial free-bet draw-down (whole-only for cutover).
