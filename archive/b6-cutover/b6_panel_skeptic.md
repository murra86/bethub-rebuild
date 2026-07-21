# B6 panel — SKEPTIC seat output

**Seat:** Skeptic — Grok (fresh chat), per `b6_gonogo_panel_pack.md` §2/§4.1.
**Run:** 2026-07-06 (Session 230), operator-run, response filed verbatim below.

---

Overall Verdict: GO-WITH-CONDITIONS
Confidence: 65/100
The money path has meaningful real-money evidence for the narrow lay-only Safety Net workflow, but the proof chain is thin, the sample is tiny, cutover mechanics are completely unstarted, and many edge/residual behaviors remain unexercised at scale or under realistic daily operation. The team's optimism treats limited observed successes as systemic proof; a skeptic sees a promising prototype that needs tighter gating before it becomes the daily driver.

Q1: Is the money path proven enough to cut over? If no, what observable events would change your answer?

No. The live proofs (D3) demonstrate that in the specific observed sessions, a handful of small-stake lay bets were placed, matched (or not), reconciled with correct Betfair data, and settled with correct derived money (one -$4.91 loss; rest $0) without fabrication or overpay. They also showed the safety valve working (parking under uncertainty).
This is far short of proving the class of all expected daily operation. Six bets over two days, all minimal stakes, all AU win markets, all single-leg lays, does not establish robustness across:

- Volume (dozens of bets/day across 10-15 accounts).
- Diversity (different market types, partial matches, varying Betfair quirks, race/day types).
- Sustained operation (multi-day, with worker restarts, network events, concurrent activity).

Observable events that would change my answer:

- 30–50+ additional live lays (varied stakes/markets) with full auto-reconciliation + settlement across at least 5–7 race days, including at least one high-volume day, with the daily money check (D4) run and signed off each day.
- Explicit live triggering and verification of the refusal-path interlock (placement blocked on dead stream) and the partial-match-then-lapse guard.
- Successful full-day tunnel + worker operation under the launcher with the fault banner and durable logs visibly working.
- Independent adversarial review (or operator-supervised stress) of in-flight bet handling at flip time.

Until then, the proof is encouraging but anecdotal for the narrow observed cases.

Q2: Which named residuals should gate the flip? Which are correctly parked?

Gating (must be closed or tightly mitigated before flip):

- All items in the honest-classification ledger (D5) that touch money-path or day-one operation: especially the placement interlock refusal path (c), tunnel ride-along under full daily load (b), durable logs + fault banner live confirmation (a), and partial-match-lapse guard observation (e). These are not cosmetic.
- B6 cutover mechanics entirely (explicitly not started).
- r11 launcher worker-enablement visibility (invisible launch condition that already caused a supervised mistake).

Correctly parked (money-harmless or explicitly out-of-scope for cutover):

- r1 (stale matched-stake column), r2 (unwired function), r4 (display quirks), r8, r9, r10 (logging/ops discipline items).
- r3, r5, r6, r7 (cost/noise/edge tunnel behaviors that resolve at cutover or are bounded).

The team has done a reasonable job naming residuals, but the skeptic notes that several "parked" display/ops items become more material once v3 is the daily tool.

Q3: What must exist in v3 on day one (fresh start, no history migration)?

- Complete, verified promo catalogue seeding with operator sign-off on EV accuracy (B4 notes this is still pending).
- All accounts/books reference data reviewed for completeness against a real day's workflow (D7 explicitly notes this has not been done).
- Launcher that reliably starts tunnel + required workers with visible confirmation of which workers are enabled (addressing r11).
- Durable logs and placement-audit journal active from first launch.
- Daily money check runnable and documented procedure for operator use.
- Clear in-tool indicators for v3 vs v2 (to avoid operator confusion during coexistence).
- Documented handling (even if manual) for any in-flight unmatched bets at flip moment (D7 notes this is missing).

No history migration is fine per locked decision, but the fresh start still needs enough seed data and day-one observability to be usable immediately.

Q4: What should the v2/v3 coexistence + rollback window look like?

At minimum a multi-day parallel window (not a hard flip), with:

- v2 kept fully functional and untouched as the explicit rollback target.
- v3 used for new Safety Net bets while v2 continues to handle any ongoing/settling bets from prior days (explicit procedure for in-flight bets).
- Tunnel management: retire v2 supervisor only after confirming v3 owns the port stably for a full day (D4/B5).
- Daily side-by-side money check: run the v3 daily check and manually verify key outcomes against v2's view and Betfair statements.
- Rollback trigger: any money discrepancy, unresolvable park that v2 would have handled, worker stall >15–30 min, or operator discomfort. Rollback should be one-command or documented script to drop back to v2 + re-enable its supervisor.
- Minimum 3–5 full race days of successful parallel before declaring v3 primary.

The current "v2 keeps running until flip completes" is too vague; it needs concrete success criteria and rollback mechanics (B6).

Q5: What would you check that the dossier doesn't mention?

- Concurrency and race conditions: Multiple simultaneous placements, reconciliations, settlements, or operator actions on the shared SQLite store. The proofs were sequential/supervised.
- Error handling under realistic load: What happens on Betfair rate limits, API timeouts, partial API responses, or VPS connectivity flaps during a busy race day? The interlock and watchdog are lightly tested.
- State consistency at worker restarts or crashes: Especially around pending bets and the reconciliation sweep.
- Operator workflow completeness: Full end-to-end day in the UI (promo selection → placement → monitoring → settlement review) with real-time feedback. The proofs focused on backend workers.
- Auditability of derive-on-read money: Independent spot-check that the ledger + logs allow full reconstruction of any day's P&L without relying on in-memory state.
- Scale to 10–15 accounts: Promo visibility, account rotation, and performance under normal daily use (not just 6 bets).

The framing itself is somewhat wrong. The question isn't solely "is the money path proven?" (it has narrow positive signals) but "is the whole daily driver ready to replace v2 without increasing operational risk or manual overhead?" On that broader (and more relevant) question, v3 is not yet there—cutover mechanics, day-one completeness, and sustained-operation evidence are missing or thin.

Recommendation summary: Do not cut over yet. Address the gating items from Q2, run the expanded live proving and parallel operation from Q1/Q4, then re-convene. The team has built a solid foundation; rushing the flip now would be the classic "it worked in the lab" failure mode.
