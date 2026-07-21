# Settlement-worker diligence — read-only investigation report

**Brief:** `settlement_worker_diligence_investigation_brief.md` (S214, commissioned 2026-07-01). Executed read-only per §9.
**Investigation run:** 2026-07-02, ~07:55–08:06 ACST (DR-021 Adelaide, ACST = UTC+9:30; ≈ 2026-07-01 22:25–22:36 UTC).
**Codebase anchor:** bethub-v3 @ `e2638fac2c659783448bece9b1810294512068bf` (`e2638fa`) — **HEAD unchanged from the brief's anchor**, working tree clean, 0 commits ahead. All brief/scope file+line anchors verified present at this sha.
**Bet-safety:** Read-only throughout. No application/test/settlement/Betfair state modified. Only execution was `uv run pytest` against existing fixture-based tests (§4). No live/staging Betfair. Findings only — no fixes proposed, no build sequencing, no launch verdict.

**Self-assessment (per §8):** ~121 source lines — marginally under the ~150–350 soft guide, by choice: every finding lands with its raw evidence and no padding was added to reach a line target (the lines are dense — long grep/citation lines render longer than the count suggests). If a fuller transcript dump is wanted, the per-finding raw grep/read output is available. One headline change vs the scope map: **5F is REFUTED** (a dead-heat winner does not park as PROVISIONAL — it force-settles to SETTLED_WON and is paid full). Everything else confirmed.

**Method + guardrail note:** findings were produced by a parallel read-only trace of 5A–5G, each draft verdict then independently attacked by an adversarial verifier that re-ran the load-bearing greps/reads (14 agents total), with the orchestrator additionally grounding the anchor, 5A, the 5B test run, and the 5F dead-heat path first-hand. **This internal adversarial pass is a verification *method*, not the pre-W16 Cowork governance panel** — that cross-model panel remains parked per brief §10/§11 and scope §5; nothing here substitutes for it. Evidence below is cited at the grep/line granularity it was gathered at.

---

## 5A — Live-integration status (scope §3C, headline)

**Claim:** the auto-settlement worker (`run_settlement_pass`, `run_provisional_resolution_pass`, `SettlementScheduler`) is implemented but never wired into the running app; the manual-resolution router is wired at `main.py:139`.

- Whole-repo grep for the three worker symbols → every hit is inside `workflows/bet_entry/v1/settlement.py` (defs at :698, :914, :1235; `__all__` at :1345/:1352/:1353) or `tests/workflows/bet_entry/v1/test_settlement.py` (:67-68, :617, :1959). **Zero app-code references anywhere else.**
- `ui/api/dependencies/composition.py` (580 lines): **zero** settlement/scheduler references (ripgrep exit 1).
- `ui/api/main.py`: the only background bring-up in `lifespan` (main.py:88-107) is the Betfair **streaming** socket (`start_streaming`/`await_subscribed`, main.py:64-65), gated on `betfair_mode == "live"`. No `asyncio.create_task`/`BackgroundTasks`/`APScheduler`/`Timer` for any settlement pass anywhere under `ui/api`. `provisional_router` is included at **main.py:139** (imported main.py:32).
- The wired provisional router's only settlement-workflow call is `apply_manual_operator_resolution` (provisional.py:344) — the **manual** path, not the auto-worker.

**Refinement A (SettlementScheduler-as-Protocol — traced for a concrete impl before landing):** `SettlementScheduler` is a `typing.Protocol` (settlement.py:1235), and its docstring **explicitly defers the production asyncio-loop scheduler to "v3 build proper"** (settlement.py:1238-1239). Concrete classes *do* exist — `ManualSettlementScheduler` (settlement.py:1255, docstring "Test scheduler — never fires automatically") and `ThreadingSettlementScheduler` (settlement.py:1286, a reference `threading.Timer` impl) — but **neither is instantiated or `.start()`-ed anywhere in app code** (grep for their construction across non-test code returns only their defs + `__all__`; no `.start()` on any scheduler exists under `ui/`). So the precise finding is stronger than "built but unwired": the **production scheduler does not exist (deferred to v3)**; only a test stub and a reference impl exist, and nothing starts either. "No concrete worker exists at all" would be *too* strong (the reference impl is concrete); "no *production* scheduler exists and nothing is wired/started" is exact.

