# B6 panel — STRUCTURING / PM seat output

**Seat:** Structuring / PM — Gemini (fresh chat), per `b6_gonogo_panel_pack.md` §2/§4.3.
**Run:** 2026-07-06 (Session 230), operator-run, response filed verbatim below.

---

## 1. Verdict & Panel Questions (Q1-Q5)

### Verdict

GO-WITH-CONDITIONS

The system's core architecture is money-safe by design, enforcing a failure-direction that drops unresolved anomalies into a manual review queue rather than guessing or fabricating financial magnitudes. However, proceeding to a blind cutover without resolving the hidden worker-enablement states, unverified bookmaker configurations, and the in-flight bet handoff would present unacceptable operational risk to day-one cash flows.

### Panel Questions

**Q1: Is the money path proven? What observable events would change your answer?**

Yes, within the limited scope of the executed live trials. The money path is proven for single-leg lay bets on Australian harness/thoroughbred WIN markets across real money outcomes (losses, lapses, and zero-money voids).

The following observable events would change this assessment or invalidate the proof:
- A partial-match-then-lapse event failing to route to the manual review queue and instead fabricating or guessing a settled stake.
- The cash-flow ledger reflecting non-zero money rows for a $0 no-bet lay during a settlement worker sweep (violating the derive-on-read architecture).
- The tool executing a placement while the live subscription stream is broken or disconnected (violating the placement interlock).
- Any occurrence of a BACK-bet being processed or settled by the tool, as this path is completely unproven live and out of scope.

**Q2: Which named residuals require mitigation before cutover, and which are correctly parked?**

Must Mitigate Before Cutover:
- **r11 (Launcher hides worker status / accidental OFF launch): Critical operational risk.** Since worker enablement relies on invisible environment flags and has already failed once during a supervised launch, an operator cannot verify if the automated reconciliation or settlement workers are actually running without manual process inspection.

Correctly Parked (Acceptable for Cutover):
- r1, r2, r3 (Money-adjacent): Stale columns, unwired constraints, and high read calls are bounded by the manual park valve or are completely unreachable; they do not compromise financial data integrity.
- r4 (Cosmetic display): Showing "$0 at $0" for unmatched pending positions is confusing but mathematically correct under the derive-on-read paradigm.
- r5, r6, r7, r8, r9 (Ops/Tunnel): v2's tunnel redialing ceases upon its retirement. Lack of web server logging, unrotated logs, and narrow tunnel disconnect windows are acceptable for a single-operator environment.
- r10 (Session discipline for daily check): Manageable via operational compliance rather than code.

**Q3: What must exist in v3 on day one?**

v3 must possess a fully seeded and validated promotion catalogue, manual environment flag overrides to explicitly force worker activation, clear visibility of running processes at launch, an operational connection over the SSH tunnel, and an empty manual review queue. Historical data migration is explicitly excluded.

**Q4: What should the coexistence window look like?**

The coexistence window must span one complete racing day (24 hours). During this window, v2 remains completely dormant but fully configured, ready to assume operational control within minutes. v3 executes all live traffic. The window terminates when a clean daily money check confirms zero manual queue blockages, zero silent losses, and precise financial reconciliation at the end of the day's racing schedule.

**Q5: What would you check that the dossier doesn't mention?**

- **Bookmaker Account Configurations:** The dossier confirms 9 rows in the promo catalogue but is silent on where or how the 10-15 bookmaker account credentials, API keys, session tokens, or login states are stored, encrypted, or verified for v3.
- **Bookmaker Bet Placement and Tracking:** The dossier exhaustively proves the Betfair lay leg of Strategy 1, but it is completely silent on whether a single bookmaker back bet has ever been executed, parsed, tracked, or recorded by v3's live store.
- **Mac Hardware/OS Compatibility:** The dossier notes v3 runs locally on the operator's Mac, but it does not establish if local dependencies, file permissions for the durable log directory, or local port availabilities have been verified outside of development.
- **Betfair Account Balance/Exposure Limits:** The dossier does not state how v3 monitors or handles exchange exposure limits or account balance deficiencies during an active racing session.

## 2. Day-One Checklist

This checklist identifies all environment states, reference data, and configurations required to execute a standard day of operations on v3.

| Item ID | Category | Description | Type | Verification Method |
|---|---|---|---|---|
| CL-01 | Reference Data | Promo Catalogue Verification: Complete eyeball verification by the operator of the 9 seeded promo rows to confirm expected value (EV) figure accuracy. | Seed-Once | Visual inspection of v3 promo-page picker. |
| CL-02 | Configuration | Bookmaker Identity Mapping: The active 10-15 bookmaker accounts must be registered or configured within v3's local store schema to allow bet tagging. | Seed-Once | Database query of bookmaker reference table. |
| CL-03 | Configuration | Environment Launch Flags: Explicit configuration profiles or scripts setting the environment flags that enable both the settlement and reconciliation workers. | Seed-Once | Inspection of launcher configuration file/script. |
| CL-04 | Environment | SSH Tunnel Path: B5 auto-start tunnel verified and connected to the remote analytics VPS. | Ongoing | App launcher health-gated watchdog reports "Healthy". |
| CL-05 | Environment | Betfair Live Stream Subscription: Active API connection to the exchange market data stream. | Ongoing | Placement interlock status reads "SUBSCRIBED". |
| CL-06 | Operational State | Clean State Baseline: The local v3 operational store must reflect zero active, pending, or unhandled historical bets. | Seed-Once | Daily money check utility returns zero records; manual queue is empty. |

