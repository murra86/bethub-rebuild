> **⛔ SUPERSEDED (S221, 2026-07-03) — DO NOT EXECUTE.** Code's read-only pre-flight refuted this brief's premise: the one-liner is **inert** against the production SQLite store (F1), inverts an existing spec-citing test (F2), and — gravest — the resolver has **no LAY inversion**, so the repro LAY bet would settle to the **wrong** terminal state (F3). See `settlement_pending_sweep_nullfix_report.md` for the evidence. The correct fix spans settlement.py + bets.py + the resolver + a test-contract change, and is being re-scoped as a deliberate settlement-correctness brief (pending-state model + LAY settlement, landing together). Retained for the record only.

# Brief — settlement worker: PENDING sweep misses NULL-state bets (one-line fix)

**Type:** Surgical fix (read-write, one production line + a regression test). Single bounded Code session.
**Status:** LOCKED — drafted S221, 2026-07-03 ACST.
**Anchored on:** a live-proving finding (S221) — the settlement worker was switched on live (`BETHUB_SETTLEMENT_WORKER=on`, `BETHUB_BETFAIR_MODE=live`) and a real $5.26 Betfair LAY, settled on Betfair, was **never picked up** by the worker after 15+ minutes. Root cause traced read-only against the live code + operational DB (below).
**Bet-safety:** MONEY-PATH change — it makes the worker settle bets it currently ignores. The park-not-overpay guards are **not** touched; the change only widens which bets the sweep *sees*. Verification (§6) must confirm the repro bet settles to the **correct** terminal state, not merely that it settles.
**Codebase anchor:** bethub-v3 (Code confirms HEAD at session start; this brief cites current live-file line numbers, ±a few).

---

## §1 — What this is
A one-line fix to the auto-settlement worker's candidate query, plus a regression test. Code makes the named change, adds the test, runs the suite, re-proves against the repro bet, and returns one report. Single bounded session. No change to the guard/park logic, the data model, or the bet-write path.

## §2 — Root cause (traced, high confidence)
- The worker's PENDING sweep, `run_settlement_pass` (`workflows/bet_entry/v1/settlement.py`, ~L1027), calls:
  ```python
  candidate_rows = storage.list_unsettled_bets(
      settlement_states=(SettlementState.PENDING.value,),   # == ("pending",)
      older_than_event_start=cutoff,
      max_results=max_results,
  )
  ```
  → it selects only bets whose `settlement_state == "pending"`.
- **Freshly-logged bets are stored with `settlement_state = NULL`, not `"pending"`** (verified: the S221 repro bet and all prior test bets are NULL). So the sweep's `WHERE settlement_state IN ('pending')` never matches them → the worker never reads their market, never settles them, never parks them. They sit at NULL forever.
- This is **not** a stray edge case — every normally-logged bet is NULL, so **as-is the worker settles nothing that comes through the log path.** This is the blocker for settlement live-proving (cutover B2).
- The codebase's own convention already says NULL *is* pending: `store/repositories/bets.py:~1075` — *"the bet is still PENDING (`settlement_state` in {NULL, "pending"})"*. The sweep is the outlier that only honours the string form.
- The store is **already built to accept NULL** in this filter: `list_unsettled_bets`' WHERE-builder (`bets.py:~1403–1414`) handles `has_null` → emits `settlement_state IS NULL`. The worker simply never passes `None`.

## §3 — The fix (preferred: widen the sweep, §5.4 alternative rejected)
In `run_settlement_pass` (`settlement.py:~1027`), change the sweep to include the NULL form:
```python
settlement_states=(SettlementState.PENDING.value, None),
```
That makes the emitted SQL `(settlement_state IN ('pending') OR settlement_state IS NULL)` — aligning the worker with the documented {NULL, "pending"} convention, using machinery the store already supports. Nothing else in the pass changes.

**Do NOT take the alternative** (stamping `"pending"` onto bets at create time): it is a wider data-model change (the whole edit-fence and multiple read paths key off the {NULL,"pending"} pair), it doesn't fix existing NULL bets, and it carries more blast radius than this one-line query widen. If Code believes the create-path stamp is genuinely cleaner, it **stops and reports** rather than doing it — that's an operator-Claude call, not in scope here.