**Refinement B (exact `__init__` exports):** `workflows/bet_entry/v1/__init__.py` exports the settlement **type** `MarketSettlement` (imported line 40, in `__all__` line 108) and the sibling **reconciliation** schedulers (`ManualReconciliationScheduler`/`ThreadingReconciliationScheduler`/`ReconciliationScheduler`/`run_reconciliation_pass`, lines 53-59/119-125) — but **does not export any settlement worker function or settlement scheduler**. The settlement worker is thus even less surfaced than its reconciliation sibling.

**Comparative note:** the app has three parallel scheduler families (TriggerB in `orchestrator.py`, Reconciliation in `reconciliation.py`, Settlement in `settlement.py`), each Manual+Threading. None of the three is started in the app lifespan/composition — the only live async bring-up in the whole app is the Betfair streaming socket. So the auto-worker doesn't diverge from a live pattern; there is no live "periodic worker" wiring pattern in the app at all yet.

**Verdict: CONFIRMED** — the auto-settlement worker is not wired into the running app; the manual router is (main.py:139). Sharpened: the production scheduler is explicitly deferred to v3; only a never-started test stub + reference impl exist; the worker isn't exported from its package `__init__`.

## 5B — Test coverage shape (scope §3D)

**Claim:** all settlement/provisional/fb_credit tests use `MockSettlementReader` or in-memory storage — zero live-mode tests.

- `uv run pytest` (orchestrator, first-hand) across the named files + the adjacent Betfair-client settlement test: **117 passed, 0 failed, 0 skipped** in 1.15s. Per file: `tests/workflows/bet_entry/v1/test_settlement.py` **83**, `tests/ui/api/test_provisional.py` **14**, `tests/workflows/promos/v1/test_fb_credit.py` **8**, `tests/workflows/promos/v1/test_fb_deployment.py` **6**, `tests/clients/betfair_client/v1/test_settlement.py` **6**. The four §5B-named files alone = **111 passed** (independently reproduced by the verifier: settlement 83 / provisional 14 / fb_credit 8 / fb_deployment 6). Scope's "~50+ / ~10 / ~20+" estimates resolve to **83 / 14 / 14** (fb_credit+fb_deployment) actual.
- `RealSettlementReader` is **absent repo-wide** (ripgrep exit 1, plain and case-insensitive). No named test file imports/instantiates a Betfair client or any network primitive (`requests`/`httpx`/`urllib`/`socket`); the only `connect()` calls are `sqlite3.connect(':memory:')`.
- Positive shape: `MockSettlementReader` (an in-memory dict implementing the `SettlementReader` Protocol) appears 55× in `test_settlement.py`; provisional tests use `InMemoryBetRecordStorage` via FastAPI `dependency_overrides` with the docstring "No real Betfair API calls"; `test_fb_credit` uses `sqlite3 :memory:`; `test_fb_deployment` uses a `tmp_path` SQLite file.
- 5B crux (the `rest_client` fixture): in `tests/clients/betfair_client/v1/conftest.py:39-40` it is `BetfairRestClient(auth=MockAuthProvider(), transport=MockTransport())` — a **fake** transport (a pure in-memory path-routing dict, `tests/fixtures/betfair/rest_responses.py:310-355`), never a live connection. Note: that conftest serves the betfair-client tests and is **not** imported by the settlement/provisional/promos tests, so the four core files don't even reach it.

**Refinement C (actual promos test files):** present under `tests/workflows/promos/v1/` — `test_fb_credit.py`, `test_fb_deployment.py`, `test_promo_derivations.py`, `test_promo_store_adapter.py` (plus `tests/ui/api/test_promos_credit_in.py`, `test_promos.py`). The "fb_credit test files" plural resolves to fb_credit + fb_deployment; both were run.

**Verdict: CONFIRMED** — fixture/in-memory only, zero live-mode tests; `RealSettlementReader` does not exist; 117 pass / 0 fail (111 across the four named files).

## 5C — Settlement → free-bet-credit failure window (scope §4 risk 2)

**Claim:** settlement commits terminal state; the IOU credit is a separate downstream call; if settlement succeeds and the credit then fails, loss is recorded but refund isn't — unguarded.

