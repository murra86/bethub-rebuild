# B3 — adversarial verification of the built fix (Code commission, MAX effort)

**Session:** S225 governance → commissioned for a Claude Code **verification** session in `bethub-v3`, run at **maximum reasoning effort**.
**Type:** Adversarial verification. **Read + run-tests only** — no source edits, no fixes, no git write ops. Output is a verification report (findings, not repairs).
**Codebase:** bethub-v3 @ HEAD `e2638fa`, B3 built additively on the in-flight settlement-worker dirty tree.
**Grounds (read first):** `b3_lay_settlement_fix_report.md` (the build), `b3_lay_settlement_fix_design.md`, `b3_lay_settlement_investigation_report.md`.
**Governing DRs:** DR-032/033, DR-030, DR-027/028, DR-019, DR-021.

---

## 0. Prime directive — try to break it

This is the last gate before real money goes through the fix. **Assume the build is broken until you prove otherwise.** Do not re-bless the build report — attack it. A green suite and a confident report are not proof; find the scenario where a real lay settles with the wrong money, a bet strands forever, the worker moves money it shouldn't, or a report claim is false. If you find nothing after genuinely trying, say so with the evidence that earns that verdict. **Report findings; do not fix them** (fixing is a separate commission the operator decides on).

---

## 1. Provenance & suite (don't trust the report — reproduce it)

1. **Git integrity:** `git rev-parse HEAD` == `e2638fa`; `git status --porcelain` — confirm no commits/stashes; confirm the working-tree file set matches the build report's §5 manifest (nothing extra, nothing missing).
2. **Run the suite yourself:** `uv run pytest` — confirm **1327 passed / 1 xfailed** (report claims +38 over 1289). If the count differs, that's a finding. Note every skip/xfail and confirm none masks a real failure.
3. **Run the B3 suites in isolation** and read their output: `test_racing.py`, `test_reconciliation_worker.py`, `test_cleared_orders.py`, `test_betfair_adapter.py`, `test_reconciliation.py`, `test_settlement.py`, `test_bets.py`.

## 2. Test-quality audit (green ≠ correct)

For each new/changed test, judge whether it would actually **catch a regression** or passes vacuously. Specifically:
- Do the P1 tests assert the *exact* status (`PROVISIONAL_PENDING`) for unmatched **and** partial, not just "not FINAL_FULL"?
- Does the coupled `gate→reconcile→settle` integration test prove **true-stake** settlement (a concrete non-zero amount), or only that it doesn't crash?
- Are any pre-existing assertions **weakened** vs HEAD to make room for P1/P4? Diff every changed test against its dirty-tree/HEAD version and justify each altered assertion. A silently loosened assertion is a finding.
- Try a **mutation probe** on the riskiest lines (e.g. flip P4's `NOT IN` to `IN`, or P1's `>` to `>=`, mentally or in a scratch copy you do NOT save) — does a test fail? If a mutation survives, coverage is illusory.

## 3. Adversarial attack per part

- **P1 (re-label).** Find any consumer that assumes an unmatched/partial lay is `FINAL_PARTIAL` or terminal-at-placement — grep balance derivation, settlement, provisional/《bets》UI, cash/ledger, any invariant or state machine. Does surfacing these lays as `provisional_pending` change any money figure, list, or count that a user/operator sees? Does anything now double-count or mis-route them?
- **P2 (worker).** Prove reconciliation moves **no** money (writes only match fields + bookkeeping, never `settlement_state`, never places/settles). Check the on-in-live default + kill switch actually gate as claimed. Check the adapter's streaming-client requirement can't crash startup (fail-safe). Check two workers (reconciliation + settlement) over the shared `SQLiteBetRecordStorage` can't deadlock or interleave into a bad write.
- **P3 (cleared-orders).** Scrutinise the `listClearedOrders` assumption hardest — it is contract-verified, not live-verified. What does the adapter do if Betfair returns: a partial match (`sizeSettled` < original), multiple cleared rows for one bet, a `sizeSettled` of 0 with a real price, a missing field, a non-SETTLED status, an empty list, or a 500? Confirm every unexpected shape **falls through safely** to the existing Step 4-5 (never fabricates a stake, never mis-resolves to a wrong terminal). Confirm the JSON-RPC translation round-trips real Betfair field names.
- **P4 (gate + valve).** The core safety claim — **can any bet still be settled from a stale/unreconciled stake?** Enumerate the settle paths (`run_settlement_pass`, `run_provisional_resolution_pass`, any other caller of `list_unsettled_bets`) and confirm every one passes the exclusion. Can the park valve ever **auto-settle** instead of park (it must never)? Can a bet be **permanently stranded** (parked and never re-swept, or gated and never reconciled)? Confirm self-healing: a parked bet that later terminalises does settle. Confirm the threshold (`>=3 attempts` + event-started) can't fire on a healthy just-placed bet.

