# Settlement-worker diligence — scope, grounded map, and outsourcing recommendation

**Created:** 2026-07-01 15:42 ACST (Session 214 open, headless runner)
**Author:** Claude Chat (diligence-first, pre-brief)
**Status:** Diligence grounding complete; outsourcing route awaiting operator confirmation. No Code brief drafted yet (that's downstream of the route decision).
**Bet-safety:** Read-only throughout. No settlement / Betfair / money code path was modified. Grounding was `grep`/`find`/`git log` + read-only file inspection + one read-only sub-agent map.

**Governing DRs:** DR-033 (settlement is the Betfair-operational side — this is the first money-path build item in the stretch), DR-027/DR-028 (two-database boundary — the settlement worker reads Betfair and writes v3 operational bet-state; the boundary is respected, see §3F), DR-032 (a Betfair market is the settlement spine).

---

## 1. Why this document exists

Settlement-worker (IOU + manual-match-to-lay) is the next build item on the
path to W16 cutover and the **first money-path item in this stretch**. Standing
practice is diligence-first — ground the real current codebase before any Code
brief is drafted. New this session (operator steer): because it's money-path and
"has to be really, really solid", explicitly weigh whether parts of the diligence
are better done by Code (out-of-session, can inspect and run the live codebase) or
a Cowork multi-agent review (parallel granular checks), rather than Chat solo.

This document is the grounded map plus that routing recommendation. It is
deliberately **not** the full deep audit — running the whole audit solo in Chat
would pre-empt the very routing decision the operator asked to weigh.

---

## 2. What the settlement worker is, in plain terms

After a race runs, something has to look at the Betfair result and mark each of
your pending bets as **won**, **lost**, or **void (money back)** — and, when a
Safety-Net bet loses in a way that triggers a refund, record the **free bet you're
owed** (the "IOU"). That "something" is the settlement worker. Two ways a bet gets
settled:

- **Automatic** — a periodic worker sweeps bets whose race has finished, reads the
  Betfair settled market, and marks them. If it sees something odd (dead-heat,
  a scratched runner, an unexpected result), it doesn't guess — it parks the bet
  as **PROVISIONAL** for you to decide by hand.
- **Manual** — you review the PROVISIONAL pile and mark each one yourself
  ("manual operator resolution" — this is the "manual-match-to-lay" surface).

The **IOU** isn't a separate machine — it's the free-bet credit that gets recorded
after a qualifying bet settles as lost. It's created as an append-only event, then
"spent" when you place a bet with it later.

---

## 3. Grounded map (read-only, bethub-v3 @ e2638fa)

Core files:
- `workflows/bet_entry/v1/settlement.py` — 1,354 lines. The worker itself:
  auto-settlement pass (`run_settlement_pass`), provisional pass
  (`run_provisional_resolution_pass`), the pure resolver state machine
  (`_resolve_settlement_for_bet`), the manual operator path
  (`apply_manual_operator_resolution`, ~line 1128), and schedulers.
- `clients/betfair_client/v1/settlement.py` — 118 lines. Reads the Betfair
  settled-market REST surface (`market_settlement()`, `GET /v1/market/{id}/settlement`).
- `domain/settlement/__init__.py` — **empty (0 lines)**.
- IOU / free-bet credit lives in the promos workflow, **not** in settlement.py:
  `workflows/promos/v1/fb_credit.py` (`record_free_bet_credit`) and
  `fb_deployment.py` (`record_free_bet_deployment`); events in `domain/promos`.

### 3A. IOU path
Free-bet credit = a `FREE_BET_CREDITED` event in `promo_events` (append-only,
immutable). Created by `record_free_bet_credit()` when a settled-**lost**
Safety-Net qualifier with a promo attachment is confirmed. Consumed/resolved by
`record_free_bet_deployment()` when the operator places a bet using it. Amount =
`stake × return_pct` (no cap). **Not written by settlement.py** — settlement only
sets the bet's terminal state; the credit is a separate downstream call.

### 3B. Manual-match-to-lay path
`apply_manual_operator_resolution()` transitions a bet **PROVISIONAL → terminal**
(SETTLED_WON / SETTLED_LOST / VOIDED) on operator action. Source state must be
PROVISIONAL; target must be terminal (both enforced). Entry points, verified wired:
- `GET /api/v1/bets/provisional` — lists the PROVISIONAL pile.
- `POST /api/v1/bets/provisional/{bet_id}/resolve` — resolves one bet
  (`ui/api/routers/provisional.py:344` calls the worker function).
"Lay" / "matched" here is the ordinary Betfair matched-stake/price recorded at
placement (W4 reconciliation), not a special settlement action.

### 3C. Live-integration status — the headline (S189 taxonomy)
- **Auto-settlement worker (`run_settlement_pass` + provisional pass + schedulers):
  IMPLEMENTED-NOT-LIVE, sub-reason never-provisioned.** Verified directly:
  `run_settlement_pass`, `run_provisional_resolution_pass`, and `SettlementScheduler`
  are referenced **nowhere** outside `settlement.py` and its tests — not in the
  composition root (`ui/api/dependencies/composition.py`), not started in
  `ui/api/main.py`, not exported from the workflow `__init__.py`. It has never run
  in a live app and has never touched real Betfair data.
- **Manual resolution path: LIVE-WIRED but STARVED.** The provisional router *is*
  included in the app (`main.py:139`) and *does* call the worker function. So the
  endpoint is reachable. But it resolves PROVISIONAL bets, and the only thing that
  produces PROVISIONAL bets is the auto-worker that isn't switched on. In a live
  run today the queue would always be empty (unless a bet were hand-seeded).
- **Betfair read surface:** real REST endpoint exists; in tests everything uses a
  `MockSettlementReader`. A `RealSettlementReader` adapter for the live path is
  **not composed** anywhere yet.

Net: the whole settlement chain is **code-complete, well-tested against fake data,
and not yet plugged into anything real.**

### 3D. Test coverage
Fixture-based only. ~50+ tests in `tests/workflows/bet_entry/v1/test_settlement.py`
(resolver logic, pass loop, counters, storage, one end-to-end SQLite pass), ~10 in
`tests/ui/api/test_provisional.py` (manual endpoint, happy + 404/409/422/500),
~20+ in the fb_credit tests. **Zero live-mode tests** — all use MockSettlementReader
or in-memory storage.

### 3E. Money-state write surfaces (the reversal-cost surface)
Where money-state gets written by this path:
1. `settlement_state` updates — 3 sites (auto pass, provisional pass, manual pass).
2. Reconciliation bookkeeping (`last_reconciled_at`, `reconciliation_attempts`) —
   after every transition; **the attempts counter is non-idempotent** (increments
   per pass).
3. Last-read market-state snapshot persistence.
4. Free-bet credit write (`FREE_BET_CREDITED`) — downstream, append-only.
5. Free-bet deployment write — consumes a credit; append-only, **no direct reversal**.
No direct cash/balance mutation in this path (cash-flow is separate, W14).

### 3F. Boundary check (DR-027/028)
Clean at first read: settlement reads Betfair (analytical/canonical source) and
writes v3 operational bet-state by reference — no shared tables, no caching of
capture.db. Worth Code re-confirming as part of any deeper pass, but no boundary
violation surfaced.

---

## 4. Money-path risk concentration (where "really solid" has to bite)

Ordered by reversal cost × likelihood of a subtle miss:

1. **The whole chain has never run live.** Green fixture tests ≠ done (S189). The
   dearest bug class here is a live-wiring gap (à la the S189 "Log Past Bet" 500s),
   not a logic bug — the logic is tested, the *plumbing* is unproven.
2. **Settlement → free-bet-credit is a two-step with a failure window.** The bet's
   terminal state is committed by settlement; the IOU credit is a *separate*
   downstream call. If settlement commits and the credit write then fails, you've
   recorded the loss but not the refund you're owed. Needs an explicit look at
   whether that gap is guarded (transaction / retry / reconciliation).
3. **Non-idempotent bookkeeping.** `reconciliation_attempts` increments per pass; a
   re-run or double-schedule accumulates. Harmless to money directly, but a smell
   worth confirming doesn't leak into any settlement decision.
4. **v1 deferreds in code comments** — e.g. post-settlement market-void
   re-transition noted as not implemented at v1. Need the full list of "not at v1"
   carve-outs so none of them is a silent money-path hole at launch.
5. **Odd-result handling** (dead-heat, removed runner, unexpected state) — the
   resolver parks these as PROVISIONAL rather than guessing. Correct instinct;
   needs verifying the parking is exhaustive (nothing odd slips through to an
   automatic wrong settlement).

---

## 5. Outsourcing evaluation (the operator's steer)

Three ways to do the deep diligence, weighed against `governance.md`'s multi-agent
review heuristic (**high reversal cost OR high blind-spot risk**; the "this is a
software call, defer to me" tell; multi-agent review is several hours of overhead,
reserved for high-stakes decisions).

**Does this clear the governance bar?** On reversal cost — yes, mis-settling real
bets or mis-crediting IOUs is real money. On blind-spot risk — yes, and pointedly:
the biggest finding here (the whole chain is unproven live) is exactly the
anchoring trap governance warns about — code that reads clean but was never
exercised. So a cross-check is justified. **But** governance's four-seat pattern is
a tool for reviewing a *decision* (is this design/sequencing sound), and there
isn't a single fork under review here — there's a body of money-path *code* to
verify. That points at empirical verification first, adversarial decision-review
second — and only when there's a live design to gate.

| Option | Best at | Weakness here | Overhead |
|---|---|---|---|
| **Chat solo** | The map, the risk framing, the routing call (this doc) | Can only *assert* code behaviour — can't run tests, trace live wiring, or exercise paths. Most anchored. | Low |
| **Code, read-only, out-of-session** | *Grounding* — run `uv run pytest`, trace the composition root, confirm the not-launched finding, walk every money-state write, check the settlement→credit failure window empirically | Single-model (shares Claude priors); not adversarial | **Low, high value** |
| **Cowork multi-agent** | Adversarial, cross-model, parallel granular checks across many money surfaces at once | High operator overhead; premature on code that isn't even wired to launch | High |

### Recommendation — staged hybrid, not solo and not straight-to-panel

1. **Chat has done the scoping map** (this document). That was Chat's job and it's
   done.
2. **Route the deep empirical verification to Code (read-only, out-of-session)
   next.** This is where "really solid" gets real: Code can *run* the tests,
   *confirm* the not-launched finding, *trace* every money-state write, and
   *pressure-test* the settlement→credit failure window and the v1 carve-out list —
   all things Chat can only assert. Low overhead, high grounding value. This is the
   recommended next step. It replaces "Chat keeps reading solo," which is the
   weakest option for money-path code.
3. **Reserve the Cowork multi-agent review for the pre-launch go/no-go**, not now.
   The money-path *does* clear the governance high-reversal/high-blind-spot bar, so
   a cross-model adversarial pass **is** warranted — but the right moment is once the
   worker is actually wired to launch and the design is stable, as the gate before
   real money flows. Running a multi-agent panel today, on a chain that isn't even
   switched on, spends hours of overhead reviewing plumbing that will change when it
   gets wired. This aligns with the already-parked **"Cowork sub-agent review →
   pre-W16 cutover go/no-go"** item — settlement is exactly the kind of thing that
   review should cover.

In one line: **Chat maps → Code grounds (read-only) → Cowork adversarially gates at
pre-launch.** Don't collapse the three into one solo pass, and don't fire the
expensive panel before there's a live design to shoot at.

---

## 6. Recommended next step (pending operator confirmation)

If the operator agrees the route: draft a **read-only Code investigation brief** (not
a change brief) that hands Code the §4 risk list and §3 map and asks it to
empirically confirm/refute each finding against the live codebase and test suite,
and return a grounded report. That report then becomes the real substrate for the
eventual settlement-worker build brief — and for the pre-launch Cowork gate.

No brief is drafted yet — the route is the operator's call to confirm first.