- `settlement.py` has **zero** references to `credit`/`free_bet`/`fb_credit`/`promo`/`record_free` (grep, no output). The terminal-state commit in `run_settlement_pass` writes `SETTLED_LOST` purely via `storage.update_settlement_state` (settlement.py:753-774); the only follow-on is counter bookkeeping — **no credit call in the settlement loop**.
- `record_free_bet_credit`'s **sole non-test caller** is the manual `POST /api/v1/promos/credit-in` endpoint (promos.py:268), on its own connection with an independent `conn.commit()` (promos.py:285), writing to the **promo-event spine** via `adapter.append_event` (fb_credit.py:197) — a different store from the `bets` table. `fb_credit.py`'s own docstring (fb_credit.py:10-13) states it "never touches `settlement.py`, `apply_manual_operator_resolution`, or `provisional.py`."
- No reconciliation/repair/backfill detects a `SETTLED_LOST` + qualifying-promo bet lacking a `FREE_BET_CREDITED` event: `reconciliation.py` has zero credit/promo refs; `ops/` and `scripts/` contain no credit sweep. The only credit-path guard, `find_existing_credit` (fb_credit.py:143-147), prevents **double**-crediting — it does not detect or repair a **missing** credit.

**Surfaced nuance (wider than the scope framed, tie-in to 5A):** the credit is not an automated downstream step from settlement *at all* today — it is a **separate manual operator action** (`POST /credit-in`, source=OPERATOR) whose §5.3 gate *requires* the bet to already be `settled_lost` (promos.py:208-212). So the loss-recorded/refund-omitted window opens not only if a call fails but if the operator simply never invokes credit-in, with nothing to reconcile either case. (Reported as an observation, not a fix.)

**Verdict: CONFIRMED** — the settlement commit and the IOU credit are genuinely independent operations (different modules, endpoints, connections, storage spines) with no atomic coupling and no reconciliation for a missing credit. The gap is real and unguarded.

## 5D — Non-idempotent reconciliation bookkeeping (scope §4 risk 3)

