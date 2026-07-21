# Session 150 — accounts-setup scoping outcome (scratch)

**Written:** 2026-06-15 (S150). For S151 brief drafting.
**Stream:** Accounts-setup (new W-stream; first W16
cutover dependency).
**Purpose:** Carry S150's locked scope + grounding into
S151 so the build brief drafts without re-deriving.

---

## Locked scope (operator calls, S150)

1. **Fresh start in v3** — no v2 import. Clean build on
   v3's account model; none of v2's account/book
   vocabulary debt carried across. (Call 1.)
2. **Core earners first** — v3 starts lean with a small
   set of real earner books, expands over time. NOT the
   full 34-book footprint at setup. (Call 2.)
3. **Setup screen** — a reusable in-v3 add/edit accounts
   page, NOT a one-time seed. Tim owns account
   management inside v3 from day one (needed for cutover
   regardless). (Call 3.)

Folded in: **v3 auto-login** (reuse v2's self-refreshing
username+password Betfair login so v3 tokens stop
expiring ~12h) builds as part of this work. The **$5
real lay test** runs once a real Betfair account is
registered in v3.

---

## Earner grounding (v2 bethub.db — read-only, reference only, NOT imported)

Footprint: 49 accounts across 5 players (Tim, Kate,
Jordan, Caroleena, Sarie) at 34 books. 22 accounts
active, 27 inactive; 9 flagged promo_excluded.

Top books by real bet activity (1,931 bets total) —
name | n_bets | staked | pnl | last bet:

- Betfair    | 424 | 16,953 | +924   | 2026-06-13  (exchange / lay side — always needed)
- StarSports | 341 | 11,478 | +40    | 2026-05-03  (high-churn / account-health workhorse)
- TAB        | 202 | 10,314 | +1,611 | 2026-06-13  (current active)
- TABTouch   | 146 |  6,283 | +1,331 | 2026-05-16  (1 acct restricted)
- PointsBet  | 129 |  5,250 | +1,279 | 2026-05-16
- BossBet    | 103 |  2,690 | +781   | 2026-03-29  (now promo_excluded)
- HotBet     |  85 |  4,413 | +1,196 | 2026-04-13
- Betr       |  58 |  1,453 | +624   | 2026-05-13
- others smaller / some negative: PremiumBet -214,
  CrownBet -68, PickleBet -19, SwiftBet -440.

Use: confirm v3's book catalogue covers these; setup
screen surfaces earners first. Catalogue contents +
ordering = Claude's territory (no operator call needed).

---

## v3 known structure (from S149 live triage)

- Backend: uvicorn on :8000 (BETHUB_ env prefix,
  pydantic-settings). Frontend: ui/web on :5174 (Vite;
  auto-bumps from 5173 when v2 holds it).
- Frontend routes today: Racing / Health / Provisional.
  No accounts/settings route exists.
- `/api/v1/racing/accounts` returns 0 books / 0 accounts
  / 0 accounts-at-book. DB empty (clean start).
- NO operator-facing create endpoints; only seed script
  is seed_promos.py. CORS allow-list at ui/api/config.py
  (defaults :5173 only — widen for v2 coexistence).
- Auto-login missing: v3 reads a static session_token
  from JSON; v2 mints its own via username+password.

---

## S151 pre-flight grounding TODO (before drafting)

Probe v3 codebase for the build brief's anchors:
- DB layer / models (where account / book /
  account-at-book tables live; existing stubs).
- API router structure + where create/edit endpoints
  attach.
- Frontend structure (how a new setup screen + route
  slots into ui/web).
- DR-030 module-boundary rules (close gate on Code work).

---

## Brief shape + governing DRs

- Shape: **build brief** (new capability). Closest
  precedent = W12 / W13 build briefs (single bounded
  Code session, named anchors, hard limits, output spec,
  pre/post verification). Universal brief spine applies.
- Governing DRs: DR-022 (book / account / account-at-book
  vocabulary — directly shapes the model), DR-027/028
  (two-DB split + boundary — setup is a cutover /
  cross-database moment; re-read at drafting), DR-030
  (v3 module boundaries), DR-031 (v3 stack), DR-021
  (Adelaide timestamps).

---

## Routing

S151 = Claude Chat brief-drafting session (accounts-setup
build brief), section-by-section, call-driven surfacing.
Then Claude Code builds against the locked brief; v3
auto-login folds in; the $5 lay test runs against the
real account once registered.
