# B7 piece 2 — in-tool fault banner (worker + feed health) — build report (S229)

**Run:** 2026-07-06 (S229), Adelaide-anchored per DR-021. Third build of the session (after B5 tunnel + B7 piece 1).
**Outcome:** BUILT + tested (12 backend + 5 frontend tests; suites **1379** / **130** green; dist rebuilt; endpoint live-checked on a mock boot). Committed `59dfcf1`, pushed.
**Classification: implemented + mock-proven.** The live confirm is passive — banner is silent when healthy, so the real proof is the first live fault it catches (or a deliberate check during any live window: kill the Terminal's network and watch the lost-contact banner).
**Scope revision (operator call, S229):** the planned **phone/heartbeat alarm is replaced by this in-tool alert.** Operator's reasoning: a fault only matters while the tool is in use. Assessment concurred with one named caveat — an in-tool alert cannot report the app being dead *while unattended* — accepted because the money path degrades hold-not-overpay, next-launch catch-up sweeps are live-proven (S228/S229), and the daily review-pull (piece 3) catches quiet slippage. **Phone alarm PARKED, revisit at unattended running / ~30-account scale.**

---

## 1. What was built

- **Worker health registry** (`ui/api/worker_health.py`): both periodic workers (settlement, reconciliation) now report start/stop, every completed cycle, every errored cycle. Previously fire-and-forget loops with zero observable state — a dead worker was indistinguishable from a healthy one. Staleness = no completed pass within **3× the worker's interval** (monotonic clock, immune to wall-clock changes; sleep-then-run first-pass grace covered). Erroring = most recent attempt failed; clears on the next clean pass (error text retained for display). Thread-safe (cycles run off-loop).
- **`GET /api/health/workers`** (health router): computed snapshot per worker + streaming connection state + overall `healthy`. Design calls: never-started workers are **absent** (workers OFF by design must not raise alarms); a missing/broken streaming client degrades to `null`/`UNAVAILABLE` — the health probe can never 500.
- **`HealthBanner`** (frontend, mounted above every route): polls every 20s; invisible while healthy. Plain-words red banner on: worker stopped doing its rounds (with "last pass N min ago"), worker hitting errors (with the error text), live price feed not connected, and **lost contact with BetHub** after two consecutive failed polls (one blip is not a fault) — that last one covers the backend dying while the operator has the screen open.

## 2. Residuals (non-blocking)

- **R-B1:** a live launch's stream bring-up window (DISCONNECTED → SUBSCRIBED over the first seconds) could flash the feed line if the page is opened unusually fast; no damping built. Cosmetic; revisit only if observed.
- **R-B2:** banner poll shares the 20s cadence with nothing else; if live REST budgets ever tighten, it's a cheap local endpoint (no Betfair call) — no cost concern identified.
- **R-B3 (parked, operator call):** phone/push alarm for unattended running — the piece 2 scope this replaced. Trigger to revisit: workers left running without the operator at the machine, or the account-footprint ramp.

**B7 remaining:** piece 3 — the one-command daily settlement review-pull (`settlement_liveproof_plan.md` §5b).

<!-- B7 PIECE 2 BUILT (S229) — worker health registry + /api/health/workers + HealthBanner; phone alarm parked (operator call); commit 59dfcf1; suites 1379/130 -->
