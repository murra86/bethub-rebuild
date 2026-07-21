# VPS supply-side review brief

**Drafted:** Session 190 (2026-06-25 ACST, DR-021).
**Status:** LOCKED (Session 190, 2026-06-25 ACST). Contract — Code executes against this as-written; surprises become findings, not edits.
**Routing:** Claude Code, single bounded out-of-session session. READ-ONLY.
**Pairs with:** `workflow_integration_audit_brief.md` (S189, the demand-side audit). This brief is the supply-side half.
**Governing DRs:** DR-027 / DR-028 (two-database architecture + the single integration boundary), DR-033 (data-source roles — Betfair operational, Racing API analytical/enrichment), DR-026 (at-log market snapshot).

---

## 1. What this brief is, and is not

**Is:** a read-only, single-session inspection of the VPS `capture.db` to verify — for every read v3's `vps_client` makes against it — that capture.db actually holds that data, in the shape the client was built to expect, fresh and complete enough for v3 to wire against. It produces one report with a per-read fit-for-purpose verdict, the known finish-position gap quantified, and a capture-liveness check.

**Is not:** a fix session. Code measures and verdicts; it does not repair the finish-position gap, does not re-seed, does not restart or reconfigure any VPS service, does not edit v3 code, and does not write to capture.db. Surprises become findings in the report, not blockers chased mid-session. All remediation routes back to operator-Claude triage, not into Code's report.

**Is not:** an analytical-layer build, a demand-side wiring exercise, or a schema migration. It inspects what exists; it changes nothing.

---

## 2. Why this work exists

The S189 pre-cutover live sweep found that "Log Past Bet" has no live data path — v3's `vps_client` reads a local `capture.db` file, but the launcher never provisions it and no capture.db is reachable on the Mac. The S189 workflow-integration audit (demand side) then showed the wider picture: `vps_client` ships eight read methods against capture.db, but only one (the race-lookup) is wired to a live screen, and the whole analytical read surface is dormant on the demand side.

Before any of that demand-side wiring is built — and before the launcher is taught to provision the capture-data link — the operator wants the supply side checked: is the VPS capturing the right data, in the right shape, to wire v3 against at all? This brief answers that. It is the "check what the VPS is dealing before we wire it" step, now aimed by the audit's demand-side map.

It also closes an open thread from S174: the finish-position gap (the nightly results-sync that stopped landing finish positions ~Apr/May 2026). This brief quantifies the gap's current state; it does not fix it (§9).

## 3. Pre-reads

Required, in order:

1. `bethub-v3/contracts/vps_client_contract.md` — the demand contract. The canonical statement of every read `vps_client` makes and the capture.db shape each expects. This is the yardstick.
2. `bethub-v3/clients/vps_client/v1/` — the eight implemented read methods (see §5 for the map). Read the query each method issues against capture.db.
3. `data_sources.md` (rebuild root) — capability + assigned role per source; what lands in which capture.db table.

Reference-only (pull when needed, not required-reads):

- `racing_api_field_catalogue.md`, `external_api_resources.md` — Racing API field/endpoint detail.
- `architecture.md` §A.8 / §A.9 — the cross-DB read tables (the demand contract in architectural form).

## 4. System access

