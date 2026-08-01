# SESSION 219 — Placings root-cause review TRIAGED → FIX 1 deployed; V3 cutover-readiness map BUILT; cutover scope locked to Strategy-1 parity

**Opened:** 2026-07-02 14:56 ACST (manual open; first action was guarded/HELD — Code's review not yet present)
**Closed:** 2026-07-02 17:03 ACST
**Tool routing:** Chat (triage of Code's placings-recovery review + FIX 1 report; cutover-map build [read-only grounding in the S189 audit + interim reports]; scope decision; close). Code ran the read-only Plan-Mode review + deployed FIX 1 out-of-session. No code touched in Chat; no VPS writes from Chat; settlement flag NOT flipped.
**Governing DRs:** DR-021 (Adelaide anchors), DR-033 (data-source roles — placings analytical, settlement Betfair-only), DR-032 (Betfair settlement spine), DR-027/028 (two-DB boundary), DR-030 (module boundaries).

---

## Anchor
- Open: 2026-07-02 14:56 ACST (manual; guarded first action HELD — no review report present at open).
- Close: `TZ="Australia/Adelaide" date` → 2026-07-02 17:03 ACST.

## Pre-flight / pre-close checks
Root clean; no v2 phantom files. Drift-check on the S218 close was clean at open (current_state / SESSION_218 / v3_build_picture all stamped 2026-07-02 13:50 ACST). New artefacts landed this session: `placings_recovery_rootcause_review.md` (Code) and `cutover_readiness_map.md` (Chat). `.close_out_backups/` held only the S219 prompt at open.

## Session shape
Opened holding (Code's placings-recovery review not yet run). Operator then ran the widest-scope Claude Code Plan-Mode review out-of-session; it returned with the review + a request to commence FIX 1. Triaged the review, authorised FIX 1 only (bounded), triaged Code's FIX 1 report, then pivoted to cutover: built the v3 cutover-readiness map and locked the cutover scope to Strategy-1 parity.

## What was delivered

1. **Placings-recovery root-cause review TRIAGED — the prior frame was overturned.** Code's multi-agent read-only review **refuted the write-contention theory** (S212–S218) with a decisive fact: the nightly run walls at 05:30 ACST (20:00 UTC) *with the collector provably asleep* (0 `bookmaker_snapshots` rows in that window; collector not even started until 08:30 ACST). Real root cause, three layers: **(a)** provider-side (Racing API) intermittent **empty-runners** degradation — HTTP 200 with races present but every `runners[]` empty (Heroku origin, not cached, complete body, no error field); recovers on plain re-fetch; worse around 20:00 UTC. **(b)** the **2026-06-25** `get_unsynced_dates` change (oldest-first→recent-first, 14-day window) turned intermittent flakiness into a persistent nightly wall — recent-first leads with the freshest dates the provider is still churning (most empty-prone). **(c)** the fatal amplifier — **empty-runners is the one mode with no retry** (`_fetch_meet_races` retried only empty-races-list; the detector's return value was discarded), and partial dates passed as "complete," stranding placings silently.

2. **Several S218 findings corrected (owned).** The review corrected my S218 verification report: collector load ~284 rows/min peak (not "~15k/min"); no two-speed drain (the entire 36,033 deficit is >14d old, so 0% drains via the recent sync — and the recent pass was *manufacturing* ~230/day new deficit); the re-timing candidate was a no-op (the run already fires in the window I'd have moved it to). Deficit numbers confirmed: 36,033 across 92 dates, exhausted=0, 100% proven recoverable.

3. **FIX 1 authorised (bounded), deployed, verified.** Authorised only the ~15-line empty-runners detect+re-fetch (mechanism-independent cure), explicitly fencing out re-timing/ordering/provider-escalation/hygiene. Code deployed it to `subscription/racing_api.py` `_fetch_meet_races` (uses the detector's True/False; ≥2s backoff + re-fetch via the existing loop; `degraded=True` after 4 persistent-empty attempts → `sync_day` soft-walls → retried next night, no strike/stranding). Deployment verified (sha256 round-trip, py_compile/import OK, pre-edit backup at /tmp). **No test suite exists in racing-data-capture** (new operational fact) — Code substituted py_compile + import smoke + a 5-scenario behavioural test (all pass, incl. regression on the empty-races-list path). Scope adherence clean. **Status: deployed but NOT yet live-proven** — first real signal is tomorrow's (2026-07-03) 05:30 ACST run.

4. **V3 cutover-readiness map BUILT (`cutover_readiness_map.md`).** Operator-approved criteria (needed-to-run-the-day / proven-vs-built / money-path / day-one-state / fall-back). Grounded in the S189 workflow-integration audit backbone + two deltas: settlement worker now **built-unproven** (was not-wired); **Log Past Bet now live-proven** (re-plumbed to the 8400 tunnel + S209 live-proof — an S189 "blocker" already cleared). Six ranked cutover blockers: **B1** lay placement (money-path, highest stakes), **B2** auto-settlement live-proving (money-path, operator-actionable now — cheapest), **B3** store-write live-proving (cheap cluster), **B4** promo-seed (data gap), **B5** tunnel auto-start/health for Log Past Bet, **B6** cutover mechanics + day-one state + fall-back (W16). Non-blockers (operator-manual steps, analytics, placings backfill, F8) explicitly fenced off.

5. **Cutover scope LOCKED — Strategy-1 parity is enough.** Operator confirmed: Strategy 1 (Safety Net insurance + free-bet conversion) working in v3 is sufficient to flip off v2. Strategy 2 (Price Booster) is NOT a cutover blocker — it stays in v2/elsewhere during coexistence and is mapped into v3 post-cutover; Strategy 3/4 out. **Consequence: the Scope-A cutover map IS the whole cutover scope — no hidden Strategy-2 workstream behind the flip.**

## Standing-instruction adherence check
- **DR-021** — open (14:56) + close (17:03) Adelaide-anchored. ✅
- **Cat 4 (bet-safety)** — all Chat work read-only/governance; FIX 1 authorised as a bounded capture-side (analytical, DR-033) change executed by Code; no Betfair/settlement/money/live path touched in Chat; settlement flag NOT flipped; capture.db reads `mode=ro`. bethub-v3 not touched in Chat. ✅
- **Cat 5 (division of labour)** — the review's worth-it call and the cutover-scope decision kept as operator calls; FIX 1 scope fenced by explicit instruction, not left open. ✅
- **S189 taxonomy / classify-by-live-integration** — applied throughout the cutover map; FIX 1 classified deployed-not-live-proven, not "done." Empirical-verification discipline caught the stale S189 Log Past Bet status (re-checked the S209 report rather than trusting it). ✅
- **First-action gate (S200, hard)** — S220 first action confirmed with operator: **draft the settlement live-proving plan** (governance drafting, self-contained). ✅
- No standing-instruction edits → no Cat-2 sweep.

## Open items
Pointer-only — full list in `current_state.md`.

**New / changed in S219:**
- Placings root-cause **reframed** (provider-side empty-runners + no-retry gap; write-contention refuted). FIX 1 **deployed, not yet live-proven** — first signal = 2026-07-03 05:30 ACST run.
- **Cutover-readiness map built**; six ranked blockers (B1–B6). Cutover scope **locked to Strategy-1 parity**.
- S218 backfill report partly **superseded** by the review (collector-load + two-speed-drain framing corrected) — needs a correction pointer.

**Closed in S219:**
- Placings-recovery review triage + FIX 1 authorisation + FIX 1 report triage. ✅
- Cutover-scope decision (Strategy-1 parity). ✅

**Carried to S220:**
- **Draft the settlement live-proving plan** (first action, self-contained governance drafting — NOT a live action; does not flip the flag).
- **Placings 05:30 run-check** (companion, time-gated to 2026-07-03 ~05:30 ACST): read the run's outcome; if it still walls, commission the fetch-only health-by-hour sweep to pick a re-time window; if it drains, monitor.
- Cutover runway B1–B6 (settlement live-proving is the recommended first execution item).
- Promo-seed; W16 cutover mechanics; re-confirm interim-worked pieces (cash/lay prefill, non-migrated vps_client surfaces, by-market route).

## Session close state
Root clean (`cutover_readiness_map.md` + `placings_recovery_rootcause_review.md` present; no phantom files). `.close_out_backups/` swept to the S220 prompt only. `current_state.md` rotated; `v3_build_picture.md` header updated. `standing_instructions.md` untouched. No code touched in Chat; **bet-safety CLEAN** (read-only/governance; settlement flag not flipped; FIX 1 was a bounded capture-side change executed by Code). bethub-v3 untouched in Chat; the racing-data-capture VPS repo carries the one-file FIX 1 change (Code, verified).

## Forward routing
**Confirmed with operator.** S220 first action = **draft the settlement live-proving plan** (a governance/checklist document: preconditions, the flag-flip, what to watch — esp. the §5.1b park decisions — success criteria to declare live-proven, and rollback). Self-contained; does NOT flip the flag or touch settlement code. Companion (time-gated): check the 2026-07-03 05:30 ACST placings run and, if it still walls, commission the fetch-only health-by-hour sweep; else monitor. Then the cutover runway proceeds B2→B3→B1→B4→B5→B6.
