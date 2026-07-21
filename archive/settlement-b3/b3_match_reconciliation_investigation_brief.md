# B3 — Lay-settlement money-path investigation (Code commission)

**Session:** S225 (governance side). Commissioned for a Claude Code **investigation** session in `bethub-v3`.
**Type:** **Read-only INVESTIGATION.** No code change, no test change, no design locked, no flag flipped, no DB/Betfair write, no git write ops. Output is an investigation **report**, not a fix and not a design.
**Codebase:** bethub-v3 @ HEAD `e2638fa` (byte-identical; a pre-existing dirty tree — the in-progress settlement-worker build — is present and **off-limits**; read it, don't touch it).
**Anchor:** 2026-07-05 ACST (DR-021).
**Governing DRs:** DR-032/033 (Betfair settlement spine / data-source roles), DR-030 (module boundaries), DR-027/028 (two-DB boundary), DR-019 (derived state on read), DR-021 (Adelaide anchors).

---

## Why this exists — and why it's an investigation, not a fix

**The live symptom (S224, real money).** A Betfair LAY was placed **unmatched**, then matched on Betfair. The operational store never updated its matched stake, so when the settlement worker later settled the bet it settled with the **correct result direction but $0 money** (`matched_stake=0`). This blocks cutover **B2** from being called fully money-proven — a bet that fills *after* placement can silently mis-value.

**Why we are NOT going straight to a fix.** The governance session first drafted this as a one-line "just wire the already-built `run_reconciliation_pass` worker" brief. A read-only verification pass against the real code **falsified that premise** (leads below). The true picture is a multi-part money-path correctness problem touching bet placement, match reconciliation, AND settlement ordering — not a missing worker. We have learned repeatedly that these fixes are never as simple as they first look (cf. the S222 settlement-correctness investigation → design → fix chain, where a "one-line nullfix" became a proper design). **So this commission is a detailed, adversarial investigation to establish the true root cause(s) and full blast radius first.** Design and fix are separate, later steps, gated on this report.

---

## Starting evidence — LEADS, not conclusions (verify every one first-hand)

A governance-side verification surfaced the following against HEAD `e2638fa`. **Treat these as leads to re-ground and challenge, not as settled facts.** Where a lead is wrong or incomplete, say so — that's the point of the investigation.

- **L1 — the offending bet may never enter the reconciliation sweep.** The live lay entry `place_lay` (`ui/api/routers/racing.py:~1105-1109`) appears to write an unmatched/partially-matched lay **directly and terminally** as `MatchStatus.FINAL_PARTIAL` (only a fully-matched lay → `FINAL_FULL`), with `matched_stake` = the (possibly 0) matched size at placement, and never revisits it. But `run_reconciliation_pass` (`workflows/bet_entry/v1/reconciliation.py:~417`) sweeps **only** `PROVISIONAL` / `PROVISIONAL_PENDING`. If both hold, a post-fill lay is invisible to reconciliation from placement — so wiring the worker unmodified would do nothing for this bug. **Verify the exact status an unmatched lay gets, and whether reconciliation would ever sweep it.**
- **L2 — settlement may not wait for reconciliation.** `run_settlement_pass` appears to select unsettled bets purely on `settlement_state="pending"` + event-start age, with **no match-status predicate** (`store/repositories/bets.py:~838-841`; `settlement.py` sweep). If so, the settlement worker and any reconciliation worker are two free-running threads with no ordering guarantee — settlement can settle a still-unreconciled bet at $0 before reconciliation lands. **Verify whether settlement is gated on match-status at all, and characterise the race.**
- **L3 — the resolver may trust the stale store stake.** Even once a bet IS swept, `_resolve_one` (`reconciliation.py:~150-377`) appears to recover the true matched size only when the bet is still visible in Betfair current orders (the in-orders branch). In the absent-from-orders path it appears to trust the record's stored `matched_stake` and can resolve a genuinely-matched-but-aged-out lay to **FAILED** (`reconciliation.py:~297-307, ~362-377`). If so, recovery is timing-dependent on Betfair's current-orders retention. **Verify what a matched-then-absent lay actually resolves to, and whether the true stake is ever re-read from Betfair in the absent path.**
- **L4 — what HELD (still verify, but these looked sound).** Money genuinely derives from `matched_stake`/`matched_price`/`settlement_state` on read (`workflows/balances/v1/balance_derivation.py`) — so correcting the stake corrects the money. `run_reconciliation_pass` is real, unit-tested, and its `BetfairAdapter` is satisfied by the composed `RealBetfairAdapter` (which, note, hard-requires a streaming-equipped client and takes client + audit_sink + operator_identity). `SQLiteBetRecordStorage` is concurrency-safe under two worker threads (fresh connection per call under a shared lock). The config pattern `reconciliation_worker: bool = True` binding `BETHUB_RECONCILIATION_WORKER` (with `=off` → False on the installed pydantic 2.13.3) is valid.

---

## Investigation mandate

Map the **true end-to-end money path for a Betfair lay** from placement → match state → settlement → derived P&L, and establish:

1. **Every entry path that creates a lay bet record** and the exact `MatchStatus` + `settlement_state` + `matched_stake` each writes at placement — not just `place_lay`. Are there other routes (orchestrator Trigger-A/B, manual entry, backfill)? Do any already leave bets mislabeled in the live store right now?
2. **The complete set of root causes** behind the $0-settle symptom (L1–L3 and anything they miss). Distinguish the *primary* root cause from contributing factors. Name the precise code locations.
3. **The full blast radius** of each candidate fix direction — WITHOUT implementing:
   - If an unmatched/partial lay is re-labeled `PROVISIONAL_PENDING` at placement: what else keys off `FINAL_PARTIAL` / `FINAL_FULL` for lays (balance derivation, UI, settlement eligibility, other sweeps)? What breaks or changes?
   - If reconciliation's swept statuses are broadened instead: what else is assumed about the `FINAL_*` states being terminal?
   - If settlement is gated on match-status (don't settle a not-yet-reconciled bet): does that hold bets forever in any real scenario? Interaction with the winner-less-hold / provisional logic already in `settlement.py`.
   - The resolver absent-path hardening (L3): what would it take to trust the live Betfair matched size over the stale store value, and what's the Betfair current-orders retention reality that determines whether it's even needed?
4. **The settlement ↔ reconciliation ordering** question: is a reconcile-before-settle guarantee needed, and what are the mechanism options (in-pass ordering; a match-status precondition on settlement; a single combined worker) — described, not chosen.
5. **The existing store state**: are the three S224 test bets (or any live bets) currently sitting in a mislabeled/mis-valued state that a future fix would need to backfill? (Read-only inspection of the operational DB, `mode=ro`.)

**Explicitly out of scope for this session:** writing any fix, locking any design, choosing between the options above, flipping any flag, or editing any file. Where you find a decision, *frame the options and trade-offs* for the operator + a later design pass — do not decide.

---

## Deliverable — `b3_lay_settlement_investigation_report.md`

Structured, evidence-anchored (file:line for every claim), adversarial (challenge L1–L4; note where the governance leads were wrong):

1. **Confirmed mechanics** — the real placement → match → settlement → P&L path for a lay, as the code actually does it.
2. **Root cause(s)** — primary + contributing, precisely located.
3. **Blast-radius map** — per candidate fix direction, what it touches and what it risks. Options framed, not chosen.
4. **Ordering / concurrency** — the settle-vs-reconcile interaction and the mechanism options.
5. **Current store state** — any already-mislabeled/mis-valued bets needing backfill.
6. **Open questions / unknowns / risks** — including anything the governance leads got wrong or missed.
7. **Recommended next step** — e.g. "ready for a design pass on approach X" or "needs live observation of a matched-then-absent lay first."

**Completion signal (required):** write the report to `bethub-rebuild/b3_lay_settlement_investigation_report.md`, and make its **final line exactly**:

```
<!-- INVESTIGATION COMPLETE -->
```

Write that sentinel only when the report is finished and saved — a governance-side watcher keys off it to trigger triage. Do not write it early or to any other file.

---

## Boundaries / disciplines (load-bearing)

- **Read-only.** No file edits, no test changes, no design locked, no flags flipped, **no git write ops** (no add/commit/stash/checkout/branch). HEAD stays `e2638fa`. The pre-existing dirty tree (settlement-worker build) is read-only context — do not touch or fold into it.
- **Bet-safety (Cat 4).** This is investigation only — it must not place, settle, reconcile, or move money, and must not start any worker. The settlement worker flag `BETHUB_SETTLEMENT_WORKER` stays OFF; do not run the app in a way that auto-settles.
- **capture.db / operational DB reads** — `mode=ro` only.
- **DR-030 boundaries / DR-021 anchors** respected in the report.
- **Adversarial posture.** Assume the simple story is wrong until the code proves it. The governance leads (L1–L4) are a starting map, not an answer key — challenge them.

---

## Ready-to-paste Code session prompt

> **Task (READ-ONLY INVESTIGATION — no code, no design, no fix):** Investigate the full money path for a Betfair LAY bet in this codebase (bethub-v3 @ HEAD `e2638fa`), from placement → match state → settlement → derived P&L, and produce an investigation report. Do NOT edit any file, change any test, lock any design, flip any flag, or run any git write op. The pre-existing dirty tree is read-only context.
>
> **Symptom (real, live):** a lay placed UNMATCHED then matched on Betfair settled with the correct result but **$0 money** — the store's `matched_stake` stayed 0. We need the true root cause(s) and full blast radius before designing a fix. These fixes are never as simple as they look — be adversarial.
>
> **Leads to VERIFY first-hand and challenge (not conclusions):** (L1) `place_lay` in `ui/api/routers/racing.py:~1105-1109` may write an unmatched lay terminally as `MatchStatus.FINAL_PARTIAL`, but `run_reconciliation_pass` (`workflows/bet_entry/v1/reconciliation.py:~417`) only sweeps `PROVISIONAL`/`PROVISIONAL_PENDING` — so the bet may never be reconciled. (L2) settlement (`run_settlement_pass` / `store/repositories/bets.py:~838`) may select on `settlement_state="pending"` with no match-status gate, racing any reconciliation worker. (L3) `_resolve_one`'s absent-from-orders path (`reconciliation.py:~297-377`) may trust the stale stored `matched_stake` and mis-resolve a matched-then-absent lay to FAILED. Confirm, refute, or extend each.
>
> **Establish:** every lay-creating entry path and the status/stake it writes; the complete root-cause set (primary vs contributing); the blast radius of each candidate fix direction (re-label placement status / broaden reconciliation sweep / gate settlement on match-status / harden the resolver absent-path) WITHOUT implementing; the settle-vs-reconcile ordering question and its mechanism options; and whether any bets currently in the operational store (`mode=ro`) are already mislabeled/mis-valued and would need backfill.
>
> **Deliverable:** `b3_lay_settlement_investigation_report.md` — confirmed mechanics; root cause(s); blast-radius map (options framed, not chosen); ordering/concurrency; current store state; open questions/risks; recommended next step. Every claim anchored file:line. Frame decisions for the operator — do not make them. **When the report is finished and saved, make its final line exactly `<!-- INVESTIGATION COMPLETE -->` (and nowhere else) — a watcher keys off it to trigger triage.**
>
> **Bet-safety:** investigation only — no place/settle/reconcile/money-move, no worker started, `BETHUB_SETTLEMENT_WORKER` stays OFF, DB reads `mode=ro`, DR-021 Adelaide anchors.

---

*This commission supersedes the earlier `b3_match_reconciliation_fix_brief.md` (whose "wire the pass unmodified" premise the verification falsified). No code touched; bethub-v3 byte-identical at `e2638fa`.*