- **VPS:** SSH to `racing-vps` (`root@187.77.183.9`, key `~/.ssh/id_ed25519`). Capture system root: `/home/racing/racing-data-capture/`. The key is passphrase-protected and only usable through the operator's unlocked `ssh-agent` — so this session must run from the operator's logged-in Mac session (where the agent lives), not a bare spawned shell. The `racing-vps` alias auto-forwards local port 8400, which collides harmlessly with the operator's live tunnel; pass `-o ClearAllForwardings=yes` (or connect to `root@187.77.183.9` directly) to silence the bind warning.
- **capture.db:** `/home/racing/racing-data-capture/data/capture.db`. **READ-ONLY.** Open with SQLite read-only URI (`sqlite3 'file:/home/racing/racing-data-capture/data/capture.db?mode=ro'`) or the equivalent Python `sqlite3.connect('file:...?mode=ro', uri=True)`. **Never copy the file** (it is WAL-mode and live; copying risks a torn read and violates the standing DB-read rule). Query the live file in place, read-only.
- **Liveness cross-check:** the capture API health endpoint at `http://localhost:8400/health` (via the operator's running SSH tunnel) returns collector status + last-snapshot timestamps — use it as a corroborating liveness signal alongside direct DB reads.
- **Timestamps:** all time-of-day references in the report in Adelaide local time (ACST/ACDT) per DR-021. capture.db stores UTC; convert on report.

**Step 0 — reachability gate.** First action: confirm SSH shell access works (`ssh racing-vps 'echo ok'`). If SSH auth fails, **STOP** — do not proceed, do not attempt to fix auth, report "blocked: VPS SSH unreachable" as the sole finding and end the session. (Confirmed working at brief-draft time: SSH shell + read-only capture.db access were verified through the operator's `ssh-agent`. The one failure mode to watch is a shell that can't see the agent — a publickey denial at Step 0 means the session isn't running with the agent available, which is the thing to fix; it is not a server-side lockout.)

## 5. Substantive scope — per-read fit-for-purpose

The review walks every `vps_client` read. Each read is graded on two dimensions, then given one verdict:

- **Schema-truth** — does the live capture.db schema still carry the tables/columns the method queries? (If the query can't even run, that's the headline finding for that read.)
- **Data-fitness** — is the data present, fresh, and complete enough for the method's purpose? Measured against a recent bet-relevant window and a known recent race.

**Verdict per read:** `fit` / `fit-with-gap` (works, but a named coverage/freshness shortfall) / `not-fit` (schema mismatch or data absent). Evidence (row counts, coverage %, sample timestamps, a worked example) sits under each verdict.

### §5.1 Schema-truth pass (gates everything below)

Inventory capture.db: table list, and for the tables `vps_client` touches (`runners`, `races`, `betfair_snapshots`, `betfair_historical`, plus any identity/resolution tables), the column set, row counts, and date span. Confirm the live schema matches what each method's query assumes. Any table/column the client queries that is absent or renamed is a `not-fit` headline for the reads that depend on it. Do this first — it explains every downstream verdict.

### §5.2 Near-term reads — DEEP (the pre-cutover consumers)

These feed features the operator needs working at/near cutover. Full fit verdict with worked examples.

- **Race lookup** — `list_meetings`, `list_races`, `resolve_race` (`race_lookup.py`). The reverse human-date/venue/race → Betfair `event_id` + win `market_id` + runner set lookup behind "Log Past Bet". Verify a recent date resolves end-to-end to a real market + runners.
- **Finish results** — `race_results` (`results.py`). Finish positions / result status for a Betfair `market_id`. This is the feed auto-settlement (W6.5) and the insurance-place-trigger evaluation will read. Verify against recent resulted races. **This read intersects the known gap — see §5.4.**
- **Race classification** — `race_metadata` (`race_metadata.py`). Race class / distance / surface / metadata for a Betfair `market_id`. Verify present and populated for recent races.

### §5.3 Analytical reads — LIGHT (post-cutover surfaces)

Present-and-shaped-right pass only; no deep coverage measurement. Flag plainly if a read is `not-fit`, otherwise a one-line "present, shaped as expected".

- **Runner detail** — `race_runners`, `runner_metadata` (`runner_metadata.py`).
- **BSP** — `runner_bsp` (`starting_price.py`). Note the known dead-end of the static `betfair_historical` import (~2026-02-28 per S173) vs live `betfair_snapshots` (BSP / near-far SP) — confirm which the method reads and whether it is current.
- **Price curve** — `race_bracketing` (`bracketing.py`). The market time-series curve used for counterfactual / pre-jump movement.
- **Identity resolution** — `identity_resolve` (`identifier_resolution.py`). The Betfair ↔ Racing API join inside capture.db. Confirm the resolution layer exists and links the two identifier schemes (this is the join every Racing-API-sourced read depends on).

### §5.4 The finish-position gap — QUANTIFY (do not fix)

The S174 diagnosis: finish positions stopped landing for recent races because the nightly `racing-metadata-backfill` sync runs `get_unsynced_dates` (only dates where `subscription_synced_at IS NULL`), so each date syncs once — before results publish — then never re-pulls. Finish positions faded from ~80% (Nov–Feb) to ~0 by May. Quantify the current state:

- `finish_position` (and `result_status`) populated-vs-null rates in `runners`, bucketed by month, across the last ~12 months. Show the fade curve and where it sits now.
- Confirm whether the one-shot-before-results scheduling pattern is still live (inspect `subscription_synced_at` coverage / the backfill service definition read-only; do not change it).
- Whether the data is still backfillable from the Racing API (the gap inside the 12-month AU window; `sync_day` idempotency).

This section is diagnostic only. The actual backfill + nightly-sync FIX is a separate brief (§9, §10).

### §5.5 Capture liveness

Is the VPS capturing *now*, and is each source current:

- Collector active; the Racing-API subscription sync and the soft-book/Betfair scrapers running.
- Latest snapshot timestamps per source (Betfair, bookmaker, Racing-API subscription) — freshness in plain ACST terms.
- **Resolve the timestamp-semantics oddity:** the `/health` Betfair-last-snapshot stamp read ~90 min ahead of wall-clock at draft time. Determine whether the collector stamps capture wall-time or market-start time, so "freshness" is read correctly. This affects how every snapshot timestamp in capture.db should be interpreted.

## 6. Sequencing within session

1. §4 Step 0 — SSH reachability gate (STOP if it fails).
2. §5.1 — schema-truth inventory (gates and explains everything else).
3. §5.2 — near-term deep reads.
4. §5.4 — finish-position gap quantification (sits naturally with the `race_results` read).
5. §5.3 — analytical light reads.
6. §5.5 — capture liveness.

If a cleaner order emerges once the schema is in front of Code, Code may deviate and say so in the report.

## 7. Empirical verification

Each read carries its own success/failure evidence, captured both as the headline number and as a worked example:

- **Near-term reads:** a known recent bet-relevant race resolves end-to-end (date/venue/race → market + runners → result + classification), plus coverage % over a recent window (e.g. last 30 days) for the result/metadata reads.
- **Finish-position gap:** the month-bucketed populated-vs-null curve, with the current-month figure stated plainly.
- **Analytical reads:** the method's query runs against a real `market_id` and returns a non-empty, correctly-shaped result (light pass — existence + shape, not coverage).
- **Liveness:** latest-snapshot timestamps per source, stated in ACST, with the wall-time-vs-market-time semantics resolved.

A read with no recent data to test against is itself a finding (`fit-with-gap` or `not-fit` with the reason), not a silent skip.

## 8. Output spec

Single report: `vps_supply_review.md` at the rebuild root.

Structure:
1. Run header — timestamp (ACST), SSH reachability result, capture.db path + size + WAL state.
2. §5.1 schema-truth table — tables/columns/row-counts/date-spans for the touched tables.
3. Per-read fit table — one row per `vps_client` read: tier, verdict (`fit` / `fit-with-gap` / `not-fit`), evidence pointer.
4. Finish-position gap — the quantified fade curve + current state + backfillability confirmation.
5. Capture liveness — per-source freshness + the timestamp-semantics resolution.
6. Self-assessment — anything Code could not test, and why.

Length: ~150–220 lines. Tables-with-evidence, not prose essays.

**The report does NOT contain:** remediation, fix proposals, a backfill plan, schema-change recommendations, demand-side wiring design, or an overall go/no-go verdict on cutover. It states what is, per read. Routing is operator-Claude's job next session.

## 9. Hard limits — what's NOT in scope

Non-negotiable. Code is forbidden from:

- **Any write to capture.db.** Read-only URI (`mode=ro`) only. No INSERT/UPDATE/DELETE, no schema change, no VACUUM, no migration.
- **Copying capture.db.** Query the live WAL file in place, read-only. Never `cp`/`scp`/dump the file.
- **Touching any VPS service.** No restart, no reconfigure, no edit to the backfill service, scrapers, subscription sync, or cron. The one-shot-sync scheduling pattern is inspected read-only, never changed.
- **Fixing the finish-position gap.** Quantify only. The backfill + nightly-sync FIX is a separate brief (the parking-lot "Racing-API placings backfill + nightly results-sync fix" item).
- **Editing v3 code.** This is a supply-side inspection; no `bethub-v3` edits, no `vps_client` changes.
- **Fixing SSH / auth.** If access fails, STOP and report (§4 Step 0). Do not modify `authorized_keys`, keys, or sshd config.
- **Demand-side wiring or analytical-layer build.** Out of scope entirely.
- **Continuing past a single bounded session.** If the work doesn't fit, that's a finding ("partial review, here's what's covered"), not a continuation. Partial-but-coherent beats complete-but-lost-coherence.

No git operations on the VPS (the capture repo may have a dirty tree — leave it untouched; read-only inspection only).

## 10. What happens after Code's session

The next operator-Claude (Chat) session triages `vps_supply_review.md`:

- Reads the per-read fit table → produces the operator digest (what the VPS can/can't feed, plainly).
- Routes the **finish-position backfill + nightly-sync fix** as its own Code brief (informed by this review's quantification).
- Feeds the launcher brief's **capture-data provisioning** scope (how v3 reaches capture.db live) with the confirmed path/shape.
- Informs which demand-side `vps_client` reads are safe to wire pre-cutover vs. which wait on a supply fix.

Code does not write any of those follow-on briefs. Each follows from this report, next session.

## 11. Cross-references

- **Pairs with:** `workflow_integration_audit_brief.md` + `workflow_integration_audit.md` (S189 demand side).
- **DRs:** DR-027 / DR-028 (two-database architecture + single integration boundary — this review reads the analytical store, introduces no new integration point), DR-033 (data-source roles), DR-026 (at-log snapshot).
- **Demand contract:** `bethub-v3/contracts/vps_client_contract.md`; `architecture.md` §A.8 / §A.9.
- **Supply reference:** `data_sources.md`; `racing_api_field_catalogue.md`; `external_api_resources.md`.
- **Prior finding:** S174 finish-position diagnosis (the nightly one-shot-sync bug).
- **Excludes (parking-lot):** the placings backfill + nightly-sync FIX (own brief); the launcher capture-data provisioning (launcher brief); all demand-side wiring.

---

*End of brief. Single bounded read-only Code session. Surprises become findings, not blockers. Remediation routes to operator-Claude triage.*
