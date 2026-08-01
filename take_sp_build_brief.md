# Build brief v2: "Take SP" at-jump option for lays

**Status:** **SIGNED OFF (operator, S246 — 20 Jul 2026).** 3-lens adversarial review
round 1 APPLIED; D3′ resolved FB-only (operator, 2026-07-14). D2 (phase-2 flip-sweep /
cancel button) stays open — only relevant after Stage 2; default = park.
**Slotting (S246):** Stage 0 capture = next race day (one tiny real Take-SP lay through
the existing API, operator present, ~$12 bounded liability); Stage 1 build = after the
Stage-0 fixtures land; Stage 2 default flip per its own gate. Runs AFTER the race-day
live-proof of the S245/S246 stack — the stack stays frozen for its first real outing.
**Origin:** S240 operator request + backtest `fb_lay_take_sp_analysis.md`.
**Review verdicts:** design-attack / governance / ops pre-mortem — all approve-with-amendments.
**Slot:** after the VPS hardening build closes; NOT part of the Wed/Thu UI pass.

## Why (restated honestly per review)

Unmatched FB-hedge lay remainders currently lapse → free bets settle $0 on losers (Capital Asset
$4.60 vs $38.95; Catch The Red Eye $4.43 vs $31.18). Converting remainders to BSP keeps the win-side
lock identical (liability preserved) and the FB lose-side positive — **always ≥ the lapse outcome**.
Honest framing (review D-5): conversion fires mostly on *drifters*, so the converted fill will
usually land ABOVE the limit price — recovery is typically smaller than the planned lock, but never
worse than lapse (FB). The two backtest recoveries (BSP below limit) are the favourable tail, not
the expectation. The unconditional stat (BSP ≤ closing lay 98–100%) bounds the SP pool's fairness,
not the conditional outcome.

## Scope stages (review G-2: default must not ship before proof)

- **Stage 0 — capture-first (review G-4):** place one tiny real Take-SP lay via the existing API
  (`racing.py:579` already accepts MOC; no UI needed) sized so remainder liability at the limit is
  comfortably ≥ $10 (e.g. ~$6 @ 3.0 = $12; bounded worst case). Capture current-orders reads through
  the suspend → in-play → settled sequence AND the cleared read; answer empirically: does the bet id
  survive conversion; is the SP-pending bet visible in listCurrentOrders during the window; exact
  resize shape. Fixtures are written FROM these captures (S223 lesson: never simulate shapes).
- **Stage 1 — the build (items below), defaults UNCHANGED:** Take SP is selectable, not default.
- **Stage 2 — default flip:** one-line default change + component-test red/green + its own dist
  swap, ONLY after the item-8 live-proof write-up is signed off. Per-race-code: default-ON applies
  to a code only once conversion is live-proven on that code (review D-1).

## Fence

- **IN:** HedgeModal dropdown/default/guards; `Racing.tsx` toast + `onPlaced` meta type + in-modal
  partial-fill banner wording (review D-2/O-3 — the v1 claim "gap is ONLY HedgeModal" was FALSE);
  `bsp_market` + `turn_in_play_enabled` serialization: contract §14.4 backward-compatible additions
  to `MarketCatalogue` from the MARKET_DESCRIPTION projection + contract v1.7 changelog line
  (review G-3/D-6 — the v1 claim "no contract change" was FALSE) + route response + `types.ts`;
  write-only `persistence_type` column on the bet row at placement + display-only "SP" tags
  (review O-4/G-7); reconciliation-decision `detail` carries the read's persistence/order type
  (free-form dict, no logic change); settlement fixtures; live-proof.
- **OUT (hard):** `updateOrders`/flip-sweep (phase 2, D2); in-tool bet-cancel route/button (named
  phase-2 candidate, review O-2); any change to stake/price computation, the liability guard,
  resolver/reconciliation LOGIC, ConfirmCard/back-log, promo/credit; the orchestrator's hard-coded
  PERSIST (`betfair_adapter.py:210`) is intentionally untouched — do not parameterize (review G-10).
- STOP rule, pre-authorized exit (review G-4): a fixture exposing a reconciliation/settlement code
  gap ends the session with a report + separate fenced fix brief (the B3 pattern) — planned exit,
  not a stall.

## Items

1. **Third dropdown option "Take SP"** → `persistence_type: "MARKET_ON_CLOSE"`. Offered only when
   `bsp_market && turn_in_play_enabled` (review D-1: BSP alone is wrong — greyhounds are BSP
   markets with no in-play transition; MOC there is an unverified no-op. Greyhounds KEEP their
   LAPSE default until Stage-2 per-code proof). Sub-lines: FB mode — "unmatched at the jump fills
   at Betfair SP — liability never exceeds this bet's"; cash mode (review D-4) — "win-side
   unchanged; lose-side floats with SP — can land below plan, never below a lapsed remainder".
2. **Default rule (Stage 2 only):** on gated markets, default "Take SP" in FREE-BET mode only
   (D1/D3′ resolved 2026-07-14); cash keeps the race-code default, Take SP selectable.
   Override stickiness via existing `userEditedPersistence`. Late-catalogue re-seed must not flip a
   dropdown the operator has seen: when Take SP is selected (or becomes default), the placement
   surface reflects it at the moment of commitment — button/summary line says "…remainder takes SP"
   (review D-8).
3. **Guard wiring:** absent/`null` `bsp_market` ⇒ option HIDDEN (never default a money-affecting
   option on missing data — review O-9); tests run against captured catalogue payloads for
   true/false/absent.
