# Report — settlement PENDING NULL-sweep fix: **STOPPED before edit, escalated**

**Session type:** Surgical fix session — **halted at pre-flight, no code changed.**
**Brief:** `settlement_pending_sweep_nullfix_brief.md` (LOCKED, S221).
**Codebase:** bethub-v3 @ HEAD `e2638fa` (dirty tree — see §6).
**Date:** 2026-07-03 ACST.
**Outcome:** The brief's one-line fix was **not applied.** Pre-flight verification (read-only) found
the brief's premise is wrong (F1), that it collides with an existing green test's contract (F2), and —
gravest — that the resolver would **mis-settle the repro LAY bet to the inverse terminal state** (F3).
Each finding independently blocks the brief; each corrective action lies **outside §8's hard limits**.
Per the brief's own §3/§8 "stop and report — operator-Claude call," this session reports and stops.

---

## 0. TL;DR

- The briefed change — `settlement_states=(SettlementState.PENDING.value, None)` at `settlement.py:1026`
  — is **inert against the production store.** The live worker runs on `SQLiteBetRecordStorage`, whose
  `list_unsettled_bets` builds a bare `settlement_state IN (?)` with **no `IS NULL` branch**. In SQL,
  `IN ('pending', NULL)` matches **zero** NULL rows. The repro bet would **still never be swept.**
- The `has_null → IS NULL` machinery the brief relied on **exists, but in a different function**
  (`_bets_filter_sql`, behind `list_bets`/`count_bets`), which `list_unsettled_bets` does not call.
- Making the fix actually work needs a **second edit in `store/repositories/bets.py`** — which **§8
  forbids** ("Edit any file beyond `settlement.py` and its test file").
- Independently, `_resolve_settlement_for_bet` has **no LAY/BACK awareness**. The repro bet is a **LAY**.
  So even after the sweep is fixed, the worker would settle it to the **wrong** won/lost state — a
  silent money-path error. Fixing that means touching the resolver, which **§8 also forbids**.
- **No code, no test, no git write op was performed.** Recommendation: leave the worker flag **off**
  (it is inert regardless) and **re-scope** before any settlement code is written.

---

## 1. What the brief asked vs. what pre-flight found

The brief (§2–§3) diagnoses a single defect — the PENDING sweep queries only `settlement_state ==
"pending"`, missing freshly-logged NULL bets — and prescribes a one-line widen to
`(SettlementState.PENDING.value, None)`, asserting (§2) that the store "is already built to accept NULL
in this filter." The verification (§6) demands the repro LAY bet resolve to the **correct** terminal
state, not merely settle.

Pre-flight (three read-only Explore passes + direct code reads + a live `sqlite3` semantics proof +
read-only reads of the operational DB) confirmed the *symptom* (the NULL bet is never swept) but found
the brief's **mechanism claim is wrong** and surfaced a **second money-path defect** on the exact repro
bet. The details follow.

---

## 2. Findings

### F1 — The one-liner is INERT against the production store *(brief premise misattributed)*

**Brief §2 claim:** "`list_unsettled_bets`' WHERE-builder (`bets.py:~1403–1414`) handles `has_null` →
emits `settlement_state IS NULL`. The worker simply never passes `None`."

**Reality:**
- Lines `1403–1415` belong to **`_bets_filter_sql`** — a helper used **only** by `list_bets` (`:957`)
  and `count_bets` (`:1015`). `list_unsettled_bets` **does not call it.**
- The live worker composes **`SQLiteBetRecordStorage`** (`ui/api/settlement_worker.py`; its module
  docstring names `SQLiteBetRecordStorage` explicitly). Its `list_unsettled_bets`
  (`store/repositories/bets.py:823–862`) builds:
  ```python
  where = f"bets.settlement_state IN ({placeholders})"      # bets.py:838 — NO "IS NULL" branch
  ```
  and its `settlement_states` param is typed `tuple[str, ...]` (`:826`) — it does not type-accept `None`.
- **Live SQL proof** (run on `sqlite3 :memory:`, three rows: `'pending'`, `'settled_won'`, `NULL`):

  | Predicate | Rows matched |
  |---|---|
  | `s IN ('pending', NULL)` | **1** (`'pending'` only — the NULL row is **excluded**) |
  | `(s IN ('pending') OR s IS NULL)` | **2** (includes the NULL row) |
  | `s IS NULL` | 1 |

  SQL three-valued logic: `NULL IN (…)` never yields TRUE, so listing `NULL` inside `IN (…)` does
  nothing. **The brief's proposed `(PENDING.value, None)` emits `IN ('pending', NULL)` → still 0
  candidates for the NULL repro bet. The worker remains broken live.**

