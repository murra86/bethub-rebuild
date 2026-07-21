# V3 cutover-readiness map

**Status refresh — Session 229, 2026-07-06 ACST.** The money path is DONE: **B1 ✅ / B2 ✅ / B3 ✅ / B4 ✅ all live-proven.**
- **B2 + B3** — live-money-proven S227 (`b3_liveproof_result.md`): matched lay reconciled to true stake and settled at true money (−$4.91); never-matched lay held → park valve. Settlement side completed **S229**: supervised settlement window stamped the four S228 lays terminal on the first sweep, $0 money, ledger untouched.
- **B1** — **formally ticked S229.** Evidence: six real lays placed through the tool across S227/S228 (Case A `434257406420` matched→settled true money; Case B + four S228 measurement lays resolved as no-bets), all through a genuinely SUBSCRIBED stream (§13.1 interlock live: stream held SUBSCRIBED through both sessions incl. restart — `stream_read_buffer_overflow_fix_report.md`). Non-blocking residuals, named: (a) F8 placement-audit sink still in-memory — fold into B7 durable-logs; (b) the interlock's refusal path (placement blocked when stream not subscribed) is unit-tested only, never tripped live — refusal is the money-safe direction.
- **B4** — promo catalogue seeded + operator-confirmed in the picker (S228).
- **F-LIVE-1** (promo cross-thread 500) fixed + live-proven `7d221b7`; **F-LIVE-2** (lapsed lays parking) measured, fixed + live-proven `2e22c5f` (S228).

**B5 ✅ DONE S229** (`b5_tunnel_hardening_report.md`, `eef2fc2`): launcher auto-starts the 8400 tunnel + health-gated reconnect watchdog; coexists with v2's supervisor until cutover.
**B7 ✅ DONE S229** (three reports `b7_piece{1,2,3}_*.md`, commits `d0ef5d2`/`a4fb928`/`59dfcf1`/`a4cdab3`): durable app log (permanent retention) + placement-audit JSONL (F8 closed); in-tool fault banner over worker/stream health (phone alarm PARKED by operator call — revisit at unattended/30-account scale); read-only daily money check (`uv run python -m ops.settlement_review`). Suite 1383.

**Remaining runway: B6 ONLY (cutover mechanics/day-one state/fall-back).** Entry step: the pre-W16 multi-agent go/no-go panel (see §Recommended sequence) — DUE, operator-involving. Bonus S229 live finding: S227's parked `434257942837` self-cleared (`failed`/$0/`voided`) during the supervised window under the S228 LAPSED fix — the manual queue is empty.

The body below is the S219 map, retained as built; read statuses through the refresh above.

---

**Built:** Session 219, 2026-07-02 ACST. **Author:** Chat (operator-approved criteria).
**Purpose:** turn "v3 cutover" from a vague goal into a concrete, prioritised checklist — what must be true before we retire v2 and run the day on v3, and where each piece stands.
**Grounding:** `workflow_integration_audit.md` (S189, 2026-06-25 — the live-integration audit of the Scope-A workflow) is the backbone; overlaid with the two known deltas since (settlement worker built S217/triaged S218; Log Past Bet re-plumbed to the tunnel + live-proven S209/2026-06-30). Scope-A = Strategy 1 (Safety Net) + free-bet conversion ≈ 95% of the operation.
**Caution:** the S189 statuses are a week old; pieces with interim work are flagged **[re-confirm]** rather than asserted.

---

## The criteria (operator-approved, S219)

1. **Needed to run the day?** — weighted to Strategy 1 (Safety Net) + Strategy 2. Nice-to-haves don't block.
2. **Proven, or just built?** — the live-integration taxonomy: **live-proven** (exercised against the real system in the running app) / **built-unproven** (code + tests, fixtures only) / **not-wired**. Only live-proven clears a critical-path piece.
3. **Touches money?** — bets / settlement / balances / free-bets / hedges get the strictest bar + a safety check.
4. **Will v3 have what it needs on day one?** — fresh start, no history carried; what must be seeded/handled at the flip.
5. **Can we fall back?** — flip mechanics + a coexistence/rollback window against v2.

