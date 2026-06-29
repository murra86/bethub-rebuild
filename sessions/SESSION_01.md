# Session 1 — Strategic rebuild discussion

**Date:** 2026-04-25 **Type:** Claude Chat, strategic only — no code, no DB writes

## What we discussed

Tim raised that BetHub v2 has reached a friction wall. Sessions take 20+ min to close, small fixes touch many surfaces, and numbers do not reconcile. He is starting to plan the next set of features (one-button profile switching, Betfair liquidity analytics, soft book scanning) and concluded these cannot be cleanly added on top of v2.

I confirmed the diagnosis. v2 grew organically over 7 months without an upfront architecture, the governance overhead has overtaken the build overhead, and the context loading cost per session is now the binding constraint on productivity.

We mapped v2's current state honestly across three diagrams:

1. **Pass 1 — eight chunks of work v2 is doing today.** Bet logging, hedging, promo engine, account ledger, AccountCare, monitoring, reporting, live odds.
2. **Pass 1.5 — added six gap boxes.** Profile switching, promo allocation, flexible Betfair hedging, smart Betfair view, soft book scanning, operations log. Plus operator tax (red — time spent fixing the tool's data) as the most damning finding.
3. **Pass 2 — light v2 autopsy.** Traced what happens when ⚡ is clicked to deploy a free bet. Nine subsystems involved, no atomic transaction across Betfair API + DB, six different surfaces all implementing the same flow.

Tim added several important refinements:

- 20 min/account/day browsing is unsustainable but full automation is dangerous. Reframed as right-sizing hygiene budget per account based on assigned strategy.
- TeamViewer-to-friends-houses raised as alternative networking model. Parked for v4.
- Promo allocation is more nuanced than reactive vs proactive — Tim wants aggressive harvest of high-EV books with throttle/longevity tradeoff (e.g. $200/week for a month preferred over $10/week for a lifetime).
- Betfair UI quality means tool should not try to replicate Betfair, only show what Betfair cannot.
- Hedge flexibility gap is small — limit orders at custom price plus a fair-price indicator (geometric midpoint + liquidity-weighted).

## Decisions made

- DR-001: Rebuild from the ground up
- DR-002: Three-layer architecture (operational, execution, accounting) with strict boundaries
- DR-003: Six-file governance, no anomaly/patch/conventions logs
- DR-004: Session open reads only work_in_progress.md
- DR-005: Diagrams as separate picture files
- DR-006: Operations log first-class from day one

## What is next

Session 2 — target architecture for v3. Triage the 15 functional concerns, design the three layers in detail, decide build strategy, define reconciliation contract.

## Notes on operator preferences (relevant for all future sessions)

- Plain English, no code-heavy explanations
- No stream-of-consciousness reversals mid-response
- Visual-first when explaining structure
- Acknowledge missing context and ask rather than guessing
- Frame technical decisions in betting/operational terms
