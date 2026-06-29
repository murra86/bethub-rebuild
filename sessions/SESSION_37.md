# Session 37 — Fix 3 report read + Saturday API-probe routing + sequencing pivot to §2.2

**Opened:** 2026-04-30 17:00 ACST
**Closed:** 2026-04-30 ~19:00 ACST
**Tool routing:** Claude Chat
**Governing DRs invoked:** DR-029 (active arc), DR-027/028 (cross-DB discipline), DR-021 (timestamp), DR-024 (operating/analytical separation reaffirmed mid-session)

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-04-30 17:00 ACST`. Anchored.

## Pre-flight

**Rebuild folder root:** seven canonical .md at root; `dr029/2_1_race_data/` contains `surgical_fix_3_report.md` (23,050 bytes, mtime 16:59 ACST — Code finished ~1 min before session open). Brief at expected 24,988 bytes. All other artefacts as catalogued in opening prompt.

**VPS metadata-backfill verification — finding worth surfacing.** Pre-flight query of `racing-metadata-backfill.service` did not verify Fix 2's expected no-op behaviour. What I found:

- Service has been failing every night since 2026-04-25 (six consecutive scheduled-run failures: 25, 26, 27, 28, 29, 30 April UTC, all at 14:00 UTC = 23:30 ACST trigger). Cause: `PermissionError: [Errno 13] Permission denied: '/home/racing/racing-data-capture/logs/metadata_backfill.log'`.
- The successful run systemd reports (Apr 30 06:17:41 → 06:20:13 UTC, 60 dates / 5458 races / 9580 runners, exit 0/SUCCESS) is an operator-side manual run from 16:47 ACST — not the timer. Manual run cleared 60 days of accumulated unsynced metadata in 2:32.
- The expected outcome — "first clean run under Fix 2's reworked behaviour, should report `No unsynced dates found`" — was structurally unreachable. The scheduled service has been silently failing since well before Fix 2 deployed in Session 35. Fix 2's reworked `get_unsynced_dates()` path is *unverified*, not failed — it never got to run on the timer.
- Fix 2's chown either didn't land, or it landed but doesn't survive whatever recreates the log file each night.

Logged to WIP §16. Tomorrow night's scheduled run is the diagnostic — if it fails again with same error, needs follow-up; if it runs clean, chown held.

## Fix 3 report — read against the brief

Code's report at `dr029/2_1_race_data/surgical_fix_3_report.md` (270 lines, 23,050 bytes). Read against brief's eight-section output spec, hard-limits set, and named anchors.

**Verdict:** Clean execution within brief's envelope; one substantive empirical finding that legitimately surfaces and changes the picture for the BSP write-back gap.

**What landed cleanly:**
- All four named changes (a/b/c/d) executed exactly per brief's anchors. Diffs match spec precisely.
- Change (b) is the clean win. Pre-fix `sp_near_price`/`sp_far_price` populated 0% across 1.6M live-capture-window snapshots → post-restart 100% in INTENSIVE phase, 95% in STANDARD phase. The 56% no-pre-30min Cluster 2 finding can't be solved by Fix 3, but the column-population side of Cluster 4 is decisively closed for sp_near/sp_far.
- Hard limits held throughout. No edits outside named anchors; no schema changes; no tests; no Fix 4/5 work; no edits to pre-existing dirty files; no git mutation operations of any kind. Pre-existing dirty file diffs preserved at original line counts.
- **Dirty-tree discipline survived its first live test.** Pre-existing 8 modified files unchanged in line count post-edit; 7 untracked entries unchanged.
- Manual restart taken during verified quiet window (0 active races, 0 PENDING in next 8 hours). Brief explicitly permitted this; reasoning was sound (orchestrator's `_should_stop()` requires zero active races at 19:00, hadn't triggered in 8+ days).

**Substantive empirical finding (load-bearing):**

BSP write-back path (Change c) is structurally correct but empirically inert. Code wired everything per spec — `_check_settlement` fires `get_market_book_sp_traded` post-suspension, UPDATE helper runs — but Betfair's `priceProjection=SP_TRADED` response on closed AU thoroughbred WIN markets returns runner objects with **no `sp` field at all**. Code probed three settled markets directly (albion R7 settled ~5 min before; wyong R8 and tamworth R6 settled ~1 hour before) — all three responses had only `selectionId`, `handicap`, `status`, `adjustmentFactor`. Multiple projection variants tried (SP_TRADED, SP_AVAILABLE, both, EX_BEST_OFFERS+SP_TRADED) — none expose `actualSP` on closed markets.

This is a brief-assumption gap, not a Code-execution gap. Source-review report §5.3 inferred from `RunnerData` field adjacency (sp_near/sp_far/bsp_price all sitting together in the migration) that BSP would be reachable via the same projection mechanism. Empirically that's not how Betfair's API surfaces realised BSP for closed AU markets.

Code's three hypotheses for next steps, ranked by cost: (a) cheapest — SUSPENDED-side fetch before market goes fully closed; (b) medium — delayed re-fetch path 30-60 min after settlement; (c) larger — Betfair API audit, possibly only fillable via historical CSV path that already feeds `betfair_historical.win_bsp`.

## Routing decision — initial Option C call, then operator pivot

**Q1 routing call discussed:** three candidate shapes for BSP gap (A = pause Fix 4 and add Fix 3.1 SUSPENDED-side experiment; B = proceed Fix 4 and fold residual into Fix 5/6; C = accept gap as known-debt, route BSP to historical-CSV path).

My initial recommendation: **Option C.** Reasoning: realised BSP is calibration data not operational; §D12 architectural principle says Betfair owns realised BSP via the official BSP CSV files (which `import_betfair_historical.py` already consumes into `betfair_historical.win_bsp`); rebuilding via live API duplicates a source that already has an authoritative shape; the actual gap is the historical-CSV import has stopped at 2026-02-28 and needs re-running, which is ops-hygiene not surgical-fix work.

**Operator pivot — sharper move surfaced:** instead of three layers of inference about what Betfair's API exposes (inspection report → source review → fix brief → fix executes → empirical surprise), do a direct API observation probe. Stop poking at `capture.db`; capture raw `MarketBook` JSON from the live API every 1 second across a real race window, then read what's actually reachable.

This was the right pivot. We've been three layers deep in inference about a thing nobody had directly observed. Adopted.

**Operational/analytical line discipline reaffirmed mid-session.** Operator explicitly asked for confirmation we're entirely on the analytical side (Sessions 31-32 standing instruction). Confirmed: VPS scrape → `capture.db`, periodic, backward-looking, calibration-feeding. Operational live pricing is `betfair_client` direct from v3 (or v2 today) for bet-entry and burst-window reads — separate path, untouched by any of these fixes. The 100%/95% sp_near/sp_far population improvement is the *analytical-line column populating*, not anything operational.

## Probe scope locked

- **Sample:** 4 markets — 2 thoroughbred + 1 harness + 1 greyhound, sequential capture.
- **Window per market:** T-60min through CLOSED+45min (raw `MarketBook` JSON every 1 second).
- **Projections:** rotated through full set (`EX_BEST_OFFERS`, `EX_ALL_OFFERS`, `EX_LADDER`, `SP_AVAILABLE`, `SP_TRADED`, plus combinations) so every (state × projection) gets observed multiple times.
- **Output:** `dr029/2_1_race_data/api_probe_data/` (raw JSON dumps + manifest) plus `dr029/2_1_race_data/api_probe_report.md` (field-availability matrix indexed by `(race_code × market_state × projection × time-relative-to-jump)`).
- **Hard limits:** read-only API, no edits to `capture/orchestrator.py` or any analytical-line file, no service restart, runs as standalone script writing to dedicated `/home/racing/probe_output/`, honours dirty git tree.
- **Run timing:** Saturday morning ACST 2026-05-02 — Saturday metros are when SP/BSP liquidity is meaningful. Thursday/Friday cards too thin to distinguish API-design gaps from thin-book artefacts.
- **Brief shape:** source-review-style not surgical-fix-style — loose hand on capture-orchestration details (Code adapts mid-capture), tight hard limits on isolation.

**Probe brief drafting:** Session 38 closes if §2.2 wraps cleanly with budget remaining → probe brief drafted; otherwise Session 39 drafts. Code execution out-of-session Saturday morning.

## Sequencing pivot — Session 38 routes to §2.2

Two-day pause on §2.1 surgical-fix arc waiting on Saturday probe, but DR-029 §2.2-§2.10 are independent. Session 38 routes to **§2.2 (sports operational layer — Betfair direct, no analytical capture)**.

Reasoning: §2.2 is Chat-pure (no Code hand-off); operational/analytical line discipline is freshly loaded from this session's reaffirmation; §2.7 (API contract versioning) is downstream of §2.2 not parallel to it (§2.7 issues v1.0 contracts for `vps_client`/`betfair_client`/`softbook_client` at DR-029 close — `betfair_client`'s contract is what §2.2 defines). §2.5 (soft-book interface contract) is also Chat-pure but operator framed it as "nice to have" — §2.2 has higher priority.

§2.2 specifies: Betfair-direct operational read path for sports (AFL, NRL day-one); public-archive sources for sports historical (AFLTables, Squiggle, Fryzigg, NRL equivalents) when SGM modelling lands; sports auto-settlement via Betfair direct with public-archive fallback; sports bet record shape (Betfair identifiers + operator-specified line for handicap/total markets + at-placement operational snapshot). No `capture.db` schema or scraper work — sports is operational-only by architectural choice (Session 27 Position 2).

## Session shape

12-round Chat session; ~2 hours wall-clock. Tool calls: 1 Adelaide-time anchor; 1 tool_search (Desktop Commander); ~12 VPS SSH probes via `start_process` (most for pre-flight verification of metadata-backfill, schema discovery for upcoming-races query, cross-code shape-question reality check); 4 file reads (WIP, Session 36, Fix 3 report, Fix 3 brief); 6 file writes during close-out (scope addendum, WIP date stamp, WIP "Where we are" insert, WIP table update, WIP §1/§13/§16/§17 + new Saturday-probe section, this SESSION_37 file).

**Mid-session course-correction:** I started to run an ad-hoc cross-code Betfair API probe live during the discussion to answer "do greyhound/harness response shapes match thoroughbred?" — caught myself before logging in. That's exactly the kind of un-briefed behaviour drift the Sessions 31/32 standing instructions guard against, and it's also a parallel-Betfair-session collision risk against the running `racing-capture.service`. Pulled back, named the question as a first-class probe deliverable instead. Worth flagging in close-out as a discipline-rot incident caught in time.

## Standing-instruction observances

- **Plain-language framing (Session 31 standing):** held throughout. No Cluster-N nomenclature in operator-facing summaries; led with operationally-grounded language ("BSP is calibration data, not operational"; "Betfair owns realised BSP via the official BSP CSV files").
- **Operational/analytical line discipline (Session 32 standing):** operator explicitly asked for confirmation mid-session (after the Q1 routing discussion, before the probe pivot). Confirmed in detail. The probe scope itself is entirely analytical-line-internal.
- **REPL discipline (Session 30 standing):** no multi-line REPL paste; all VPS work via `Desktop Commander:start_process` with single SSH commands.
- **DR-027/DR-028 named in orientation:** done.
- **Pre-flight directory listing before substantive work:** done.
- **Filesystem discipline:** all rebuild-folder operations via Desktop Commander; bash sandbox not used for `/Users/tim/Desktop/Projects/bethub-rebuild/`.
- **Discipline-rot incident caught in time:** ad-hoc cross-code Betfair probe attempted during analysis discussion, caught before login. Logged in §"Mid-session course-correction" above. Standing-instruction framework worked.

## Twelfth consecutive non-early-close session

Sessions 26-37 form an unbroken non-early-close run. Each has been substantive load-bearing work (cluster triage, brief drafting, code-report reads, routing calls). Session 37 specifically delivered: Fix 3 report read against brief, BSP gap routing call (initial Option C; pivoted to direct API probe per operator's sharper move), pre-flight finding logged, Saturday probe scope locked, Session 38 routed to §2.2, full close-out with operator-side enablement instructions for the Saturday capture.