**Blocker test:** a piece blocks cutover if it's *needed to run the day* AND *not yet live-proven* — money-path pieces held strictest.

---

## Critical-path status (the Scope-A day)

| Piece | Money? | Best-known status | Note |
|---|---|---|---|
| Read Betfair prices / market / catalogue | — | **live-proven** ✅ | S189 tier-3 (live prices, real runners). |
| EV column / promo-prep wiring | — | **live-proven** wiring ✅ | But arithmetic needs promo rows → blocked by promo-seed (below). |
| Log the bet (store write) | — | **built-unproven** ⚠️ [re-confirm] | S189: real+provisioned, one live-run check away. Interim cash/lay-prefill work — re-confirm. |
| Mark-triggered / credit free bet (the hinge) | money-adjacent | **built-unproven** ⚠️ | Free-bet asset created. Gated store write; read side proven. |
| Lay the runner (Betfair placement) | **money-path** | **built-unproven** ⚠️⚠️ | Real placement surface; needs a genuine SUBSCRIBED stream (§13.1 interlock). No live placement evidence yet. |
| Auto-settlement worker | **money-path** | **built-unproven** ⚠️⚠️ | Was *not-wired* at S189; built S217, triaged clean S218; flag OFF, never run vs real Betfair. Guards park-not-overpay. |
| Manual settlement resolve (burst review) | money-adjacent | **built-unproven** ⚠️ | Queue read proven; nothing populates PROVISIONAL live until the worker runs. |
| Log Past Bet — late-entry lookup | — | **live-proven** ✅ [updated] | Re-plumbed to the 8400 tunnel (vps_client rewrite) + live-proven S209. Residual: tunnel auto-start/health; write-side (`create_manual_bet`) live-run check. |

---

## The cutover blockers (ranked)

**B1 — Lay placement, live-proving (money-path, highest stakes).**
The exchange leg of the conversion loop. Built but never fired live; needs a real lay through a genuine subscribed stream. This is the single riskiest piece — plan it carefully (small real lay, watch the interlock + audit trail). NOTE the placement audit sink is in-memory today (F8) — worth durability before we lean on it.

**B2 — Auto-settlement worker, live-proving (money-path, operator-actionable now).**
Built + triaged clean, wired but OFF. Live-prove by flipping `BETHUB_SETTLEMENT_WORKER` on in live mode and watching it settle real bets (and, crucially, watching its park decisions via the §5.1b verification records). Lower-risk than it sounds — the guards park anything uncertain rather than overpay. **This is the cheapest money-path blocker to start on.**

**B3 — Store-write live-proving (cheap cluster) + LAY money-path fix (fix-side GOVERNANCE-CLOSED S226; live-proof pending).**

**S226 — B3 fix-side GOVERNANCE-CLOSED** (`b3_governance_close.md`). HIGH-1 triaged clean + focus-re-verified (S226 open); then the **R2 price-null hardening** built + proven first-hand (F1/F2 in `reconciliation.py`), 3-lens read-only adversarial re-verify **R2 UPHELD** and surfaced **R3** (F2 left a stale non-None price on FAILED zero-stake rows — money-harmless; hardened so terminals clear the price). Both red-before/green-after proven; **suite 1343 green** on `e2638fa`; R2 surface residual **none**. **Only gate left = operator supervised live-proof** (§4 runbook), which clears **B2↔B3**. Two watch-items to observe live: **R1** (partial→full lay must converge to the TRUE stake, never a stored-low `FINAL_FULL` — the sole open money-adjacent item, MEDIUM) and **R2** (still-pending lay must keep its price). Operator commit-time: **HIGH-2** (stage/commit vs the shared S222/S223 uncommitted tree) + **LOW-5** (`*.db.bak-*` gitignore). Flags OFF until the live-proof passes.

