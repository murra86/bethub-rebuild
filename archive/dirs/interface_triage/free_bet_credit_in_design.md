# Free-bet credit-in design — Piece 0 + A (locked)

**Status:** locked, Session 168 (2026-06-19 ACST).
**Purpose:** the agreed approach the Piece 0 + A build
brief is drafted against. Not a build brief itself.
**Builds on:** S167 `cycle_capture_records_look.md`,
S168 `free_bet_pool_review_report.md`, and the locked
Session 70 free-bet pool model.

---

## The problem (from the S168 review)

v3's free-bet pool can be drawn **down** but nothing in
the running app fills it **up** — no production path
creates a free-bet credit (review §2.2). So v3 cannot
run a full Strategy 1 cycle today: an insurance qualifier
settles and the tool has no way to know a free bet was
earned. Building the credit-in side is the real
pre-cutover work; "wire a link" was hiding it.

## Scope split (locked)

- **Piece 0** — credit-in: create the free-bet credit
  when an insurance qualifier is confirmed placed.
- **Piece A** — cycle attribution: the deployed free bet
  inherits its qualifier's cycle.
- **Piece B** — timing tolerance (deploy-before-credit,
  provisional negative pool, settlement-cascade
  auto-crediting): **its own slice, post-cutover.** Not
  in this design.

Order: Piece 0 → Piece A, both pre-cutover. Piece 0 and
A effectively fuse (see flow).

---

## The locked flow (end to end)

1. **Log qualifier** on the race screen with its promo
   attached — as today. The promo carries the insured
   positions (e.g. 2nd, 2nd–3rd). Mostly already built.
2. **Settle the qualifier** — win/lose, auto or manual,
   as today. The settlement engine is NOT modified.
3. **Trigger confirmation.** For a *non-winning*
   insurance qualifier, the operator answers one
   question at the settle step: *"placed in the insured
   spots?"* yes/no. This is the only operator input, and
   it is the v2 flow that already worked (v2 used a
   `promo_triggered` flag; insurance was its dominant
   free-bet source — 226 deployed).
   - Rationale: the settled result is only win/lose; the
     win feed cannot tell 2nd from last. The operator
     supplies the placing because only they know it.
     Auto-detecting placing from a Betfair place feed is
     Piece B / later.
4. **Credit created.** On yes, the tool writes a
   free-bet credit (`free_bet_credited`, source
   `triggered`) into that account-at-book's pool,
   stamped with the qualifier as `triggering_bet_id`.
   This fills the write-path gap the review found.
5. **Amount** defaults to the qualifier's stake (the
   standard insurance refund, capped); operator adjusts
   on the rare promo that pays differently. No
   structured-terms modelling pre-cutover — v3 stores
   promo terms free-form, and stake-back covers the
   common case.
6. **Deploy** (Piece A). When the operator places a
   free-bet-funded bet, the deployed bet inherits the
   consumed credit's qualifier cycle — because the
   credit already carries `triggering_bet_id`. The cycle
   link is derived server-side, no fresh cycle minted,
   no extra UI pick. Piece 0's source-stamp hands Piece A
   its link for free.

---

## The safety seam (load-bearing)

Credit creation is fired by the operator's trigger
confirmation and runs as a step that **reads** settled
qualifiers — it does **not** wire credit-writes into the
settlement engine's internals (`settlement.py`). That
keeps Piece 0 out of the bet-safety-sensitive settlement
write path. Risk band: reaches the promo-event write
(same zone as the existing deploy write), not the
settlement transition. This is what makes Piece 0
pre-cutover-safe; the settlement-cascade version is Piece
B.

## Drawdown rules (locked)

- **Consumption order: FIFO — oldest-earned first**, by
  credit age (always known; no expiry data needed).
  Expiry is not tracked and won't be pre-cutover.
  Operator deploys free bets promptly, so FIFO is the
  natural fit and matches the Session 70 lock.
- **Whole-credit consumption only** for cutover. Matches
  denomination-matched practice (a $50 free bet → $50
  stake). Partial draw-down is a noted better-future
  system, deferred.
- **Multi-credit deploy across cycles:** if one deploy
  consumes credits from two qualifiers, the bet joins the
  **oldest consumed credit's** cycle (consistent with
  FIFO). Rare under whole-only + one-at-a-time use.

## Edge / adjacent cases

- **Goodwill / ad-hoc free bets** (no qualifier): manual
  entry, credit source `freebie`, no cycle to inherit.
  Existing model already supports this shape.
- **Winning qualifier:** no insurance payout (you won the
  bet) — no credit, matching v2.

## Deferred to Piece B (explicit)

Settlement-cascade auto-crediting (no operator
confirmation), auto-placing detection from a Betfair
place feed, provisional/negative pool balance, and
deploy-before-credit timing tolerance. All post-cutover.

## Governance note

This formalises and slightly extends the Session 70 pool
lock (FIFO confirmed; credit-in seam + operator-confirm
flow added). May warrant a short DR or a Session 70
amendment — operator's call whether to formalise.
