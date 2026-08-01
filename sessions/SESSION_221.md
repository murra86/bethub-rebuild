# SESSION 221 — Settlement worker LIVE-PROVING started → first $5 test EXPOSED two money-path gaps (NULL sweep inert + LAY resolver inversion); placings FIX 1 verified working, 05:30 confirmed a bad provider window (24h health sweep launched)

**Opened:** 2026-07-02 14:56 ACST (manual) / re-opened via headless runner 2026-07-03 (cutover dot-point summary)
**Closed:** 2026-07-03 18:19 ACST
**Tool routing:** headless runner (open + cutover summary); Chat (placings run-check + health-sweep launch; operational housekeeping; drove the settlement live-proving first test; diagnosis + one-line brief; triaged Code's STOP report; close). Code ran a read-only pre-flight that refuted the brief. **No settlement/store/resolver code changed anywhere; bethub-v3 tree byte-identical at `e2638fa`.**
**Governing DRs:** DR-021 (Adelaide anchors), DR-032 (Betfair settlement spine), DR-033 (data-source roles), DR-030 (module boundaries), DR-027/028 (two-DB boundary).

---

## Anchor
- Open: runner 2026-07-03 (cutover summary saved); interactive continuation same day.
- Close: `TZ="Australia/Adelaide" date` → 2026-07-03 18:19 ACST.

## Session shape
A long, high-value session that turned the corner from planning to real live-proving — and the first live settlement test immediately exposed two genuine money-path gaps, caught read-only before any code changed. Also: placings FIX 1 got its first real-run signal, operational housekeeping cleared the slate, and the settlement worker was switched on live for the test then switched back off.

## What was delivered

1. **Cutover dot-point summary produced (headless).** The runner opened S221 and wrote the plain-language cutover runway (B1–B6, Strategy-1-parity scope) — the operator's quick-start.

2. **Placings FIX 1 — verified working, but 05:30 ACST confirmed a BAD provider window.** The 2026-07-03 05:34 run logged `deficit 36033→36033, placings=0, walled=6`. The metadata log shows **FIX 1 firing correctly** — each empty-runners meet retried 4× (backoff 2/2/4s) then flagged degraded (soft-wall, no strike) — but **0 of the retried meets recovered**: at 20:00 UTC the empty-runners degradation is **sustained, not transient**. So re-timing is now confirmed necessary. A read-only fetch-only probe at 22:59 UTC returned FULL runners on the walling dates (incl. 2026-03-21, 1540) — healthy windows exist. **Launched a detached 24h health-by-hour sweep** (`/tmp/health_sweep.sh` on the VPS, 9 rounds ×3h over 4 walling dates, read-only) — **completes ~08:30 ACST 2026-07-04**; log `/tmp/health_by_hour_sweep.log`.

3. **Operational housekeeping — clean slate for proving.** Via the tool's own endpoints (read-only inspect first, then API): (a) **archived the duplicate `BetFair` book** (`d2d2a2dd…`; soft-archive; the real `ef65cbdd…` with the account link untouched); (b) **hard-deleted all 5 June-25 test bets** (`DELETE /api/v1/bets/{id}`, each 200) — bet log now empty. Account "Tim", real BetFair, SportsBet all intact; mutation-log trail preserved.

4. **Settlement worker switched ON live + first test run.** Operator flipped `BETHUB_SETTLEMENT_WORKER=on` (verified on both live processes, mode=live). Placed a real **$5.26 Betfair LAY on "12. Gossamer Glow"** (Toowoomba R2, market `1.259636589`, sel `100232235`), logged via the race screen. Verified read-only: pending, fully Betfair-mapped. **First finding (cosmetic):** a stale amber "unmatched" warning persisted on the race page after the bet matched.

5. **The test EXPOSED the settlement gaps — worker never settled the bet.** After 15+ min (bet settled on Betfair), the worker never touched it (reconciliation_attempts 0, no market read, not parked). Diagnosed read-only: the worker sweeps `settlement_state="pending"` but logged bets are stored **NULL**. Drafted a one-line fix brief (`settlement_pending_sweep_nullfix_brief.md`).

6. **Code pre-flight REFUTED the brief — STOP & escalate (no code touched).** Read-only pre-flight found three blockers, each independently fatal:
   - **F1** — the one-liner is **inert live**: the worker's `SQLiteBetRecordStorage.list_unsettled_bets` (bets.py:823–862) is a bare `settlement_state IN (?)` with no `IS NULL` branch (the `has_null` logic I cited is in a *different* function). SQL-proven: `IN ('pending', NULL)` matches 0 NULL rows. A correct fix needs a **second edit in bets.py** — which the brief's §8 forbids. (In-memory store honors None → a unit-test-only regression would falsely pass.)
   - **F2** — an existing green test (`test_pass_sweeps_only_pending_bets`) **asserts NULL bets are NOT swept**, citing spec §2.6/§3.2 — a contract, not a missing test.
   - **F3 (gravest)** — the resolver `_resolve_settlement_for_bet` has **no LAY inversion** (WINNER→WON / LOSER→LOST, no `record.side` branch; `side` added later at W12.1). The repro bet is a **LAY**, so the worker would settle it to the **inverse** terminal state — a silent money-path error — even after fixing the sweep. Fixing it needs the resolver — also §8-forbidden.
   Code halted, wrote `settlement_pending_sweep_nullfix_report.md` (F1–F3 + SQL proof + read-only DB evidence + "what a correct fix requires"), changed nothing. Operator-confirmed the halt.

## Standing-instruction adherence check
- **DR-021** — open + close Adelaide-anchored. ✅
- **Cat 4 (bet-safety)** — the money-path stayed protected: the settlement worker was proven OFF at close; the broken one-liner was **stopped before any edit**; no settlement/store/resolver code touched; the two required fixes (store + resolver) flagged to **land together** so a half-fix can't mis-settle live. Housekeeping used the tool's own endpoints; capture reads read-only. ✅
- **S178 (ground "already-built" premises) — VIOLATED by the brief, caught by Code.** The one-line brief asserted the store "already handles NULL" without verifying which function the worker calls — F1. Recorded as the lesson: even a "one-liner" money-path brief must trace the exact live call path. ✅ (caught before harm)
- **S189 (green tests ≠ done)** — vindicated: the settlement build triaged "clean" S218 on fixtures that never exercised a LAY; live-proving surfaced F3. The S218 "clean" verdict is **caveated** accordingly.
- **First-action gate (S200)** — S222 first action recommended + set: the settlement-correctness re-scope investigation (below).
- No standing-instruction edits → no Cat-2 sweep.

## Open items
Pointer-only — full list in `current_state.md`.

**New / changed in S221:**
- **Settlement B2 BLOCKED** on a re-scoped correctness fix (pending-state model + LAY resolver inversion — must ship together). Worker **OFF**. One-line brief **SUPERSEDED**. S218 "clean" **caveated**.
- **Placings FIX 1 verified working**; 05:30/20:00-UTC confirmed a sustained bad provider window; **health-by-hour sweep running** (ready ~08:30 ACST 2026-07-04) → re-timing.
- Clean operational slate (dup book archived, test bets cleared).
- Finding: stale amber "unmatched" warning (cosmetic UI).

**Closed in S221:**
- Cutover dot-point summary; placings run-check + sweep launch; housekeeping; the settlement live-proving first test (found the gaps); one-line brief → Code STOP triage. ✅

**Carried to S222:**
- **Settlement-correctness re-scope investigation** (first action — read-only): why logged bets are NULL (create-path vs never-run reconciliation), the intended lifecycle, and what a correct fix covers (pending-state + LAY side-awareness + P&L consumption) → grounds a re-scoped brief designed with the operator.
- **Placings health-by-hour sweep map** (companion, ready ~08:30 ACST 2026-07-04) → commission run re-timing (weigh 2–3 healthy windows/day).
- Cutover runway B1/B3/B4/B5/B6; promo-seed; re-confirm interim pieces.

## Session close state
Root clean; STOP report + health-sweep artefacts present; no phantom files. `.close_out_backups/` swept to the S222 prompt only. `current_state.md` rotated; `v3_build_picture.md` header updated; the one-line brief marked SUPERSEDED. **Bet-safety CLEAN** — settlement worker OFF, no code touched anywhere, bethub-v3 byte-identical at `e2638fa`; v2 untouched. The racing-data-capture VPS carries the S219 FIX 1 change + the running throwaway health sweep (read-only). App currently stopped (operator relaunches worker-OFF when they want the tool).

## Forward routing
**Confirmed with operator.** S222 first action = **read-only settlement-correctness re-scope investigation** (the NULL/pending lifecycle + LAY-settlement design requirements → findings that ground a properly-scoped brief). Companion (time-gated ~08:30 ACST 2026-07-04): read the placings health-by-hour sweep map and commission the run re-timing. Settlement B2 stays paused on the re-scoped fix; the worker stays OFF until both the store and resolver fixes land together.