4. **Floor messaging (reworded — review D-7/O-8):** placement note explains the *remainder*
   semantics ("if less than ~$10 of lay liability is left unmatched at the jump, that sliver
   cancels instead of taking SP"). Post-placement: the partial-fill banner on a Take-SP lay
   computes remainder liability from `size_remaining` × (price−1); ≥$10 → reassurance ("$X
   unmatched — takes SP at the jump, liability capped at $Y"); <$10 → "remainder below the SP
   floor — will cancel at the jump". The banner must never present an expected Take-SP remainder
   as an alarm (review D-2's double-hedge scenario: −$135 on a "locked" cycle).
5. **Truthful messaging end-to-end:** widen `HedgeModalProps.onPlaced` meta persistence union;
   fix the `Racing.tsx:508–510` ternary (currently calls MOC "lapses at the jump"); toast test
   asserts the MOC string **through the Racing route wiring** (vitest doesn't typecheck — the
   string, not the type, is the test).

## Settlement verification (fixtures FROM Stage-0 captures)

6. **Reconciliation truth fixtures — mandatory set:**
   (a) resize-UP: `sizeMatched > sizeRequested` (BSP below limit — BOTH backtest cases and the
   Stage-0 bet will have this shape; `record_builder.py:285–289` raises on it and
   `unmatched = requested − matched` goes negative — assert no path recomputes/rebuilds through the
   builder invariant; review D-3);
   (b) resize-DOWN (BSP above limit — the common production case);
   (c) **CRITICAL (review G-1): transient conversion-window read** — partially-matched Take-SP lay
   ABSENT from current orders, market SUSPENDED/in-play, `settled_time=None` → expected outcome is
   carry-forward, NOT the `absent_resolved_pre_settlement_full` terminal at
   `reconciliation.py:396–408` (which would FINAL_FULL the stale pre-jump fragment with no later
   correction; the B3 HIGH-1 fix guarded only the zero-matched branch). If the fixture proves the
   terminal fires → STOP per the pre-authorized exit;
   (d) sub-$10 remainder cancelled at the off (from a manufactured Stage-0/item-8 capture) —
   asserts the S228 conclusiveness guard handles the partial-cancel cleared shape.
7. **Removed-runner / abandoned-market fixtures — oracle from designed semantics (review G-5):**
   removed runner ⇒ `absent_resolved_void_or_removed` → FAILED/$0 (NOT winner-less hold — v1's
   oracle was wrong); abandoned/pulled market ⇒ cancelled remainder + voided matched portion must
   carry-forward → park valve → manual queue, never wrong-settle, and the brief documents that a
   Take-SP bet on an abandoned race resolves through the manual queue hours later (review O-7).
8. **Live-proof (operator-supervised), expanded (reviews G-6/O-6):** at least — one thoroughbred
   conversion with BSP materially ≠ limit; one manufactured sub-$10 remainder cancel; one greyhound
   attempt (does MOC fire at all on a never-in-play market? Stage-2 gate for code G); one small
   CASH cycle ONLY if the operator later widens D3′ (dropped per FB-only resolution). Evidence
   list per bet: audit entry with
   `persistence_type=MARKET_ON_CLOSE`, conversion observed in captured reads, bet-id continuity
   answer, reconciled money matches BSP arithmetic, settlement_review line shows the SP tag.
   Sizing rule: limit below best-back so it cannot pre-match; remainder liability ≥ $10 at the
   limit; bounded liability the operator names in advance.

## Operating rules (ship WITH stage 1, diary + standing instructions)

- **No walk-away on Take-SP** (review O-2): once placed, the tool has no cancel — the Betfair
  website is the manual escape. Rule: *never place a Take-SP lay you would not accept at BSP.*
- First ~2 weeks / first 10 conversions: every SP-converted fill gets a settlement-review eyeball
  (the SP tag from the fence makes them enumerable; review O-4).
- Greyhound lays keep today's habit (LAPSE) until the code-G proof.

## Acceptance

- Suites green + `npm run build`; dist swaps app-idle only; Stage 2 has its own red/green + swap.
- Component tests: option gating (bsp/turn-in-play/absent), default + override stickiness (Stage 2),
  floor messages (remainder semantics, both bands), MOC toast via Racing route, banner reassurance
  variant, placement-surface readback.
- Item 6–7 fixtures green from captured shapes; audit entry asserted (review G-10).
- Live-proof write-up signed before Stage 2; per-code gate honoured.
- Contract v1.7 changelog: `bsp_market`/`turn_in_play_enabled` additions + overdue §15.4
  `listClearedOrders` carve-out correction (stale since S228; review G-9).

## Decisions

- D1. **RESOLVED 2026-07-14: default ON** (at Stage 2, per-code gated).
- D2. Phase 2 (updateOrders flip sweep; in-tool cancel button now named alongside it) — park or
  commission after Stage 2?
- **D3′ RESOLVED 2026-07-14 (operator, accepting the panel): FB-mode-only default.** Take SP
  defaults ON only when the modal is in `free_bet` mode (on gated markets, Stage 2); cash lays
  keep the existing race-code default with Take SP selectable per bet. The cash sub-line (item 1)
  and the no-walk-away rule still apply whenever cash Take-SP is manually selected. The item-8
  cash live-proof cycle is DROPPED from the mandatory set (cash is now opt-in, covered by the
  sub-line wording + operating rule).

## Effort (revised)

Stage 0 capture ≈ ½ session (one racing day, tiny bounded bet). Stage 1 build + fixtures ≈ 1–1½
sessions (fixture set is the bulk). Item 8 proof = 1 supervised racing-day slot. Stage 2 flip ≈
trivial + its own swap. Total ≈ 2–2½ sessions + two racing-day touchpoints.
