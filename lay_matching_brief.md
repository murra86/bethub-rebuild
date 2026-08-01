# Lay matching — implementation brief (worklist 0t-A)

**Operator BUMPED this up the queue on 31 Jul 2026**, ahead of the Phase 1 deploy.
Evidence base: `bet_integrity_audit_s260.md` (defect: cycle tracking 74.2%) and
`pl_audit_s260.md` D8. Every audit claim below was re-verified against the live
DB and the code during design; five audit corrections are recorded in §6.

---

## 0. Operator summary — what this means for your betting day

When you hedge a free bet, you place the lay on Betfair a second or two *before*
you log the back in the tool. The tool only ever looked backwards — at bets that
already existed — so at the moment you place the lay there is nothing to link it
to. The list is empty, every time. That is why the pairing prompt has never once
appeared: not a bug in the matching, a bug in the direction.

The fix is to look the other way. When you log the back, the tool checks whether
you just placed a lay on that same runner moments ago, and joins them up for you.
No extra clicks, and nothing to remember.

Three things change: new lays link themselves from now on; the warning that tells
you a lay is unpaired stops only looking back 24 hours (which is why it showed you
1 of 32); and the ⚠ marker on the race screen becomes cycle-aware instead of
turning green as soon as *any* back exists on that runner.

Your 32 existing unpaired lays get repaired separately, as a reviewed batch. **No
money moves — not one stake, price, result or profit figure changes.** Only the
joining-up.

---

## 1. Root cause (proven, not inferred)

`list_parent_cycle_candidates` offers only **pre-existing** BACK bets. The
operator places the LAY first — **32 of 32 cases, deltas 1.1–4.0 s, no
exception.** So the candidate list is empty at lay time and the door has never
fired in production. The 29 pairs that do exist came from the S246 hand backfill;
**zero lays have paired since 21 Jul.**

**A second, independent bug in the same area:** `CANDIDATE_LOOKBACK_SECONDS`
(24 h) is used for *both* the unpaired-lay list floor and candidate resolution,
**and candidates are filtered against `now` rather than against the lay.** That is
why the existing repair button cannot reach the older 31 even when they are shown.

---

## 2. Design — forward-link at BACK time (recommended)

Server-side in `log_bet` (`ui/api/routers/racing.py:999`). After the back commits:
find LAY bets on the same market + selection whose cycle holds no back, placed
within **180 s** of the back. If **exactly one**, move it into the back's cycle —
the same single `bets.cycle_id` write the existing assign-cycle door makes — and
echo `linked_lay_bet_id` in `LogBetResponse`. If **zero or 2+**, write nothing and
let Burst review surface it.

* **Best-effort, never blocking.** Modelled on `FB_DEPLOY_EVENT_WRITE_FAILED`: a
  failure returns a warning and never fails the bet. Honours the standing rule —
  allow → flag → review later.
* **Atomic + audited.** The link and a raw-inserted `bet_edited` row share one
  `BEGIN IMMEDIATE` txn (reassign-door pattern, `ui/api/routers/bets.py:1701-1915`).
  No migration needed — `bet_edited` is already in the live CHECK constraint.
* **Undo** is the existing `POST /v1/bets/{id}/assign-cycle` with `cycle_id: null`.
* **Ambiguity self-resolves.** Forward-linking consumes candidates
  chronologically, so the one genuinely ambiguous case in the data (two identical
  Tim@BetFair lays, $43.10 @ 14.0 on Sir Myka) resolves by time — 2.4 s / 2.3 s
  versus 100.3 s / −95.6 s — which is the same tiebreak S246 sanctioned.

**Options rejected:** auto-match on market+selection+account with confirmation
(adds a click to the hottest path and still needs the time tiebreak); a deferred
proposer (leaves the window open for more unlinked lays, and the operator already
has Burst review for exactly this).

**Accepted known behaviour:** an explicit lay-time pairing *decline* would be
silently overridden by the forward-link. Currently hypothetical — that door has
never fired.

---

## 3. Repair of the 34 existing rows