**(S225, retained for the record)**
Log-bet, credit-in/mark-triggered, manual-resolve — all "one live-run check away" per S189. Bundle with normal live use to lift them to proven. Credit-in is money-adjacent (creates a free-bet asset) so watch it.

**S225 — the not-wired finding was one level too shallow; root cause + fix now built.** The real cause: `place_lay` (`racing.py:1105-1109`) writes a not-fully-matched lay **terminally** as `FINAL_PARTIAL matched_stake=0`, which the reconciliation sweep (`PROVISIONAL*` only) never touches — so wiring the worker alone fixes nothing. The **4-part coupled fix** (`b3_lay_settlement_fix_design.md`) is **BUILT + suite-green** (`b3_lay_settlement_fix_report.md`, HEAD `e2638fa`, additive on the dirty tree, no git writes, 1327 passed): **P1** re-label → `PROVISIONAL_PENDING`; **P2** wire the periodic reconciliation worker (on-in-live + `BETHUB_RECONCILIATION_WORKER` kill switch); **P3** `listClearedOrders` true-stake recovery; **P4** settlement match-gate + park valve. A **max-effort adversarial verify** (`b3_verification_report.md`) then found **HIGH-1** — P3's cleared-orders fall-through re-books the incident-class winner at $0/`FAILED` when the cleared read misses (no self-heal, was untested) — so **B3 is NOT cleared for money yet**; a **HIGH-1 fix is in flight** (`b3_high1_fix_commission.md`, carry-forward not `FAILED`). Also surfaced: **HIGH-2** (B3 inseparable from the S222/S223 chain in one uncommitted tree — operator commit-time decision) and **LOW-5** (`data/bethub.db.bak-S222-*` not gitignored). **Next:** triage the HIGH-1 fix → focused re-verify → then the operator supervised live-proof (§4 runbook incl. the §4.4 HIGH-1 negative case), which **clears the B2↔B3 dependency** (B2 fully money-proven). Flags OFF until it passes.

**S224 live finding (the original diagnosis, retained for the record) — sharper than "unproven":** the **match-reconciliation pass** (`workflows/bet_entry/v1/reconciliation.py::run_reconciliation_pass`, the piece that syncs a bet's real matched/unmatched stake from Betfair back into the store) is **built but NOT WIRED into the running app** — `ui/api/main.py` lifespan starts only streaming + the settlement worker (settlement + provisional passes); nothing calls `run_reconciliation_pass`, and the `settlement_worker_cycle` doesn't either. Proven live S224: a lay placed **unmatched** then matched on Betfair stayed `matched_stake=0` in the store (`reconciliation_attempts=0`, `last_reconciled_at=None`) through settlement, and the worker settled it `SETTLED_WON` (correct *result*) with **$0 money** (wrong *value*). **Money-path consequence + B2↔B3 dependency:** the settlement worker faithfully settles whatever stake the store holds, so a stale stake yields a **correct-direction / wrong-value** settle. Direction of harm here is *under*-record (never overpay), but the general risk is any bet that **fills after placement** (unmatched or partial → fuller). **B2 cannot be called fully money-proven until B3 match reconciliation is wired.** A fully-matched-at-placement bet is unaffected (store already holds the right stake). Wiring `run_reconciliation_pass` as a periodic worker (or via the order-stream) is the fix — scope alongside B3.

**B4 — Promo-seed (data, not wiring).**
The promo catalogue is empty live, so promo-prep, the EV column's promo modes, and the credit-in gate have nothing to work with. Needs the catalogue seeded. Blocks the day even though the wiring is proven.

**B5 — Tunnel reliability for Log Past Bet.**
The lookup itself is proven, but it rides the 8400 tunnel to the VPS; tunnel auto-start/health-check is still parked. Harden so the late-entry fallback can't silently 500 mid-day. Smaller than S189 implied.

**B6 — Cutover mechanics + day-one state + fall-back (W16).**
The actual flip: what reference data must exist in v3 at go-live (accounts, books, the seeded promo catalogue), how any live unmatched lays are carried, and a v2↔v3 coexistence/rollback window. Scope once the money-path pieces above are proven.

**B7 — Live monitoring / observability (operational-readiness hardening; pairs with F8, surfaced S224).**
Once the money-path automation (B1 lay placement, B2 auto-settlement) runs *unsupervised* on v3, we need always-on visibility that doesn't depend on a live Claude session watching a Terminal. Three thin pieces: (1) **durable logs** — the app writes to a rotating file by default (today the worker's settlement + verification records only reach the Terminal / a manual `tee`, so they vanish on window-close and can't be reviewed next session without a restart); (2) **a heartbeat/health alarm** — a small always-running check that pings the operator (phone/desktop) *only* on a real fault: app down, worker stopped cycling, or a settlement pass erroring (silence = healthy); this is what replaces a human staring at the screen; (3) **the read-only settlement review-pull** (`settlement_liveproof_plan.md` §5b) — a one-command daily summary grouped by cycle with every `paid_full` flagged, which Claude runs *with* the operator on a schedule. The load-bearing split: cheap always-on infrastructure is the alarm; **Claude is the periodic reviewer on top, not the alarm itself** (a chat watcher is session-bound, can't wake the operator, and burns tokens idling — right for a supervised proving window, wrong as a 24/7 monitor). Not a hard single-day blocker, but wanted before the automated money-path is left running unattended, and it scales to the ~30-account footprint. Operator raised it S224 during the B2 proving window.