## 3. Coexistence & Rollback Window

### Window Parameters

- **Length:** 24 Hours (One full Australian racing calendar day).
- **v2 State During Coexistence:** v2 remains fully operational on the operator's Mac but sits completely idle. Its automated tunnel-supervisor script must remain active until the formal cutover sign-off, but its betting interfaces must be closed to prevent accidental double-entry.

### Fallback Trigger Conditions

An immediate rollback to v2 will be executed if any of the following events occur:

1. **Reconciliation Stall:** The v3 reconciliation worker hangs or experiences an unhandled exception that cannot be cleared by an app restart within 15 minutes during live racing.
2. **Silent Loss/Data Mismatch:** The daily money check utility flags a discrepancy between Betfair's account balance changes and v3's derived-on-read calculations.
3. **Tunnel Deadlock:** The B5 watchdog fails to self-heal a disconnected or half-open SSH tunnel within 5 minutes, starving the system of race lookups.
4. **Worker Failure Masking:** The launcher drops an environment flag at startup, leaving a worker disabled without displaying an error banner (Residual r11 condition).

### Mechanical Rollback Procedures & The In-Flight Bet Problem

If a rollback condition is met mid-day, the operator will execute a mechanical fallback using the following sequence:

[Stop v3 App & Workers] ──> [Assess/Cancel Unmatched Exchange Bets via Web/App] ──> [Start v2 App & Supervisor] ──> [Manually Sync v3 Bets into v2]

1. **Terminate v3 Processes:** Force-kill the v3 launcher app and all child processes to release the physical VPS tunnel port.
2. **Mitigate In-Flight Exchange Bets:**
   - The Problem: Any live, unmatched exchange lay bets placed by v3 will be completely invisible to v2 upon launch because v3 operates on an empty database with no historical migration. v2 will have no record of these orders.
   - The Resolution: Before opening v2, the operator must log directly into the native Betfair web interface or mobile application. The operator must manually cancel all unmatched pending orders placed by v3 to eliminate exposure drift.
   - Any partially or fully matched lay bets must be identified on the exchange interface. The operator will write down their exact matched stakes and prices for manual ledger entry.
3. **Initiate v2 Recovery:** Launch BetHub v2. v2's tunnel supervisor will immediately claim the freed VPS tunnel port and re-establish lookups.
4. **Re-reconciliation of v3 Legacy Positions:** For any bets that were fully or partially matched on v3 prior to the fallback (which v2 has never seen), the operator must manage settlement manually outside of the software suite at the end of the day, using Betfair's native statements. v2 will only be used to drive new betting strategies for the remainder of the day.

## 4. Cutover Runbook

This sequence details the precise execution steps for Cutover Day.

1. **Pre-Flight Verification** (Coexistence Day minus 1 Hour): Execute the v3 daily money check tool to verify the log baseline. Ensure the manual review queue is entirely empty. Verify that the v3 application working directory is completely clean and matches the approved private repository commit.
2. **Quiesce v2 Traffic** (Cutover Minute 0): Close all active browser tabs or user interfaces interacting with BetHub v2. Ensure all bets placed via v2 on the current calendar day are fully settled and reconciled within the v2 SQLite database.
3. **Decommission v2 Automated Infrastructure** (Cutover Minute 5): Terminate the legacy v2 tunnel-supervisor script. This step is critical to resolve Residual r5 and prevent the script from continuously spamming the authentication logs every 5 seconds.
4. **Deploy v3 Runtime Fix** (Cutover Minute 10): Before launching, modify the v3 startup launcher script to echo the explicit status of all active environment flags (resolving Residual r11). The script must output text to the terminal confirming SETTLEMENT_WORKER=ON and RECONCILIATION_WORKER=ON before initializing the core application loop.
5. **Initialize v3 Environment** (Cutover Minute 15): Execute the modified v3 launcher script. Observe the terminal output to visually confirm worker enablement flags are active. Verify that the in-tool fault banner remains silent, confirming a successful connection to the live Betfair stream and the B5 SSH lookup tunnel.
6. **Execute Post-Flip Smoke Test** (Cutover Minute 20): Navigate to the promo-page picker interface. Select a non-gating test promotion from the 9 seeded rows. Confirm that race lookups pull accurately through the active tunnel without triggering the health watchdog. The system is now live on v3 under the Coexistence framework.
