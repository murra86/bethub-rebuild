# Settlement-worker diligence — read-only investigation brief

**Commissioned:** 2026-07-01 (Session 214) · Adelaide local timestamps (ACST/ACDT) throughout per DR-021.
**Codebase anchor:** bethub-v3 @ `e2638fa` (confirm current HEAD at session start; if it has moved, note the new sha in the report header and proceed — this brief's file/line anchors were correct as of `e2638fa`).
**Bet-safety:** Read-only. No money-path code, settlement state, Betfair account, or test fixtures are modified. This is investigation, not a fix.

---

## 1. What this brief is and is not

This is an **empirical investigation brief**, not a fix brief and not a build brief. Code's job is to confirm, refute, or refine — with evidence — the findings and risk list Chat mapped in `settlement_worker_diligence_scope.md` (S214), by actually running the test suite, tracing the live composition root, and reading the named code paths. Single bounded Code session.

- Code does **not** write or modify any application code, test code, or settlement/Betfair state.
- Code does **not** propose or draft fixes. Findings only.
- Surprises (anchors that don't match, findings that don't hold up, new risks surfaced) become findings in the report, not blockers — note them and continue.
- Remediation and the eventual settlement-worker build brief are operator-Claude triage territory in the next session, not this one.

## 2. Why this work exists

Settlement-worker (auto-settlement + manual-match-to-lay + the free-bet IOU) is the first money-path build item in this stretch, ahead of the W16 cutover. Standing practice is diligence-first. Because this is money-path and needs to be "really, really solid" (operator steer, S214), Chat mapped the codebase and produced a risk list rather than asserting readiness from a single read. The agreed route is **Chat maps → Code grounds (read-only) → Cowork adversarially gates at the pre-W16 launch decision**. This brief is the "Code grounds" step — it exists because Chat's map can only assert code behaviour; Code can actually run it.

## 3. Pre-reads

- `settlement_worker_diligence_scope.md` — the full grounded map and risk list this brief operationalises. Required, read in full.
- `workflows/bet_entry/v1/settlement.py`, `clients/betfair_client/v1/settlement.py`, `workflows/promos/v1/fb_credit.py`, `fb_deployment.py` — named in scope §3, read before starting each corresponding section below.
- `governance.md` — reference only, for the multi-agent-review heuristic context (not invoked this session, but explains why the route was staged rather than going straight to panel).
- DR-027/DR-028 (two-database boundary) and DR-032 (Betfair market as settlement spine) — reference only, relevant to §5F below.

## 4. System access

- Mac filesystem, bethub-v3 repo — read-only. `git status`, `git log`, `git show`, file reads. No edits.
- Test suite — read-write execution is fine (running `uv run pytest` writes nothing to the app's real state; it's the test harness). Run against the existing fixture-based suite only. **Do not** attempt to run any settlement pass against a real or staging Betfair account — none of this brief's verification touches live Betfair.
- No VPS access needed for this brief — settlement is a Mac-side / app-side concern, not the VPS capture pipeline.

## 5. Substantive scope — per-area empirical confirmation

Each sub-section below corresponds to a specific claim in `settlement_worker_diligence_scope.md`. For each, Code's job is: confirm with evidence (test run output, grep/trace result, line citation), or refute with evidence, or flag as unable-to-determine-read-only with a one-line reason.

### 5A — Live-integration status (scope §3C — the headline finding)

The scope doc's central claim: the auto-settlement worker (`run_settlement_pass`, `run_provisional_resolution_pass`, `SettlementScheduler`) is **implemented but never wired into the running app** — not referenced in `ui/api/dependencies/composition.py`, not started in `ui/api/main.py`, not exported from the workflow `__init__.py`. Meanwhile the manual-resolution router (`ui/api/routers/provisional.py`) *is* wired at `main.py:139`.

Confirm by: grepping the composition root and `main.py` for every reference to `run_settlement_pass`, `run_provisional_resolution_pass`, `SettlementScheduler`, and the provisional router; tracing whether any startup hook, scheduler registration, or background task references the auto-worker anywhere in the app (not just the two named files — check for a task runner, cron-equivalent, or `asyncio` background task registration pattern used elsewhere in the app for comparison, since another workflow might reveal how "live" workers are normally wired here).

### 5B — Test coverage shape (scope §3D)

Confirm the test inventory: run the full `tests/workflows/bet_entry/v1/test_settlement.py`, `tests/ui/api/test_provisional.py`, and the fb_credit test files. Report pass/fail counts, and confirm the scope doc's claim that all tests use `MockSettlementReader` or in-memory storage (zero live-mode tests) — grep for any reference to `RealSettlementReader` or a live Betfair client in the test files to confirm it's genuinely absent, not just absent from the files Chat sampled.

### 5C — Settlement → free-bet-credit failure window (scope §4, risk 2)

This is the sharpest money-path risk in the map: settlement commits a bet's terminal state, and the IOU credit (`record_free_bet_credit`) is a *separate* downstream call. If settlement succeeds and the credit call then fails, the loss is recorded but the refund isn't.

Trace: where in the call chain does settlement's terminal-state commit happen relative to the credit call — same function, same transaction, or genuinely two independent operations with no coupling? Is there any retry, reconciliation sweep, or idempotency check that would catch a bet that's SETTLED_LOST with a qualifying promo attachment but has no corresponding `FREE_BET_CREDITED` event? If none exists, confirm that as a finding (don't propose the fix — just confirm the gap is real and unguarded).

### 5D — Non-idempotent reconciliation bookkeeping (scope §4, risk 3)

Confirm `reconciliation_attempts` genuinely increments per pass with no upper bound or reset, and trace whether that counter (or `last_reconciled_at`) feeds into any settlement *decision* logic (i.e., does the resolver branch on attempt count anywhere) or whether it's purely observational bookkeeping as the scope doc assumes.

### 5E — v1 deferred/not-implemented carve-outs (scope §4, risk 4)

Grep `settlement.py` and the betfair client settlement file for every comment or docstring indicating a v1 deferral, "not implemented", "TODO", "post-v1", or equivalent. Produce the full list with line references — the scope doc named one example (post-settlement market-void re-transition) but flagged that the complete list wasn't yet enumerated.

### 5F — Odd-result / PROVISIONAL parking exhaustiveness (scope §4, risk 5)

Trace `_resolve_settlement_for_bet`'s branching: enumerate every terminal Betfair market/runner state the resolver handles, and confirm whether the PROVISIONAL fallback is genuinely the default for anything unrecognised (i.e., no state falls through to an automatic terminal settlement by accident — dead-heat, scratched/removed runner, void market, and any other non-standard state should all route to PROVISIONAL unless explicitly and correctly handled).

### 5G — Two-database boundary re-confirmation (scope §3F)

Quick re-check, not a deep audit: confirm settlement.py and the betfair settlement client don't cache, denormalise, or write anything from `capture.db` into v3 operational tables (or vice versa) — the scope doc's first read found this clean; this is a second-pair-of-eyes confirmation, low effort expected.

## 6. Sequencing within session

Suggested order (dependency-driven, Code may reorder if a different sequence is operationally cleaner — say so in the report if it deviates):

1. **5A first** — the headline finding gates how much weight the rest of the investigation carries (if the auto-worker somehow *is* wired, that changes the risk profile of everything downstream).
2. **5B** — run the test suite early; failures or surprises here inform how much to trust the fixture-based confirmations in 5C–5F.
3. **5C, 5D, 5E, 5F** — the four risk-list items, any order, each self-contained.
4. **5G last** — quick confirmation, low effort, no dependencies.

## 7. Empirical verification / success criteria

This is an investigation, not a fix, so there's no pre/post baseline. Success criteria per finding:

- Each of 5A–5G resolves to one of: **confirmed** (with the specific evidence — command run, output, line citation), **refuted** (with the corrected finding and evidence), or **indeterminate read-only** (with a one-line reason, e.g. "requires live Betfair sandbox access, out of scope for this brief").
- Test suite run (5B) reports actual pass/fail counts, not an assumption that the scope doc's "~50+" estimate is exact.

## 8. Output spec

Single file: `settlement_worker_diligence_investigation_report.md` at the bethub-rebuild root.

Structure: one section per 5A–5G (same headings), each ending in a one-line **confirmed / refuted / indeterminate** verdict, followed by a short **§9 — overall read** (2–4 sentences, plain language, no recommendation on build sequencing — that's the next operator-Claude session's job) and a **§10 — anything else noticed** catch-all for anchors that didn't match or findings outside the named scope that surfaced incidentally.

Length: roughly 150–350 lines. Code may exceed if the evidence trail genuinely warrants it (e.g. a long grep output worth including in full) — flag if so in a brief self-assessment line at the top of the report.

Report does not contain: proposed fixes, a build sequencing recommendation, a go/no-go call on launch readiness, or any edits to application code.

## 9. Hard limits

- No edits to any file under `workflows/`, `clients/`, `domain/`, `ui/`, or any test file. Read-only on all application and test code.
- No git operations beyond read-only (`status`, `log`, `show`, `diff` against nothing). No `commit`, `stash`, `checkout`, `reset`, `add`.
- No connection to a real or staging Betfair account. Test-suite execution against existing fixtures only.
- No scope creep into other DR-029 items, other build streams, or the placings/VPS workstream — this brief is settlement-worker only.
- No fix proposals, no build brief drafting, no launch-readiness verdict. Findings only.
- If Code judges the investigation needs more than one session to do properly, surface that as a finding and stop at whatever's coherent — partial-but-coherent beats complete-but-rushed.

## 10. What happens after Code's session

Next operator-Claude session reads the investigation report in full, triages the confirmed/refuted/indeterminate findings against the operator, and decides the next step — most likely either (a) a settlement-worker build brief once the picture is solid enough, or (b) a further narrow investigation if 5A–5G surfaced something that needs its own follow-up. The pre-W16 Cowork multi-agent gate remains parked until the worker is actually wired toward launch, per the staged-hybrid route agreed this session.

## 11. Cross-references

- `settlement_worker_diligence_scope.md` (S214) — the source map and risk list this brief operationalises.
- DR-033 (settlement as the first money-path build item this stretch), DR-027/DR-028 (two-database boundary), DR-032 (Betfair market as settlement spine).
- `governance.md` — multi-agent review heuristic, referenced but not invoked; the parked pre-W16 Cowork gate item this feeds into.
- Precedent: Session 33's source-review brief (structural template for this brief's per-area shape).