---

## Not blockers (so we don't chase them)

- **Operator-manual steps** — account switching, odds-mirroring, the pounce, cover behaviour, win/last self-resolve. Outside the tool; no cutover dependency.
- **Promo scheduling into the tool** — named future-relief, not needed to flip.
- **Analytics layer + placings backfill** — deferred, post-cutover; the placings/capture track is separate from this runway.
- **Placement audit durability (F8)** — hardening, not a day-blocker (but money-path-adjacent — pair with B1).
- **Betfair entry is lay-only (the `HedgeModal`), surfaced S224** — by design it's the Strategy-1 hedge tool, so lay-only is *sufficient* for the Scope-A cutover (the Betfair leg **is** the lay). **NOT a Strategy-1 blocker.** But two tails: (a) the operator wants a **more flexible Betfair entry** (general back *and* lay) — future work, scope as its own piece; (b) it **parks the BACK settlement live-proof** — the worker's BACK mapping is built + unit-tested but can't be exercised live through the tool until a back-entry path exists, so BACK settlement stays *implemented-not-live* (S189 taxonomy), to be proven when the entry flexibility lands.

---

## Cutover scope — RESOLVED (S219)

**Strategy-1 parity is enough to cut over.** The operator confirmed (S219) that Strategy 1 (Safety Net insurance + free-bet conversion) working in v3 is sufficient to flip off v2. Strategy 2 (Price Booster) is **not** a cutover blocker — it continues in v2/elsewhere during the coexistence window and gets mapped into v3 **post-cutover**. Strategy 3/4 are out (aspirational). **Consequence: this Scope-A map IS the cutover scope — no hidden Strategy-2 workstream sits behind the flip.**

## Open questions (operator calls)

1. **Re-confirm interim-worked pieces** — cash/lay-stake prefill, the four non-migrated vps_client surfaces, the broken by-market route: statuses need a quick re-check against their S-interim reports before we trust them on the map.

---

## Recommended sequence to cutover

1. **B2 settlement live-proving** — actionable now; draft the flag-flip + watch plan (I can do this next).
2. **B3 store-writes + credit-in** — lift via live-run checks during normal use.
3. **B1 lay placement** — the big money-path one; careful live-proof plan (+ F8 audit durability).
4. **B4 promo-seed** — scope + seed the catalogue.
5. **B5 tunnel auto-start/health** — harden the late-entry dependency.
6. **B6 cutover mechanics** — scope the flip once the money path is proven.

Data Foundation harvest and the placings/analytics track run in parallel and don't gate this. The pre-W16 Cowork multi-agent go/no-go panel fires once the money-path pieces (B1/B2) are live-proven.