- **False-green trap.** The *in-memory* store (`bets.py:438–460`) filters via Python `set()` membership
  (`if row.settlement_state not in state_set` — `:448`), so `{"pending", None}` **does** contain a
  `None` row. A regression test written against the in-memory store (the default unit-test path) would
  therefore **PASS** on the one-line change alone — while production (SQLite) stays broken. The two
  Protocol implementations **disagree on NULL handling**; that divergence is itself a latent bug.

- **What a correct store fix requires** (out of scope, §8): add the `IS NULL` OR-branch to SQLite
  `list_unsettled_bets` (mirroring `_bets_filter_sql:1403–1415`) **and** widen its param type to
  `tuple[str | None, ...]`. That is a **second production file** (`store/repositories/bets.py`) —
  forbidden by §8.

### F2 — An existing green test asserts the OPPOSITE contract

`tests/workflows/bet_entry/v1/test_settlement.py::test_pass_sweeps_only_pending_bets` (`:607–639`)
explicitly asserts a `settlement_state=None` bet is **not** swept:
```python
no_state = _make_record(bet_id="no-state", settlement_state=None)
...
assert result.swept_count == 1
assert _read_record(storage, "no-state").settlement_state is None
```
with docstring *"Bets in non-PENDING settlement states (or None) are not swept. Only PENDING is the
pass-loop population per §2.6 §3.2."* The brief's requested regression test — proving NULL *is* swept —
directly **inverts** this. So the change is a **contract change** to a green test that cites a spec
(§2.6/§3.2), not "add a test while keeping the others green" (brief §6). The operator should reconcile
whether §2.6/§3.2 *intended* to exclude NULL, or predates the realization that the log path writes NULL.

### F3 — **GRAVEST:** resolver has no LAY inversion; the repro bet is a LAY → **inverted settlement**

`_resolve_settlement_for_bet` (`settlement.py:558–751`) settles on the Betfair runner's **objective**
status only:
- `RunnerSettlementStatus.WINNER → SETTLED_WON` (`:688–724`, via the dead-heat/reduction guard)
- `RunnerSettlementStatus.LOSER → SETTLED_LOST` (`:726–736`)

A grep of `settlement.py` for `\bside\b|LAY|BACK|BetSideTag` returns **only** unrelated prose
("read-side", "side-effect"); there is **no `record.side` branch anywhere.** `BetRecord.side` was added
later (W12.1); the W6.5-era resolver never consumes it.

**Operational-DB read (read-only, `mode=ro`)** — the sole bet in the book is the repro bet:

| field | value |
|---|---|
| `bet_id` | `bet-df31ffcd-c841-4593-a3bd-506f4dd41de2` |
| `settlement_state` | **NULL** |
| `side` | **LAY** |
| `matched_stake` / `matched_price` | 5.26 / 3.5 |
| leg market / selection | `1.259636589` / `100232235` "12. Gossamer Glow" |
| market name | `R2 1100m 3yo` (a **win** market) |
| event start | 2026-07-03T17:00:00+09:30 (past cutoff) |

State distribution across the whole DB: `<NULL> ×1`. Side distribution: `LAY ×1`. **The only bet the
worker has to settle is a NULL-state LAY** — so F1 and F3 both bite it directly.

By the brief's own §6 definition — *"SETTLED_WON if Gossamer Glow did NOT win, SETTLED_LOST if it
won"* — the resolver is **inverted** for this bet:
- If Gossamer Glow **won** → runner `WINNER` → resolver returns **SETTLED_WON**; correct-for-LAY is
  **SETTLED_LOST**.
- If Gossamer Glow **lost** → runner `LOSER` → resolver returns **SETTLED_LOST**; correct-for-LAY is
  **SETTLED_WON**.

Either way, on a clean result the worker would settle the repro LAY to the **inverse** of correct — a
silent money-path error, precisely the failure §6 ("correct, not just settled") and the live-proof
plan's money-path invariant ("never silently overpaid") exist to catch. Fixing it requires editing
`_resolve_settlement_for_bet` — **§8 explicitly forbids touching "the `_resolve_*` resolvers."**

