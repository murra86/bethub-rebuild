# Session 6 — active log

**Session opened:** 2026-04-27 11:04 ACST

## Scope (planned, in order)

1. Slice 2 — event log structure, re-presented from scratch with concrete operator-workflow walkthroughs leading.
2. Slice 3 — bet record (incl. DR-026 market-context snapshot).
3. Slice 4 — promo + free-bet linkage (B2 event-sourced FB model made concrete).
4. Slice 5 — four-state cash flow.
5. Slice 6 — hedge state (DR-025 six states).
6. Reconciliation contract write-up.
7. Build strategy decision (strangler-fig vs clean break + slice strategy, resolved together).
8. `diagrams/v3_target.svg`.

## Open questions carried in

- (D) Auto-classify losses vs operator-confirms-in-Burst-Review. Operational. Needs operator read.
- (E) Single event log table vs split per category. Software. Lock to single unless operator pushes back.
- (F) Never delete events, always supersede vs allow real deletion in immediate-error case. Software. Lock to never-delete unless operator pushes back.
- Item 7 build strategy — interlocked, resolve together.

## Framing note

Slice 2 re-presentation must lead with concrete operator workflows ("I log a bet at PointsBet, here's what happens; I edit it later, here's what changes; insurance bet loses, here's how the FB credit gets created") before any abstract event-shape tables. If operator can't follow, framing is wrong, not operator.

## Entries

### 2026-04-27 11:04 ACST — Session opened

Anchored on system clock. Created active session log per DR-021. Read `work_in_progress.md` to orient. About to read `sessions/SESSION_05.md` and `decisions.md` in full before re-presenting Slice 2.

### 2026-04-27 11:05 ACST — Orientation complete

Read `work_in_progress.md`, `sessions/SESSION_05.md` in full (incl. Slice 1 canonical lock and Slice 2 carry-forward), `decisions.md` DR-001 through DR-026 in full. Confirmed framing instruction: Slice 2 must lead with concrete operator-workflow walkthroughs before any abstract event-shape. About to re-present Slice 2 starting from workflows.

### 2026-04-27 12:40 ACST — Walkthrough framing landed; operator clarifications captured

Operator confirmed core principle ("ledger is the basis for all calculations at a point in time, no stored balance, displayed balance computed every time you look — solid"). Five corrections/clarifications absorbed:

1. **Insurance bets are not normally hedged** — operator runs them at raw EV, hoping for win, treats trigger as ~70% consolation. Hedge modal is wrong capture surface for insurance bets. They go through Log button on racing page after a bet is placed at the soft book. Hedging only happens on FB *deployments* (chasing ~70% conversion) and rare arb opportunities. Walkthrough 1 needs redoing for the actual common case.
2. **Insurance bet settlement requires operator input** — three outcomes (win / loss-no-trigger / loss-and-trigger). Tool must know per-promo trigger terms (2nd only, 2nd-3rd, 2nd-4th, didn't-win, didn't-place). Auto-settlement on insurance is gated by Betfair API ability to derive place position. This connects directly to open question (D).
3. **FBs can also arrive randomly as freebies** — manual FB credit input must persist. Not every FB credit is triggered by a bet.
4. **Walkthrough 2 stake-edit caveat** — the $1000-vs-$100 mistake was an execution-layer concern (lay liability sized off the wrong stake), not an accounting concern. Accounting approach accepted. Operator listed five common edit categories: wrong account, wrong stake/odds, manual bet entry (tool down / forgot / distracted), deletes (duplicate FBs, declined-but-logged), and event/operation grouping errors from fuzzy matching.
5. **Friend payments stay simple** — `paid person X amount Y on date Z`, no over-engineering.
6. **Restrictions** — books don't reverse promo restrictions. End-of-promos is end-of-book usefulness; operator stops using book at that point. Walkthrough 5 simplifies.

**Forward flag:** sports promos, especially SGM insurance, will need accommodation in event log / accounting / data capture. Currently 95%+ racing turnover; sports expansion is a near-term direction.

About to (a) redo Walkthrough 1 for the actual insurance flow, (b) add Walkthrough 1B for the FB deployment flow (where the hedge modal *does* belong), (c) add the trigger-term and freebie-FB notes into the FB credit walkthrough, then circle back to D / E / F.

