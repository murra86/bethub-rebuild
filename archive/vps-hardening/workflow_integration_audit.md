# Workflow-map integration audit

**Run:** Session 189 Code session, 2026-06-25 18:41 ACST (Adelaide, DR-021). READ-ONLY throughout.
**Source map:** operator_workflow_map.md (S185, Scope A — Strategy 1 insurance + free-bet conversion).
**Brief:** workflow_integration_audit_brief.md (S189).
**Method note:** Each tool-touching activity graded on two dimensions — **code-wiring** (does the real v3 path call a real external client, or a stub/fixture/TODO) and **launch provisioning** (does the live launch supply what that client needs). Status = the *worse* of the two per the §5.4 decision table; `live-proven` additionally requires evidence from the §5.4a hierarchy (tier in the hand-off note). External systems in scope: Betfair live (`betfair_client`), VPS capture (`vps_client` → `capture.db`), operational store (`bethub.db`).

**System state captured (provisioning evidence):**
- Live process: `uvicorn ui.api.main:app` PID 31279 on 127.0.0.1:8787 (`ps eww`).
- Live env vars present: `BETHUB_BETFAIR_MODE=live`, `BETHUB_BETFAIR_CREDENTIALS_PATH=/Users/tim/Desktop/Projects/bethub-secrets/betfair.json` (file exists, 110 bytes). **Absent:** `BETHUB_CAPTURE_DB_PATH`, `BETHUB_DB_PATH`, `BETHUB_DB_URL`.
- Launcher `BetHub.command:75-78` exports `BETHUB_BETFAIR_MODE` + (live-only) `BETHUB_BETFAIR_CREDENTIALS_PATH`; it sets **no** capture-db path and **no** operational-db path.
- Operational DB present at default fallback `bethub-v3/data/bethub.db` (217 KB) — `resolve_db_path` `composition.py:381-407`.
- **`capture.db` is not present anywhere on disk** (`find` over Projects → none). `Settings` carries no capture-db field at all (`config.py`).
- Live GET probes (read-only, 2026-06-25 ~18:24 ACST) used as evidence — see table + §"what the method confirmed".

---

## Per-activity table

Map ref key: §3 = insurance back-bet loop; §4 = conversion loop; §5 = cross-cutting layers; §6 = named manual re-entry points.

