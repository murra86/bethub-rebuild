# Settlement-correctness re-scope — read-only investigation

**Session:** S222 first action (auto-executed by the headless runner).
**Type:** Read-only investigation + design write-up. **No code touched, no flag flipped, no brief locked.**
**Codebase:** bethub-v3 @ HEAD `e2638fa` (byte-identical to the S221 close baseline; dirty tree unchanged).
**Anchor:** 2026-07-03 18:23 ACST (DR-021).
**Grounds:** Code's STOP report `settlement_pending_sweep_nullfix_report.md` (F1–F3). This document answers the three questions the S222 prompt set — why bets sit NULL, the LAY settlement design, and what a correct fix must span — and closes the one link Code left untraced (how won/lost flows to P&L for a lay).

**Governing DRs:** DR-032 (Betfair settlement spine), DR-033 (settlement Betfair-only / placings analytical), DR-030 (module boundaries), DR-027/028 (two-DB boundary), DR-021 (Adelaide anchors).

---

## 0. TL;DR (plain language)

- **Why the worker never settled the $5.26 lay:** the settlement worker only looks at bets stamped `"pending"`. But **nothing in the whole codebase ever stamps a bet `"pending"`** — I grep-proved it. Every live-logged bet is born with an empty settlement slot (NULL) and nothing ever fills it. So the worker's in-tray is permanently empty for *every* live bet, not just this one. This is a **create-path gap**, not a reconciliation step that failed to run.
- **This is bigger than "the one-liner is inert."** The settlement pipeline has never engaged a single live bet. It passed its build tests because the tests hand-stamp bets `"pending"` — a state the real app never produces.
- **The lay inversion is real and I traced it all the way to the money.** The resolver records a lay from the *market's* point of view (favourite won → "won"). But the P&L/balance layer reads that same field as the *lay's own* point of view (lay won → "won"). They disagree by exactly one inversion. Left unfixed, a lay that actually **won** would be booked as a **loss** on your ledger (and vice-versa) — a silent, self-inflicted accounting error. The fix is to invert won/lost for lays inside the resolver (WINNER→SETTLED_LOST, LOSER→SETTLED_WON).
- **A correct fix spans three edits that must land together:** (1) fix the pending-state so the worker actually sees live bets, (2) make the resolver lay-aware, (3) change the one test whose contract currently says "don't sweep NULL bets." Plus a dead-heat/removed-runner design question for lays that is genuine new money-path design, not a surgical tweak.
- **Two open calls are yours (operator / operator-Claude), not mine to lock:** (a) *how* to fix the pending-state — stamp `"pending"` at create time, or teach the worker that NULL means pending; (b) the dead-heat/Rule-4 liability rules for a losing lay. My recommendation on (a) is below with reasoning; (b) needs its own short design pass.

---

## 1. Q1 — Why do logged bets sit at `settlement_state = NULL`?

### 1.1 The mechanism (confirmed, end-to-end)

The NULL is a **create-path default**. The live race-screen entry builders never stamp a settlement state, and the field defaults to None:

- `BetRecord.settlement_state: SettlementState | None = None` — the domain default (`domain/bets/__init__.py:319`).
- **Live lay entry** (the repro bet) goes through `build_hedge_bet_record` (`record_builder.py:267`), reached from the race-screen lay path (`ui/api/routers/racing.py:1094`). It **does not pass `settlement_state`** → stays None.
- **Live soft-book entry** goes through `build_soft_book_bet_record` (`record_builder.py:353`), reached from `orchestrator.log_soft_book_bet` (`racing.py:934`). It **also does not pass `settlement_state`** → stays None.
- **Only** `build_manual_bet_record` (`record_builder.py:509`) stamps a state — and it *requires a terminal one* (`settlement_state` field `:491`, validated terminal-only `:525`). That is the "Log Past Bet" / settle-at-entry path, where the bet is already resolved when logged. It is not the live path.
- The store adapter is a faithful pass-through: `settlement_state = record.settlement_state.value if not None else None` (`bet_store_adapter.py:69–73`). None in → NULL on disk.
- Schema: `settlement_state TEXT` (nullable) (`store/schema/bets.py:39`).

**So: a live-logged bet is born NULL and stays NULL.**

### 1.2 The decisive finding — nothing ever writes `"pending"`

A grep across `workflows/`, `store/`, `ui/` for any write of `SettlementState.PENDING` / `"pending"` as a settlement state returns **only the sweep query itself** (`settlement.py:1026`) and a docstring. There is **no producer** of the `"pending"` state anywhere.