New `ops/repair_lay_cycles.py`, on the `ops/correct_promo_selection.py` template:
dry-run by default, `--apply` to commit, one transaction on a fresh bare
connection, `PRAGMA foreign_keys=ON` before `BEGIN IMMEDIATE`, one `bet_edited`
per move whose before/after snapshot is **identical** with the from→to recorded in
`notes` — **the identical snapshot is itself the no-money-moved proof.**

Process in `placed_at` order, and do the **2 mis-linked free bets FIRST**
(`bet-76ae5c5a…`: `fc14344a…` → `a61d684a…`; `bet-8149d9e9…`: `a61d684a…` →
`1aa7cca6…`) — both are pairing targets for lays `bet-0a498911…` and
`bet-d67c5ffe…` and would otherwise strand them. 34 rows total, all `cycle_id`
only; the reverse map is recoverable from the audit events.

Post-repair cycle count: **215**.

---

## 4. Flag widening + where the operator sees it

* Add `anchor: datetime | None` to `list_parent_cycle_candidates` — floor becomes
  `anchor - lookback`; `list_unpaired_lays` passes the lay's own `placed_at`. The
  live quick-lay path is unchanged.
* Separate `UNPAIRED_LAY_LOOKBACK_DAYS = 30` for the list floor.
* **Surfaces:** Burst review is primary (its Pair/Undo UI already works); the
  money check's `CYCLE PAIRING WATCH` capped at 5 lines plus "…and N older"; and
  **`RaceActivityBoard.tsx:373`'s ⚠ becomes cycle-aware** — today it only asks
  "is there a back on this selection", which is why it went green 2 s later on all
  32.

---

## 5. Tests, invariant, rollback

**P&L invariant is structural, not merely tested:** `cycle_id` appears nowhere in
`workflows/balances/v1/balance_derivation.py` or `ui/api/routers/cash_flow.py`,
and `_lay_commission_shares` keys on `(account_at_book_id, betfair_market_id)`.
**Test anyway:** snapshot per-bet `bet_net_pnl` and the total across all 336 bets
before/after the repair on a DB copy and assert byte-identical; assert every
`bet_edited` payload has `before == after`.

Red-before: `list_unpaired_lays` returns 1 on a 22-Jul-shaped fixture (today's
behaviour) and 32 after the anchor fix. Plus: forward-link fires on a
lay-then-back sequence; does nothing on 0 or 2+ candidates; never fails the bet
when the link write errors; undo restores.

Rollback: the linker is one code path behind a best-effort try/except — revert and
restart. The repair is reversible from its own audit events.

---

## 6. Corrections to the audit (verified against code + live DB)

1. It is **32 of 32** lay-before-back, not 31 — no exception exists.
2. The Sir Myka ambiguity is **not** resolvable by account/book/stake as the audit
   claimed — both lays are identical. **Time is the working discriminator.**
3. **The audit's fix #1 was backwards.** It proposed holding the lay's group open
   so the free bet joins it; but the FB must keep its qualifier's cycle via
   `resolve_inherited_cycle`, so **the LAY must move**, not the FB.
4. Post-repair cycle count is **215**, not 216 (`fc14344a…` also vacates).
5. The V2 chain re-verified exact (credits `19a3e9d5…`/`5e32f0d7…` → bets
   `bcd524f8…`/`2527b525…`).

---

## 7. Same-day-ship risk

The linker adds a `BEGIN IMMEDIATE` write to the hottest race-day path and can
contend with the settlement worker — needs `busy_timeout=5000` and an
unconditional swallow-to-warning. `npm run build` (`tsc -b`) must run, because
vitest does not typecheck.

**Recommended split: ship the linker + flag widening + cycle-aware board flag
today** so no new lay lands unlinked tomorrow, **and hold the 34-row repair until
after race day** — it wants a quiet app and a fresh backup, and it fixes history,
which is not urgent.

## 8. DECISIONS NEEDED FROM OPERATOR