| Activity | Map ref | System underneath | Code anchor | Code-wiring | Provisioning | Status | Reason | Hand-off note |
|---|---|---|---|---|---|---|---|---|
| Switch into the account | §3 | AdsPower + router + MacBook | — | n/a (outside tool) | n/a | operator-manual | — | Hard serial gate; no tool integration exists or is intended. |
| Promo prep (set EV mode) | §3 / §5 | Bet tool race page (promo catalogue) | `promos.py:120` `list_promo_catalogue` → `PromoStoreAdapter` (bethub.db); mode-select is frontend | real client (store) | provisioned (default db) | live-proven | — | Tier 3 — `GET /v1/promos/catalogue` → 200. **But catalogue is empty (`[]`) live**: no promo rows seeded, so promo-mode prep has nothing to select (data-seeding gap, see drift D4). |
| Read + monitor market — Betfair price feed | §3 / §6 | Soft book + bet tool | `racing.py:690` prices, `racing.py:701` catalogue → `betfair_client` | real client (Betfair) | provisioned (mode=live, creds present) | live-proven | — | Tier 3 — live prices for market `1.259422667` (9 runners), catalogue runner names returned. |
| Read + monitor market — odds-mirroring | §3 / §6 | Soft book (hand-keyed into tool) | — | n/a (operator hand-entry) | n/a | operator-manual | — | The hidden risk surface (map signal 3). Operator types soft-book odds; the Betfair column beside it is live-proven (row above). |
| Pounce — place the back | §3 | Soft book (bookmaker site) | — | n/a (outside tool) | n/a | operator-manual | — | Placed on the soft bookmaker; never touches v3. |
| Cover behaviour | §3 / §5 | Account-health layer | — | n/a (outside tool) | n/a | operator-manual | — | Browsing/site activity; no tool path. |
| Log the bet (soft-book) | §3 / §6 | Bet tool | `racing.py:859` `log_bet` → `orchestrator.log_soft_book_bet` (`orchestrator.py:1142`) → store write | real client (store) | provisioned (default db) | implemented-not-live | {evidence-absent} | Pure store write, no Betfair call (confirmed). Store **read** path live-proven (tier 1); a live **write** cannot be exercised under read-only limits and existing rows can't be attributed to this endpoint. Very likely operational — needs one live-run check. |
| Switch out → next move | §3 | AdsPower + router | — | n/a (outside tool) | n/a | operator-manual | — | Returns to routing decision. |
| Mark bet triggered (the hinge) | §4 | Bet tool (bet log) → credit FB | `promos.py:186` `credit_in` → `record_free_bet_credit` (bethub.db) | real client (store) | provisioned (default db) | implemented-not-live | {evidence-absent} | The cross-cycle hinge. Real gated store write (safety_net + settled_lost + promo attached). Same evidence limit as other writes; read side of store is live-proven. |
| Switch back into the account | §4 | AdsPower + router | — | n/a (outside tool) | n/a | operator-manual | — | Pays the gate again. |
| Find a good price (EV conversion mode) | §4 / §5 | Soft book + bet tool | EV column = frontend; inputs `racing.py:690` (Betfair) + `promos.py:120` (catalogue) | real client (Betfair) for price input | provisioned | live-proven | — | Tier 3 on the Betfair price input. The "good price" read itself is operator judgement at the soft book (operator-manual); the tool surface feeding it is live. |
| Place the free bet at the soft book | §4 | Soft book (bookmaker site) | — | n/a (outside tool) | n/a | operator-manual | — | Soft-book placement; outside v3. |
| Lay the same runner | §4 | Bet tool → Betfair modal | `racing.py:1014` `place_lay` → `place_bet` (`betfair_adapter.py:181`) | real client (Betfair) | provisioned (mode=live, creds present) | implemented-not-live | {evidence-absent} | Real placement surface; placement is a write I must not exercise (§9). Read path proves auth/transport work, but the §13.1 interlock needs a *genuine* SUBSCRIBED stream (`main.py:46-85`) whose state is unobservable read-only. No live placement evidence available within limits. |
| EV column (mode-selected) | §5 | Bet tool race page | Frontend derivation; no server EV endpoint (confirmed); inputs = Betfair prices + promo catalogue | derived in UI (no external client of its own) | inputs provisioned | live-proven | — | Tier 3 via its Betfair price input; promo-mode arithmetic also needs catalogue rows, currently empty (drift D4). Load-bearing surface (map signal 4) — correctness not in audit scope. |
| Settlement checking — auto (mark-triggered/settlement) | §5 | Bet tool / settlement worker | `settlement.py:698` `run_settlement_pass` (reads `betfair_client.market_settlement`) | real client (Betfair) **but never invoked** | no live trigger | not-wired | — | `run_settlement_pass` has **no caller** in app/ops/scripts — no worker, cron, or endpoint runs it. The automated half of "open cycles held by the tool" (map signal 2) does not execute live. Also drift D1 (reads Betfair, not `vps_client`). |
| Settlement checking — manual resolve | §5 | Bet tool (burst review) | `provisional.py:321` `resolve_provisional_bet` → `apply_manual_operator_resolution` (store) | real client (store) | provisioned (default db) | implemented-not-live | {evidence-absent} | Manual PROVISIONAL→terminal path. Queue read live-proven (tier 1, `GET /v1/bets/provisional` → `[]`). With no auto-settlement worker, nothing populates PROVISIONAL, so this path has no live input today. |
| Settlement checking — win/last self-resolve | §5 | Operator glance at result | — | n/a (outside tool) | n/a | operator-manual | — | Wins / last-place settle on a glance per the map. |
| Account-health behaviours | §5 | AdsPower fingerprint + router; cover browsing | — | n/a (outside tool) | n/a | operator-manual | — | Per-account isolation, cover browsing, different-runners spread — all operator-side. Account/book **registry** (`accounts.py`, store) is supporting reference data, not a betting-loop activity. |
| Promo scheduling | §5 / §6 | Operator's head | — | no code path | n/a | not-wired | — | Named by operator as a thing to move into the tool; no code exists. |
| End-of-day cleanup | §5 | — | — | n/a (no formal close) | n/a | operator-manual | — | Day trails off; deliberate use-all-free-bets pass is operator-driven. |
| Odds-mirroring (pre-bet) | §6 | Soft book → race page column | — | n/a (operator hand-entry) | n/a | operator-manual | — | Same as the §3 odds-mirroring row; listed as a named re-entry point. |
| Log Bet (post-bet) | §6 | Bet tool | `racing.py:859` (as "Log the bet") | real client (store) | provisioned | implemented-not-live | {evidence-absent} | Same endpoint/verdict as "Log the bet (soft-book)" above. |
| **Late-entry fallback — Log Past Bet (race-lookup)** | §6 | Bet tool → `capture.db` via `vps_client` | `bets.py:925/938/952` lookup endpoints + `bets.py:1003` `create_manual_bet` → `resolve_race` (`vps_client`); path from `bets.py:98-107` `get_capture_db_path` = `os.environ["BETHUB_CAPTURE_DB_PATH"]`; resolver `_connection.py:29-38` | real client (`vps_client`/capture.db) | **not provided** (no `BETHUB_CAPTURE_DB_PATH`; no `capture.db` on disk) | implemented-not-live | {unprovisioned} | **Known-answer node — independently re-derived.** Demonstrated live: `GET /v1/bets/lookup/meetings?race_date=2026-06-20` → **HTTP 500** (`vps_client: capture.db path not set`). The cascading picker and the server-side re-resolve in `POST /v1/bets` both block, so the entire after-the-fact entry flow is non-operational live. |