**Claim:** `reconciliation_attempts` increments per pass with no cap/reset; purely observational (doesn't feed settlement decisions).

- Both storage backends increment unconditionally by +1 per bet per pass: in-memory adds `attempts_increment` (default 1) to the prior value with no cap (bets.py:388-406); SQLite does `COALESCE(reconciliation_attempts,0) + ?` (bets.py:748-762). Invoked per-bet-per-pass from reconciliation (reconciliation.py:487-493, :538-541, "regardless of whether a transition fired") and the settlement/manual paths (settlement.py:852-870, :1206). **No cap** (keyword sweep empty), **no reset-to-zero** (reset grep empty).
- Candidate selection filters **only** on `match_status` + `placed_at` — never on the attempt counter (reconciliation.py:416-423; SQLite WHERE at bets.py:722-728) — so a stuck bet is re-swept and re-incremented **unbounded**. Load-bearing test proves it: a stuck PROVISIONAL bet swept 3 passes with no transition ends at `reconciliation_attempts == 3`, status unchanged (test_reconciliation.py:667-693).
- Every one of the ~14 non-test references to the counter is data movement — adapter row↔record mapping (bet_store_adapter.py:68/142), the increment write itself, migration INSERT, hydration, dataclass/schema declarations, docstrings (settlement.py:714/1153). **No code branches on it**; a comparison/branch grep found no conditional (only a benign `last_reconciled_at is not None` serialization guard at bets.py:595). The bookkeeping write is documented non-fatal on failure (settlement.py:862-865), reinforcing its observational role.
- Sibling `last_reconciled_at` *is* read elsewhere (surfaced in the provisional payload provisional.py:380; reused as `entered_provisional_at` settlement.py:309) — but those are timestamp reads, non-branching, and not the attempts counter.

**Verdict: CONFIRMED** — `reconciliation_attempts` is non-idempotent (unbounded +1 per pass, no cap, no reset) and is purely observational: it feeds no settlement/resolver decision.

## 5E — v1 deferred / not-implemented carve-outs (scope §4 risk 4)

**Claim:** v1 deferrals exist in comments (scope named the post-settlement market-void re-transition); the complete list was not yet enumerated. Full enumeration below. `workflows/bet_entry/v1/settlement.py` holds them all; `clients/betfair_client/v1/settlement.py` holds **none** (grep of that file returns only design/special-case notes at :94/:98, no deferral/TODO/not-implemented markers).

**Genuine money-path carve-outs:**
- **Post-settlement market-void re-transition — NOT implemented at v1** (the scope's named example), documented in *both* resolvers: `_resolve_settlement_for_bet` (settlement.py:350-353) and `_resolve_provisional_for_bet` (settlement.py:547-550); the worker only reads PENDING/PROVISIONAL. Its trigger source `POST_SETTLEMENT_VOID` is defined (settlement.py:244-247, enum member :250) but **has zero firing sites repo-wide** — and the worker's query sites only pull PENDING/PROVISIONAL — so a terminal-state bet whose market later voids can never be re-picked-up. Carried forward per W6.5 brief §5.5 Change C.
- **No persisted settlement audit trail at v1** (settlement.py:1157-1161): manual transitions log `operator_reason`/prev/new states at INFO only; a structured audit table is deferred to a follow-up brief (W8 report §6).
- **Manual operator resolution can only fire from PROVISIONAL at v1** (settlement.py:1112-1116) — no manual override of PENDING or terminal states at v1.

**Placeholder / calibration deferrals (money-path-adjacent thresholds):** all three `DEFAULT_*` thresholds are v1 placeholders "calibrate post-DR-029-close" (settlement.py:56-58): `DEFAULT_AGE_THRESHOLD_SECONDS`=300 (:61-68), `DEFAULT_SETTLEMENT_INTERVAL_SECONDS`=60 (:71-78), `DEFAULT_PAST_WINDOW_SECONDS`=1800 (:81-88).

**Build-proper deferrals (non-money-critical):** burst-review queue is v3 UI, and `entered_provisional_at` is only *approximated* at v1 by `last_reconciled_at` (exact-transition-time column deferred, settlement.py:258-274); production asyncio scheduler deferred to v3 (settlement.py:1237-1239); the two scheduler classes may consolidate in build-proper (settlement.py:1256-1262).

**Incidental (not gaps):** forward-compat defensive branches for the closed runner-status enum (settlement.py:473-475, :676-677); a `# pragma: no cover` defensive branch (:1223); a design note on the omitted age filter (:935-939). No `NotImplementedError`/raise-stub/empty-pass stubs exist in either file (the `...` hits are Protocol method bodies at :114/:1251).

**Verdict: CONFIRMED** — deferrals exist and are now fully enumerated. The sharpest genuine money-path carve-out is the post-settlement market-void re-transition (`POST_SETTLEMENT_VOID` defined but never fired; terminal bets whose market later voids are never revisited).

## 5F — Odd-result / PROVISIONAL parking exhaustiveness (scope §4 risk 5)

**Claim:** the resolver parks odd/unrecognised results as PROVISIONAL rather than guessing, and this parking is exhaustive — nothing odd (dead-heat, removed runner, void market, unexpected state) slips through to an automatic terminal settlement.

**Part that holds:** the *default fall-through* is safe. A genuinely unrecognised `settlement_status` routes to PROVISIONAL (`reason_code="provisional_unexpected_state"`, settlement.py:473-479), and a missing runner (selection not in the market) also routes to PROVISIONAL (settlement.py:419-427). Market-level void routes to terminal VOIDED (settlement.py:406-408) — correct.

**Part that REFUTES exhaustiveness — dead-heat (first-hand confirmed):** `RunnerSettlementStatus` is a closed 3-value enum, `WINNER`/`LOSER`/`REMOVED` (clients/betfair_client/v1/settlement.py:35-38) — there is **no DEAD_HEAT state**. A dead-heat winner returns as `WINNER` and hits the unconditional branch `WINNER → SETTLED_WON` in the PENDING resolver (settlement.py:449-459) **and** the parallel PROVISIONAL resolver (settlement.py:652-662). `dead_heat_count` is carried only as metadata in the `counts` dict (settlement.py:400) and passed through to the storage write (settlement.py:756) — **no branch anywhere gates on `dead_heat_count`** (conditional grep empty, first-hand confirmed), and the per-runner `voided:bool` field is never read by the resolver. Downstream, `balance_derivation.py:270` pays a won bet **full** winnings (`matched_stake * (price - 1)`, then `* conversion`) with **no** dead-heat reduction — and `workflows/balances/` contains **zero** `dead_heat`/`reduction` references (grep empty). Reduction factors for removed runners are likewise not modelled anywhere in `workflows/`, `clients/`, or `domain/`.

So a dead-heat — explicitly named in the scope as something that must not slip through — does **not** park to PROVISIONAL; it auto-settles to `SETTLED_WON` and is paid in full. (Two trace imprecisions were corrected by the verifier and are excluded above: `reduction` is unrelated order-sizing, and the `.voided` grep hits were counter fields, not the runner flag.) Reported as a factual finding; whether it is a defect requiring remediation is operator-triage territory, not this brief's call.

**Verdict: REFUTED** — PROVISIONAL is the safe default for the *truly unrecognised*, but the exhaustiveness claim does not hold: a dead-heat winner force-settles to `SETTLED_WON` (both resolvers) and is paid full winnings, with `dead_heat_count`/`voided` never gating any branch or payout.

## 5G — Two-database boundary re-confirmation (scope §3F)

**Claim:** settlement.py and the betfair settlement client don't cache/denormalise/write `capture.db` into v3 operational tables (or vice versa).

- Neither settlement file references `capture.db`, `vps_client`, the VPS IP, or any analytical surface. The only `capture` token is the English docstring verb "captures" at settlement.py:215 (boundary-token grep otherwise empty across both files).
- Transitive check: the betfair settlement client imports only stdlib + pydantic + four intra-package modules (`_clock`/`_connection`/`_errors`/`envelope`, clients/betfair_client/v1/settlement.py:17-20); `envelope.py:12` is an explicit DR-030 disclaimer that it does not import `vps_client`. The `vps`/`analytic` tokens in the betfair package live only in **non-imported** siblings (placement/consumer/identity/racing_catalogue/_audit).
- The worker reads Betfair via `clients.betfair_client.v1.settlement` (operational canonical source) and writes v3 operational bet-state via `store/repositories/bets.py`; the only `snapshot` reference is the typed `MarketSettlement` last-read snapshot (operational Betfair data), not capture.db.

**Verdict: CONFIRMED** — the settlement path respects the DR-027/028 two-database boundary; no capture.db caching/denormalisation, in either direction.

---

## §9 — Overall read

The settlement chain reads exactly as the scope mapped it: **code-complete, thoroughly tested against fake data (117/117 green), and not plugged into anything live** — the production scheduler is explicitly deferred to v3 and nothing starts the worker, so the biggest exposure is unproven plumbing rather than untested logic. Two money-path gaps are real and unguarded as described: the settlement→IOU-credit step is fully decoupled (the credit is a separate *manual* action today, with no reconciliation catching a missing credit), and the post-settlement market-void re-transition is defined-but-never-fired. The one place the map was **wrong** is odd-result exhaustiveness: a dead-heat winner is not parked as PROVISIONAL — it force-settles to `SETTLED_WON` and is paid full winnings, with `dead_heat_count` never consulted. The reconciliation-attempts counter is non-idempotent but genuinely observational, and the two-database boundary is clean.

## §10 — Anything else noticed

- **Anchors:** all brief/scope file+line anchors matched at `e2638fa` (settlement.py 1354 lines, betfair client 118, domain/settlement `__init__` empty, main.py:139, provisional.py:344, `apply_manual_operator_resolution`@1128). No drift.
- **Scope §3C precision (carried refinement A):** the scope's "SettlementScheduler … Protocol" framing is right; the material sharpening is that concrete scheduler classes *do* exist but are a **test stub + reference impl**, the **production** scheduler is explicitly deferred to v3, and none is started — so "never provisioned" is accurate and, if anything, understated.
- **Scope §3D count precision:** actual counts are 83/14/8+6 (not ~50/~10/~20); all green.
- **`RealBetfairAdapter` in adjacent tests (§10 catch-all):** `tests/workflows/bet_entry/v1/test_betfair_adapter.py` references `RealBetfairAdapter` — but that is the production *adapter class under test*, driven by a mock transport, **not** a live-Betfair settlement test, and it is outside the §5B-named files. The "zero live-mode" finding stands beyond the sampled files.
- **5C is wider than framed** and **5D's sibling `last_reconciled_at` is read (non-branching)** — both detailed in-section; noted here so a later reader doesn't take the scope's narrower framing as the whole picture.
- **Reconciliation mirror:** the app has parallel `ReconciliationScheduler`/`TriggerBScheduler` families with the same Manual+Threading shape; like the settlement scheduler, none is started in the app lifespan — there is currently no live periodic-worker wiring pattern in the app at all.

**Not in this report (per §9 hard limits):** no proposed fixes, no build-sequencing recommendation, no launch-readiness go/no-go. Those are the next operator-Claude triage session's call; the parked pre-W16 Cowork governance panel is unaffected by this diligence.