**One.** Run the 34-row repair *before* tomorrow's race day (app closed, backup
first, ~5 min) or *after* it? Everything else is settled by code precedent.
Default if unanswered: **after**, per §7.

---

# v2 — Adversarial review (NORMATIVE; overrides §0–§8 on conflict)

Verdict **SAFE WITH FIXES**. The structural money claim survives; the matching
predicate did not.

## L1 — the P&L claim was overstated (reword, do not weaken the test)
"Not one profit figure changes" is false as written: two **per-cycle displays**
are cycle-keyed and will change value — `ops/settlement_review.py:673-792`
(`Cycle {id} — net ±$X`) and `BetLog.tsx:385-418` `CycleChain`'s `Net:`. That is
the *intent* (the groupings become correct), not a defect. Per-bet net, balances
and the grand total are untouched (`cycle_id` has zero hits in
`balance_derivation.py` and `cash_flow.py`).
**Correct wording:** "no stake, price, result or per-bet profit changes; per-cycle
net *groupings* become correct." Keep the byte-identical per-bet + total assertion.

## L2 — SPLIT-COMMIT TRAP (most severe)
§2 said "the same single `bets.cycle_id` write the assign-cycle door makes" — but
that door calls `bet_storage.update_cycle_id`
(`ui/api/routers/bets.py:2738` → `store/repositories/bets.py:924-949`), which runs
on a **separate autocommit connection**. Adapter + raw `bet_edited` insert = two
commits, and a crash between them leaves a moved lay with **no audit row** —
unreversible.
**Fix: raw `UPDATE bets SET cycle_id=?` inside the same `BEGIN IMMEDIATE` as the
audit insert. Never the adapter.** (This is the S254 lesson again.)

## L3 — missing fence: target cycle may already hold a lay on that selection
The manual door refuses this (`bets.py:2716-2737`); the linker as designed does
not. Two free-bet conversions inheriting one qualifier cycle on the same runner
would produce a cycle with two lays, invisible to `list_unpaired_lays` forever.
**Fix: reuse `_cycle_holds_lay_on_selection` and skip when true.**

## L4 — 180 s is 45× the evidence, and it opens a real wrong-link class
Live DB: all 32 deltas are **1.1–4.0 s**; the next value is 8.2 s, then 100.3 s.
But **42 back↔back pairs sit within ±180 s on the same market+selection** (mostly
different people/books). When backs are logged out of order, back A steals the lay
intended for back B.
**Fix: window 30 s, AND require `lay.placed_at < back.placed_at`.** Kills the
whole class at zero cost to real cases.

## L5 — busy_timeout on the hot path
§7's `busy_timeout=5000` can add 5 s to a race-day bet log when the settlement or
reconciliation worker holds the lock. **Use 1000 ms** — the linker is best-effort
by design.

## L6 — account scoping would be ACTIVELY WRONG (do not add it)
I asked whether the predicate needed `account_at_book` scoping. It must not have
it: all 61 lays sit on one Betfair account (`b4cb3fd6…`, owner `ef9cf678…`) while
the backs span **4 `account_id`s** — person-scoping would refuse ~197 legitimate
backs. **Time-narrowing (L4) is the correct discriminator, not identity.**

## Verified by review (do not re-litigate)
`bet_edited` is in the live CHECK; 32/32 lay-before-back; §6 correction #3 is right
(`fb_credit.py:518-566` forces the FB to keep its qualifier's cycle); the repair
ids and cycles are exact and FBs-first is **necessary** (else lays `0a498911…` /
`d67c5ffe…` strand on `fc14344a…`); 248 − 33 = **215** confirmed; the live
quick-lay path is unchanged (`racing.py:1178` passes no `now`);
`_lay_commission_shares` keys `(account_at_book, market)` and is cycle-free;
`bet_net_pnl` takes row + share only; the Sir Myka ambiguity does self-resolve in
live chronological order; a half-applied link is impossible once L2 is honoured.

**Ship order confirmed by review: linker + flag widening + cycle-aware board flag
today; the 34-row repair after race day.**