### 2026-04-27 13:25 ACST — Second round of operator clarifications absorbed; awaiting D/E/F resolution

Operator pulled four important threads forward:

1. **Workflow goal explicitly named** — v3 efficiency gains depend on (a) auto-promo surfacing per current operating context (which AdsPower/router/sim is active), (b) cross-book odds + EV comparison from scraped data, (c) one-click profile switching mid-burst (close AdsPower, switch router/sim, open new AdsPower), (d) auto-settlement of *all* bets including insurance via Betfair API. The day starts with operator entering all soft-book promos in the tool; everything downstream is about minimising burst-execution friction. Operator wanted to confirm this is the goal — yes, this is in scope (DR-009 concerns 6, 8, 9, 10, 13a; DR-011 Promo Planner; DR-023 division of labour) but several of those concerns are operational/execution-layer and the schema's job is to *not block* them, not to design them in this slice.

2. **Betfair matching is piecemeal and messy** — single order can match in many partial fills over seconds-to-minutes, and at jump some portion may remain permanently unmatched. **Unmatched amount is as important to capture as matched amount.** Lay record needs to handle a stream of fill events against a single order. Builds on DR-016 persist-after-jump.

3. **Betfair market context wanted on every bet, not just hedged ones** — operator wants market snapshot + standardised Betfair data attached to every bet (insurance, non-hedged, FB deployments, hedged bets) for analytical depth and auto-settlement support. This is exactly what DR-026 already locks. Confirming and reinforcing.

4. **Insurance auto-settlement Betfair-place trap** — Betfair Place market behaviour varies by field size (3rd not paid in fields under a certain runner count), but books often still honour 2nd/3rd in those races. Auto-settlement logic must not rely on Betfair Place market alone for trigger position. Need book-side trigger terms cross-checked against actual finishing position from a position-aware source, not Betfair Place market settlement.

5. **Free bets lost** — books can revoke pending FBs as part of a limitation. New event type needed.

6. **Promo-shrink as health signal** — operator noted Kate's PointsBet 2nd-only insurance dropped from $50 to $10 yesterday-vs-today. This is a soft restriction signal preceding hard limitation. Promo-instance changes per book per account-at-book are observable and meaningful — flag for AccountCare data capture.

7. **manual-entry-after-fact question** — operator asked whether `bet_placed_at` is a manual entry, and whether the at-time/log-time distinction matters when log happens within a minute of placement. Need to give a straight answer.

About to: (a) answer the at-time/log-time question honestly, (b) absorb the partial-fill / unmatched-capture point into the lay-record shape, (c) confirm Betfair-on-every-bet is already covered by DR-026 with no schema change, (d) add `free_bet_revoked` as event type, (e) add `promo_changed` observation as event type, (f) move to D/E/F.

### 2026-04-27 13:35 ACST — Session closing

Operator agreed all Walkthrough corrections and structural additions land cleanly. Stopping at natural break before D/E/F. No context loss expected — corrections captured in this log and lifted to handoff prompt for Session 7.

**Closed:** 2026-04-27 13:35 ACST
**Summary:** Slice 2 re-presented from scratch with workflow-first framing per Session 5 stop signal. Operator confirmed core principle (notebook is truth, all displayed state computed on read — solid). Five workflows walked through and corrected against actual operational reality. Major refinements absorbed: insurance bets are not normally hedged (entered via Log button on racing page, not hedge modal); FB deployments are where the hedge modal belongs; Betfair fills arrive piecemeal and unmatched amounts must be captured by construction; auto-settlement of insurance bets needs a position-aware result source per code (not Betfair Place market, which has small-field trap); free bets can be revoked by books on limitation; promo-shrink is a soft-restriction signal worth its own event type. Five new structural points locked: (1) parent/child event relationships are first-class (lay orders + fills, SGM bets + legs), (2) `bet_placed_at` auto-stamped live with optional retrospective entry, (3) DR-026 already covers Betfair-on-every-bet — no schema change needed, (4) bet record will carry Betfair market_id for full-curve queries (lift to Slice 3), (5) F (never delete, always supersede) reinforced by additional analytical value of preserved trail. New event types added to catalogue: `free_bet_revoked`, `promo_terms_changed`. Slice 2 framing is solid; D/E/F deferred to Session 7.