> I did **not** perform a live Betfair read (no need, and out of a HALT session's scope), so I do not
> assert which way Gossamer Glow ran. The finding does not depend on it: the resolver returns the
> market-objective mapping, which for a LAY is the inverse of correct **whichever** way it went.
> One link not traced under read-only: how downstream P&L consumes `SETTLED_WON/LOST` for a LAY. But
> the brief's §6 is itself the bet-relative spec, and the resolver contradicts it. The dead-heat/Rule-4
> **park guard** (`:688–713`) is also oriented to a *backer's* payout reduction; its correctness for a
> LAY's liability is a further open design question, not just a sign flip.

---

## 3. Symmetry check (confirmed, unchanged — per brief §4)

- The **PROVISIONAL** pass `run_provisional_resolution_pass` sweeps
  `settlement_states=(SettlementState.PROVISIONAL.value,)` (`settlement.py:1289–1292`) with **no**
  `older_than_event_start` and would **not** be touched by the brief's change. PROVISIONAL bets are
  always explicitly stamped on transition — never NULL — so this pass correctly needs no NULL widen.
  **Confirmed; not changed** (nothing was changed at all).
- The two `list_unsettled_bets` call sites are the only ones (`:1025` PENDING, `:1289` PROVISIONAL);
  no other caller depends on the PENDING sweep excluding NULL.

---

## 4. Why the briefed scope cannot deliver a correct live result

A single, self-contained collision of the brief's §6 (correctness) with its §8 (hard limits):

| To make the repro bet settle **correctly** live, you must… | …but §8 forbids it |
|---|---|
| widen the sweep (`settlement.py:1026`) | ✅ in scope |
| add `IS NULL` to SQLite `list_unsettled_bets` (`bets.py`) so the sweep actually returns the NULL bet | ❌ "no file beyond settlement.py + its test" |
| make the resolver invert won/lost for `side == LAY` (`_resolve_settlement_for_bet`) | ❌ "the `_resolve_*` resolvers" |
| flip the existing `test_pass_sweeps_only_pending_bets` contract | ⚠️ in the test file, but changes a spec-citing green test |

The in-scope edit alone yields either a **still-broken** worker (F1) or, if the store were also fixed, a
**wrong** settlement (F3). There is no correct outcome reachable within §8 — which is exactly the
"stop and report" condition the brief anticipates.

---

## 5. What a correct fix actually requires (for the re-scoped brief)

Not executed here — recorded so the operator can re-scope. Suggested order:

1. **Decide the NULL-is-pending contract** (F2): confirm freshly-logged bets *should* be swept as
   pending, updating §2.6/§3.2 and `test_pass_sweeps_only_pending_bets` accordingly. (Alternative — the
   §5.4 create-path stamp — was rejected by the brief and does not fix the existing NULL bet.)
2. **Store fix (F1):** SQLite `list_unsettled_bets` gains the `IS NULL` OR-branch + type widen; reconcile
   the in-memory/SQLite divergence so both honor `None` identically. Add a store-level test that
   exercises the **SQLite** path (not just in-memory) so the false-green trap can't recur.
3. **Resolver fix (F3):** make settlement `side`-aware — invert won/lost for LAY — and design/validate
   what dead-heat & Rule-4 parking mean for a LAY's *liability* (not a backer's payout). This is the
   real money-path design work and deserves its own go-ahead, not a "surgical" pass.
4. **Sweep widen (`settlement.py:1026`)** + regression tests: NULL-state bet is swept **and** a LAY
   settles to the correct inverted state — both proven, and at least one exercising the SQLite store.
5. **Only then** re-run the S220 live-proof against the repro bet and confirm the actual Betfair result
   matches the resolved state, with the money-path invariant held.

---

## 6. Dirty-tree confirmation & self-assessment

- **HEAD:** `e2638fa`. **No git write op** was run (no add/commit/checkout/stash).
- The working tree is **byte-identical to session start** — same modified set (incl. the pre-existing
  `M workflows/bet_entry/v1/settlement.py` and `M tests/workflows/bet_entry/v1/test_settlement.py`) and
  same untracked set (incl. `?? ui/api/settlement_worker.py`). **I edited neither named anchor**, nor
  any other repo file. The only file written this session is **this report** (in the rebuild folder,
  outside the code repo).
- **No live Betfair read, no DB write, no schema change, no flag/launcher change** — all §8 respected.
- All read-only actions: 3 Explore agents; direct reads of `settlement.py`, `store/repositories/bets.py`,
  `tests/…/test_settlement.py`, `ui/api/settlement_worker.py`, `ui/api/config.py`; a `sqlite3 :memory:`
  semantics proof; and `mode=ro` reads of `data/bethub.db`.
- **Confidence:** F1 — certain (code + SQL proof + store-composition). F2 — certain (quoted test). F3 —
  high (resolver code + grep + DB-confirmed LAY); the sole untraced link is downstream LAY P&L, which
  does not change the §6-defined verdict.

## 7. Recommendation

1. **Leave `BETHUB_SETTLEMENT_WORKER` off** until a re-scoped fix lands (it is inert either way; the
   only real risk is turning it on *after* a store fix but *before* the resolver fix, which would settle
   the LAY wrongly — so the store and resolver fixes must land **together**).
2. **Re-scope** per §5 above (a new operator-authorized brief spanning `settlement.py` + `bets.py` +
   resolver + the test-contract change). The original one-line brief should be marked superseded.
3. Settlement live-proving (cutover **B2**) stays paused on the re-scoped fix, not this one.