---

## Map-drift section

Built code vs operator map / architecture.md:

- **D1 — Auto-settlement reads Betfair, not `vps_client`.** architecture.md §A.6 / §A.8 / the DR-019 cross-DB table specify auto-settlement (W6.5) reading `vps_client.get_race_result(betfair_market_id)` for finish position / race result. The shipped `settlement.py` resolves *only* from `betfair_client.market_settlement` (§9.2); `vps_client` is never called for settlement. The architectural "capture.db is canonical for what happened in the race" line is not realised in the settlement path.
- **D2 — No live settlement worker.** `run_settlement_pass` (`settlement.py:698`) exists and is tested but has **no invocation** anywhere in `ui/`, `ops/`, or `scripts/` (ops/ holds only `__init__.py`; no cron/scheduler/background task). The map's settlement/"open-cycles-held-by-the-tool" automation does not run live; only manual resolve + credit-in are live write paths.
- **D3 — `vps_client` is wired at exactly one consumer.** The only v3 consumer of `vps_client` is the §9.7 race-lookup surface in `bets.py`. The broader cross-DB analytical reads architecture.md §A.9 envisions (race classification, finish position, market curve / bracketing, BSP, identity-resolution on bets) are **not wired into any live demand-side path**. The entire analytical cross-DB read surface is dormant on the demand side (independent of the supply-side VPS review, which is out of scope here).
- **D4 — Promo catalogue empty live.** `GET /v1/promos/catalogue` returns `[]`. Promo prep, the EV column's promo modes, and the credit-in gate all depend on catalogue rows; none are seeded in the live `bethub.db`. A data-seeding gap, not a wiring gap — flagged so it isn't read as "promo prep works end-to-end".
- **D5 — Placement audit sink is in-memory.** `composition.py:529-534` wires `MemoryAuditLogSink` for the `place_bet` audit trail (contract §12). Placement audit entries are not durably persisted live (the bet-*mutation* audit log for create/edit/delete/credit, by contrast, persists to `bethub.db`). Noted; not a map activity.

No drift found between the map and code for the exchange-leg shape: the map shows the lay as the only exchange leg (§4), and `place_lay` is the only Betfair write surface.

---

## What the method confirmed

- **The two-dimension method works and caught the systemic gap by construction.** Every real client was graded for provisioning independently of its code path, so a real-but-unprovisioned path (race-lookup) and a real-but-unevidenced path (lay placement, store writes) land in distinct buckets from a real-and-live-proven path (Betfair reads).
- **Known-answer calibration — PASS.** The audit independently re-derived **Log Past Bet race-lookup → implemented-not-live {unprovisioned}**, from first principles: real `vps_client.resolve_race`/`list_meetings` code path (`bets.py`), but the launcher and live env set no `BETHUB_CAPTURE_DB_PATH` and no `capture.db` exists on the Mac, so `_connection.py:35` raises. It was also demonstrated live (HTTP 500 on the lookup endpoint while store/Betfair endpoints return real data). The method did not need to be told the answer to reach it.
- **Live-proven verdicts and their evidence tiers:** Betfair racing reads — race list (93 real markets incl. Penrith/Casino), market prices (market `1.259422667`, 9 runners), market catalogue (real runner names) — **tier 3**. Operational store reads — bets feed (real bet `bet-60f74e8c…`, BetFair, $50 @ 2.35, placed 2026-06-25 13:08), accounts ("Tim"), provisional queue, promo catalogue — **tier 1** (live read of the real operational DB through the running app).
- **Where the audit is deliberately conservative:** all operational-store *write* activities (log soft-book bet, mark-triggered/credit-in, edit, delete, manual resolve) and the Betfair *lay placement* are real + provisioned but carry **{evidence-absent}** — under the §9 read-only limit a live write cannot be exercised, and pre-existing rows cannot be attributed to a specific write endpoint. These are the activities a single live-run check would most cheaply lift to live-proven; they are flagged, not assumed.

---

*Scope-A demand-side audit only. No recommendations, fixes, remediation plan, VPS supply-side review, or edits to the operator map are included, per §8. ~160 lines.*