Consequence: the settlement worker sweeps `settlement_states=(SettlementState.PENDING.value,)` = `("pending",)` (`settlement.py:1026`), but that population is **structurally empty** for every live bet. The PENDING→terminal pipeline has **never engaged a live bet**. The repro lay is not a one-off; it is the general case.

Why the build tests didn't catch it (the S189 lesson, again): the settlement tests construct records already stamped `"pending"` (a state production never emits), so they exercise a sweep population the live app never fills. Green-on-fixtures, dead-on-arrival live.

### 1.3 It is NOT a never-run reconciliation

The S221 observations (stale amber "unmatched" warning, `reconciliation_attempts=0`) point at the **match-reconciliation** path, which is a *different axis* from settlement:

- Reconciliation resolves `match_status` (`MatchStatus.FINAL_FULL` / `FAILED` / `PROVISIONAL_PENDING`), **not** `settlement_state`.
- The string `"pre_settlement_pending"` at `reconciliation.py:293` and `:304` is a **`detail` annotation only** (a reason-code payload), never written to the `settlement_state` column.

So even a reconciliation pass that *did* run would not have stamped `settlement_state="pending"`. The NULL is independent of reconciliation. (The amber warning + zero reconciliation count are a separate, cosmetic/match-status matter — worth its own look, but not the settlement blocker.)

### 1.4 The intended lifecycle vs. the codebase's own disagreement

The spec (§2.6/§3.2, cited verbatim by the F2 test's docstring — *"Only PENDING is the pass-loop population per §2.6 §3.2"*) presumes a distinct `"pending"` state is the worker's in-tray. But the codebase contradicts itself on what "pending" *is*:

| Layer | What it treats as "unsettled / pending" | Anchor |
|---|---|---|
| **Create path** | writes **NULL** (never `"pending"`) | `record_builder.py:267/353`, default `:319` |
| **Balance / P&L layer** | **NULL, `"pending"`, `"provisional"` all count as unsettled** | `balance_derivation.py:151` |
| **Settlement worker + F2 test** | **only `"pending"`** (NULL explicitly excluded) | `settlement.py:1026`; test `:607–639` |

The balance layer already treats NULL as pending (`_PENDING_SETTLEMENT_STATES = frozenset({None, "pending", "provisional"})`). The settlement worker is the outlier. This split is the root of the whole bug: **the create path and the P&L layer agree that NULL means "not yet settled"; only the settlement worker (and the test guarding it) insist on a `"pending"` literal that nothing produces.**

---

## 2. Q2 — The LAY settlement design (and the P&L link Code left untraced)

### 2.1 Confirmed: the resolver has no side branch

`_resolve_settlement_for_bet` (`settlement.py:558–751`) settles purely on the Betfair runner's **objective** status:

- `RunnerSettlementStatus.WINNER → SETTLED_WON` (`:688–724`, via the dead-heat/reduction winner-guard).
- `RunnerSettlementStatus.LOSER → SETTLED_LOST` (`:726–736`).
- `REMOVED → VOIDED`; runner-not-found / unknown → `PROVISIONAL`.

There is **no `record.side` branch** anywhere in the resolver. `BetRecord.side` was added later (W12.1, `domain/bets/__init__.py:345`); this W6.5-era resolver never consumes it. Confirmed.

### 2.2 The untraced link — CLOSED: P&L reads settlement_state as the *lay's own* perspective

Code flagged one link it hadn't traced: *how downstream P&L consumes SETTLED_WON/LOST for a lay.* I traced it. `balance_derivation.py::_bet_cash_return` (`:190–229`) is explicit (`:203–215`):

> *"`settlement_state` is interpreted as the **lay bet's own** perspective (matching how the existing back-bet logic interprets won/lost)."*
> - `settled_won` (lay won; backed selection lost): return `L + S×(1−c)` → **net cash +S×(1−c)**
> - `settled_lost` (lay lost; backed selection won): return `0` → **net cash −L** (full liability lost)
> - `voided`: net cash 0

with `_is_lay` (`:164–168`) and `_lay_liability = matched_stake × (matched_price − 1)` (`:171–187`).

**So the money layer expects a BET-RELATIVE state, and the resolver produces a MARKET-OBJECTIVE state. For a lay they are exact inverses:**

| Real outcome | Runner status | Resolver writes | P&L reads it as | Correct state | Money error |
|---|---|---|---|---|---|
| Laid selection **wins** → lay **loses** | WINNER | **SETTLED_WON** | lay won → **+S×(1−c)** | SETTLED_LOST (−L) | **books a loss as a gain** |
| Laid selection **loses** → lay **wins** | LOSER | **SETTLED_LOST** | lay lost → **−L** | SETTLED_WON (+S×(1−c)) | **books a gain as a loss** |

This is worse than an "overpay" in the liveproof sense (§4d "nothing silently overpaid"): the worker wouldn't over-pay a payout, it would **silently invert the ledger entry** — a winning lay recorded as a full-liability loss, or a losing lay recorded as a win. The liveproof plan's "correct, not just settled" bar (§4a) is exactly what this violates.

### 2.3 The fix direction (matches the prompt) and the guard interaction

**Core fix:** make the resolver `side`-aware. For `record.side == LAY`, invert the terminal mapping: **WINNER → SETTLED_LOST, LOSER → SETTLED_WON.** VOIDED stays VOIDED (net cash 0 both sides — `balance_derivation.py:212–213` confirms a voided lay nets 0). Then the P&L layer's bet-relative interpretation is satisfied and the ledger is correct.

**But the dead-heat / removed-runner park guard needs design, not a straight sign-flip** (this is genuine new money-path work):

- The winner-guard (`_evaluate_winner_guard`, gating the WINNER branch at `:695`) is built for a **backer's payout reduction** — dead-heat halving, Rule-4 deductions on the *winning* selection. It parks-to-PROVISIONAL rather than overpay a backer.
- After inversion, a **losing lay** (laid selection WON) routes to SETTLED_LOST. A dead-heat on the winning side **does** reduce a lay's liability (a dead-heat winner means the backer is paid at reduced stake, so the layer's liability is correspondingly reduced). A naive inversion would send this down the LOSER→SETTLED_WON... no — down the WINNER→(invert)→SETTLED_LOST path, **bypassing** the guard's reduction logic and paying **full** liability `L` when the true liability is reduced. That is a real (if smaller) money error in the opposite direction.
- A **winning lay** (laid selection LOST → LOSER branch, which has no guard) correctly just collects `S×(1−c)`; removed runners / Rule-4 elsewhere don't reduce a winning lay's collect. No guard needed there.