## §4 — Symmetry check (confirm, don't change)
- The **PROVISIONAL** pass (`run_provisional_resolution_pass`, sweep `settlement_states=("provisional",)`) does **not** need this change: PROVISIONAL bets are always explicitly stamped `"provisional"` on transition — never NULL. Confirm this in the report; do not touch it.
- Confirm no other caller relies on the PENDING sweep excluding NULL (it shouldn't — NULL bets are exactly what we want swept).

## §5 — Pre-reads (in order)
1. This brief.
2. `workflows/bet_entry/v1/settlement.py` — `run_settlement_pass` (the edit target) + the `_resolve_settlement_for_bet` guard chain (context; unchanged).
3. `store/repositories/bets.py` — `list_unsettled_bets` + its WHERE-builder (`has_null` handling); the {NULL,"pending"} convention comment (~L1075).
4. `settlement_liveproof_plan.md` (rebuild folder) — the proving criteria this unblocks.

## §6 — Verification (the important part — correct, not just settled)
**Repro bet (the live case):** `bet-df31ffcd-c841-4593-a3bd-506f4dd41de2` — LAY $5.26 @ 3.5, Betfair market `1.259636589`, selection `100232235` ("12. Gossamer Glow"), Toowoomba R2, event start 2026-07-03T17:00 ACST. **Settled on Betfair; `settlement_state` still NULL in our DB.** It is past the age cutoff, so it is eligible the moment the sweep sees NULL.

- **Before:** show the sweep returns 0 candidates for this bet (NULL excluded).
- **After the fix:** the sweep includes it; run one settlement pass (mock reader for the unit test; and a live/real read for the proof) and confirm:
  - The bet resolves to the **correct** terminal state read from Betfair — LAY logic: **SETTLED_WON if Gossamer Glow did NOT win**, **SETTLED_LOST if it won**, void if the market voided. State the actual Betfair result and that the resolved state matches it.
  - `last_read_market_state` is written and `reconciliation_attempts`/`last_reconciled_at` advance.
  - **No silent overpay / money-path invariant holds** — if the race carried a dead-heat or removed runner, confirm it **parked** (it should not have on a clean result).
- **Regression test (must add):** a unit test proving a **NULL-`settlement_state`** pending bet (past the cutoff, with a settleable Betfair leg) is swept and settled by `run_settlement_pass` — the guard that stops this bug returning. Keep the existing "clean winner → SETTLED_WON", park, and Option-B fallback tests green.
- Full suite: `uv run pytest` green, net-new test(s) counted, no regressions.

## §7 — Output spec
Single file `settlement_pending_sweep_nullfix_report.md` (rebuild folder root). Sections: (1) the one-line change with `git diff`; (2) before/after candidate-count for the repro bet; (3) the live re-prove — Betfair result + resolved state + confirmation they match + money-path invariant held; (4) the PROVISIONAL-pass symmetry confirmation; (5) test results (incl. the new NULL regression test); (6) self-assessment + dirty-tree confirmation. ~150–250 lines.

## §8 — Hard limits (non-negotiable)
Code does **not**:
- Touch the guard/park logic (§5.1 Option C / Option B), the `_resolve_*` resolvers, the §5.1b verification records, or the materiality threshold.
- Change the bet **create/log** path or the settlement-state data model (the create-path-stamp alternative is out of scope — report, don't do).
- Edit any file beyond `workflows/bet_entry/v1/settlement.py` and its test file.
- Flip `BETHUB_SETTLEMENT_WORKER` or touch the launcher/config; change schema; touch the placings/VPS/capture side.
- Run git write ops; escalate mid-session.

## §9 — After Code's session
Operator-Claude triages `settlement_pending_sweep_nullfix_report.md`. If the repro bet settled correctly and tests are green → the settlement worker is unblocked; resume the S220 live-proving plan (re-run the same $5 test end-to-end, then accumulate the five proof criteria via the read-only review passes). If Code hit the create-path question → operator decides the data-model direction before any further change.

## §10 — Cross-references
Governing DRs: DR-021 (Adelaide anchors), DR-032 (Betfair settlement spine), DR-030 (module boundaries). Prior artefacts: `settlement_liveproof_plan.md` (B2 proving), `settlement_worker_build_report.md` (the build this fixes a gap in), `cutover_readiness_map.md` (B2). Live finding: S221 first settlement test (this brief's repro).