## 4. Coupling / race analysis

Walk the full lifecycle of a lay that matches *after* placement, across concurrent reconciliation + settlement worker ticks. Is there **any** interleaving where settlement reads `matched_stake=0` and settles before reconciliation has terminalised — despite the P4 gate? Is there any window where P1's `PROVISIONAL_PENDING` write and the settle pass race? State the ordering guarantee (or the hole).

## 5. Dirty-tree interaction

B3 is layered on the uncommitted settlement-worker chain. Confirm B3's additive edits don't silently depend on, or conflict with, the dirty changes in a way that would break if that chain is later revised — especially in `settlement.py`, `betfair_adapter.py`, `composition.py`, `main.py`. Flag any coupling the operator must know before committing either body of work.

## 6. Boundaries

**Read + run-tests only.** No source edits (a scratch mutation you discard is fine; never save it), **no git write ops**, `BETHUB_SETTLEMENT_WORKER` stays OFF, no worker started against live, no live Betfair call, no place/settle/money-move, operational-DB reads `mode=ro` only. HEAD stays `e2638fa`.

## 7. Deliverable — `b3_verification_report.md`

- **Verdict up top:** SOUND (cleared for supervised live-proof) / DEFECTS FOUND (with the worst severity).
- Provenance + suite reproduction result (your numbers, not the report's).
- Findings, severity-ranked (blocker / high / medium / low / nit), each with file:line evidence and a concrete failure scenario. Empty list if genuinely none.
- Test-quality verdict (any vacuous/weakened/mutation-surviving tests).
- The P3 live-confirm item restated (what the operator must watch).
- End the final line with the sentinel `<!-- B3 VERIFY COMPLETE -->`.

---

## Ready-to-paste Code session prompt (run at MAX effort)

> **Task (ADVERSARIAL VERIFICATION — read + run-tests only, no edits, no fixes, no git writes; run at max reasoning effort):** This is the last gate before real money flows through the B3 LAY money-path fix in bethub-v3 @ HEAD `e2638fa`. **Assume the build is broken until you prove otherwise — attack it, don't re-bless it.** Read `b3_lay_settlement_fix_report.md`, `b3_lay_settlement_fix_design.md`, `b3_lay_settlement_investigation_report.md` first.
>
> **Reproduce, don't trust:** confirm `git rev-parse HEAD == e2638fa` and no commits/stashes; confirm the working-tree file set matches the report §5 manifest; run `uv run pytest` yourself and confirm 1327 passed / 1 xfailed (+38) — a different count is a finding.
>
> **Test quality:** judge whether the new/changed tests would catch a regression or pass vacuously; diff every changed assertion vs HEAD/dirty and justify it (a silently weakened assertion is a finding); mentally/scratch-mutate the riskiest lines (P4 `NOT IN`→`IN`, P1 `>`→`>=`) and confirm a test dies.
>
> **Attack each part:** P1 — any consumer that assumes an unmatched lay is FINAL_PARTIAL / any money figure that changes when these surface as provisional_pending. P2 — prove reconciliation moves no money (match fields + bookkeeping only, never settlement_state), the gate/kill-switch work, the streaming requirement can't crash startup, two workers can't interleave badly on shared SQLite. P3 (hardest — listClearedOrders is contract-not-live-verified) — for partial/multi-row/zero-size/missing-field/non-SETTLED/empty/500 responses, confirm safe fall-through to Step 4-5, never a fabricated stake or wrong terminal; confirm JSON-RPC field names round-trip. P4 (core safety) — enumerate every caller of list_unsettled_bets and confirm all exclude PROVISIONAL*; confirm the valve can never auto-settle, can never permanently strand, self-heals, and can't fire on a healthy just-placed bet.
>
> **Race analysis:** find any concurrent reconcile+settle interleaving where settlement derives money from a stale matched_stake despite the P4 gate; state the ordering guarantee or the hole. **Dirty-tree:** flag any B3 coupling to the uncommitted settlement-worker chain the operator must know before committing.
>
> **Boundaries:** read + run-tests only; no edits/fixes/git-writes; BETHUB_SETTLEMENT_WORKER OFF; no live Betfair; no money-move; DB reads mode=ro; HEAD e2638fa. **Deliverable `b3_verification_report.md`:** verdict up top (SOUND / DEFECTS FOUND + worst severity), your suite numbers, severity-ranked findings with file:line + failure scenario (empty if none), test-quality verdict, the P3 live-confirm restated. End the final line with `<!-- B3 VERIFY COMPLETE -->`.

---

*Read-only commission — no code touched; bethub-v3 byte-identical at `e2638fa`.*