**So the guard logic is asymmetric for lays and needs a small explicit design:** the reduction/dead-heat handling that currently protects a backer's *payout* must be re-expressed as protection of a lay's *liability* on the losing-lay path. Simplest safe interim: **park any lay whose race had a dead-heat or a material removed-runner reduction to PROVISIONAL** (manual settle), rather than auto-compute reduced liability — mirroring the worker's existing "park anything uncertain rather than overpay" stance (liveproof §7). This keeps the money-path invariant while deferring exact lay-liability maths.

---

## 3. Q3 — What a correct fix must span (files / anchors)

Three edits that **must land together** (a store fix without the resolver fix would start mis-settling lays live — the exact half-fix the worker-OFF hold guards against), plus one design decision and one deferred design question.

| # | What | File / anchor | In old §8 scope? |
|---|---|---|---|
| 1 | **Pending-state fix** (see §3.1 for the two options) | *Option A:* `record_builder.py:267` + `:353` (stamp PENDING on live entry) · *Option B:* `settlement.py:1026` sweep widen **+** `store/repositories/bets.py:823–862` `list_unsettled_bets` (add `IS NULL` OR-branch, widen param type `tuple[str, ...]` → `tuple[str \| None, ...]`, reconcile in-memory vs SQLite divergence) | No (both spill outside `settlement.py`) |
| 2 | **Resolver LAY inversion** | `settlement.py:_resolve_settlement_for_bet` `:688–736` — add `record.side == LAY` branch inverting WINNER/LOSER | No (`_resolve_*` explicitly forbidden by old §8) |
| 3 | **F2 test-contract change** | `tests/workflows/bet_entry/v1/test_settlement.py::test_pass_sweeps_only_pending_bets` `:607–639` — currently asserts NULL is **not** swept, citing §2.6/§3.2 | In test file, but changes a spec-citing green test |
| 4 | **Lay dead-heat/Rule-4 liability rule** (design) | resolver winner-guard `:695` + `_evaluate_winner_guard` — decide park-vs-compute for a losing lay's liability | New design (§2.3) |
| 5 | **Spec reconcile** | §2.6/§3.2 settlement model — align the "pending population" definition with whichever Option A/B is chosen | Governance |

The old one-line brief is correctly **SUPERSEDED**. This is a multi-file money-path change with a design decision inside it — not a surgical pass.

### 3.1 The pending-state fix — recommendation (operator call to confirm)

Two coherent ways to make the worker see live bets:

**Option A — stamp `"pending"` at create time.** Live builders (`build_hedge_bet_record`, `build_soft_book_bet_record`) set `settlement_state=SettlementState.PENDING` on entry.
- *Pros:* makes the lifecycle explicit and self-documenting; keeps the worker sweep (`:1026`) and the F2 test's spec-citing contract **intact** (only PENDING is swept — we just make the create path actually produce PENDING); smallest change to the settlement/read side.
- *Cons:* touches the live **bet-creation path** (money-path-adjacent write flow); leaves the one existing repro NULL bet needing a one-off backfill (or a defensive NULL branch); NULL becomes a "should-never-happen" state that still wants defensive handling.

**Option B — teach the worker that NULL means pending.** Widen the sweep + add the store `IS NULL` branch + widen the param type + reconcile the in-memory/SQLite `None`-handling divergence + invert the F2 test.
- *Pros:* self-heals the existing NULL bet and any legacy rows; aligns the settlement worker with what the balance/P&L layer **already** does (NULL ∈ pending, `balance_derivation.py:151`); leaves the live bet-creation path untouched.
- *Cons:* more surface area on the read/store side; must fix the false-green trap Code flagged (in-memory store honours `None`, SQLite doesn't — a unit test would pass while production stays broken); inverts a spec-citing test.

**My recommendation: Option A as primary** (stamp PENDING at create), because it makes the model explicit, keeps the F2 spec contract honest rather than inverting it, and confines the "pending population" to a real, produced state. Pair it with a **one-off backfill** of the single existing NULL lay (or a narrow defensive NULL-treated-as-pending branch in the sweep) so the repro bet is covered without a general NULL-semantics change.

**Caveat that could flip me to B:** Option A edits the live bet-entry write path. If the operator/operator-Claude judge that path too sensitive to touch right now (it's the flow that logs real bets), Option B's "leave creation alone, fix the read side" blast-radius is the safer call — at the cost of the false-green trap needing a real SQLite-path test. **This is a money-path decision I am deliberately not locking** — flagging it for the design-with-operator step.

---

## 4. What stays an operator / operator-Claude decision

1. **Option A vs B** for the pending-state (§3.1) — recommendation given, not locked.
2. **Lay dead-heat/Rule-4 liability** (§2.3) — park-to-PROVISIONAL interim vs compute reduced liability. New money-path design; deserves its own short go-ahead.
3. **The re-scoped brief itself** — spans `settlement.py` + (`bets.py` or `record_builder.py`) + resolver + test + spec-reconcile. To be **designed with the operator**, then handed to Code as one bounded, all-together brief. Worker stays **OFF** until all of it lands and is re-proven against the repro lay.

Everything else here (the create-path NULL mechanism, the P&L inversion trace, the file anchors) is **confirmed fact**, not a call.

---

## 5. Evidence log (all read-only)

- **HEAD `e2638fa`** — no git write op; no code, test, flag, or launcher touched. Only this rebuild-folder document was written.
- Direct reads: `settlement.py` (resolver `:558–751`, sweep `:1026`), `store/repositories/bets.py` (`list_unsettled_bets` `:823–862`), `workflows/bet_entry/v1/reconciliation.py` (`:255–329`), `record_builder.py` (builders `:267/:353/:509`, inputs `:428–491`, `:560–586`), `bet_store_adapter.py` (`:55–154`), `balance_derivation.py` (`:120–229`), `domain/bets/__init__.py` (`:257–371`), `store/schema/bets.py` (`:38–39`), `ui/api/routers/racing.py` (`:900–934`, `:1088–1105`).
- Greps: no producer of `settlement_state="pending"` anywhere in `workflows/`+`store/`+`ui/` (only the sweep query + docstrings); `side`/LAY money consumption isolated to `balance_derivation.py`.
- **Confidence:** create-path NULL mechanism — certain (code + defaults + grep). No-`"pending"`-producer — certain (grep). LAY P&L inversion — **certain** (resolver objective-mapping vs `balance_derivation.py:203–215` bet-relative interpretation, both quoted). Lay guard interaction — high (guard is backer-oriented; lay-liability path undefined).
- **Bet-safety:** worker remains OFF; no money path exercised; capture/DB reads not required this pass; bethub-v3 byte-identical.

---

## 6. Recommended next step

Design the re-scoped brief **with the operator** (money-path — not auto-locked), settling the two open calls in §4, then hand Code one bounded brief covering edits 1–3 (+4 as park-interim) all landing together, with the F2 contract change and a **SQLite-path** regression test (both "NULL/pending live bet is swept" and "a lay settles to the correct inverted state"). Re-prove against the repro lay before the worker goes back on. B2 stays paused until then.
