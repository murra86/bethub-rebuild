# B7 piece 1 — durable app log + placement-audit substrate — build report (S229)

**Run:** 2026-07-06 (S229), Adelaide-anchored per DR-021. Same session as the B5 tunnel hardening (`b5_tunnel_hardening_report.md`).
**Outcome:** BUILT + verified end-to-end in mock mode (no Betfair contact, no live-store write). Suite **1358 → 1367 green**; behavioural red-before proven on the composition pair. Committed `d0ef5d2`, pushed. **Classification: implemented + mock-proven**; the live confirm is passive — the next real launch writes the diary at `~/.bethub/logs/` by default, nothing to flip.
**Anchor:** built on `eef2fc2`. Files: `ui/api/logging_setup.py`, `clients/betfair_client/v1/_audit.py` (+`__init__`), `ui/api/config.py`, `ui/api/dependencies/composition.py`, `tests/conftest.py`, 3 test files.

---

## 1. What was closed

Two "vanishes on window-close" gaps from the B7 scope (`cutover_readiness_map.md` B7 item 1) + **F8**:

- **The app diary.** Worker settlement/verification records, placements, errors — previously Terminal-only (and only two namespaces reliably surfaced at INFO at all). Now every app namespace (`ui`, `workflows`, `clients`, `store`) also writes to a daily-rotating file: `~/.bethub/logs/bethub-app.log`, **retained permanently** (operator call, S229 — was 60 days at first commit; disputes/account reviews look back further and a day's log is a few MB; follow-up commit `a4fb928`), `BETHUB_LOG_DIR` override. One shared handler owns the rotation (per-namespace handlers on one file would race the midnight rollover). Root logger untouched (the uvicorn double-print guard holds); if the log dir is unavailable the app runs terminal-only after a single warning — logging can never stop the app.
- **The placement audit trail (F8 CLOSED).** Contract §12's write-surface audit entries went to a per-process in-memory list — gone at shutdown, the residual flagged at S219 and at the S229 B1 tick. New `FileAuditLogSink` (the contract §12.2 "deployment substrate", a named deferral now due) appends one JSON line per place/cancel/replace to `~/.bethub/logs/placement-audit.jsonl` (`BETHUB_AUDIT_LOG_PATH` override), opened per write so a crash loses nothing buffered. **No-silent-loss fallback:** a disk failure logs the full serialised entry at ERROR — into the durable app log — and never raises into the money path. The live composition now builds this sink; the memory sink remains test-only.

## 2. Discipline notes

- **Diary purity:** the suite redirects `BETHUB_LOG_DIR` to a tmp dir at conftest import (before `ui.api.main`'s import-time logging setup can run), so test runs can never write test records into the real diary or the real money-audit file. Same pattern as the existing placement-failure-log isolation.
- **Pre-existing caplog pins:** widening the namespaces broke two existing tests that assert on captured log records (`propagate=False` starves pytest's root-attached capture). Fixed suite-wide with a conftest bridge attaching caplog's handler directly to the app namespaces — production propagation flags (and their S161 test pin) untouched. Future caplog tests just work.
- **Mock-mode end-to-end proof:** (a) plain boot with default env → `~/.bethub/logs/bethub-app.log` created at the real path with real records; (b) mock lay through the API with scratch DB + scratch log dir → full structured audit line (operator, side, price, stake, outcome, Betfair ref) in `placement-audit.jsonl`; real audit file confirmed absent after. The real diary holds only genuine boot lines.

## 3. Residuals (non-blocking)

- **R-L1:** uvicorn's own access/error lines are not in the diary (deliberate — root/uvicorn config untouched; the app records are the forensic surface). Revisit only if a fault post-mortem ever needs request-level HTTP history.
- **R-L2:** the audit JSONL never rotates (append-only, one line per real placement — years to matter at operator volume). Fold into a later housekeeping pass if it ever grows.
- **R-L3 (watch):** `clients` tree now surfaces at INFO in the Terminal too; if live streaming proves chatty at INFO, drop the *stream* namespace's Terminal level — keep the file at INFO.

**B7 remaining:** piece 2 (heartbeat/phone alarm on real faults only), piece 3 (the one-command daily settlement review-pull, `settlement_liveproof_plan.md` §5b).

<!-- B7 PIECE 1 BUILT (S229) — durable app log + placement-audit JSONL; F8 closed; commit d0ef5d2; suite 1367; residuals R-L1..R-L3 -->
