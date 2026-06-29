# DR-029 §2.1 follow-up — VPS analytical pipeline source-code review brief

**Drafted:** Session 33, 2026-04-30 ACST.
**Hand-off target:** Claude Code, single bounded session, out-of-session execution.
**Output target:** `dr029/2_1_race_data/source_review_report.md`.
**Read-by:** Session 34 operator-Claude, to make the surgical-fix-vs-rebuild call against Cluster 1's three candidate routings.

---

## 1. What this is and isn't

This is a **read-only source-code review** of the VPS racing-data-capture pipeline at `/home/racing/racing-data-capture/` on the VPS (`root@187.77.183.9`). It is the follow-up to the §2.1 inspection report (`dr029/2_1_race_data/inspection_report.md`) — the inspection measured what's *in* `capture.db`; this review reads the code that produces it.

The purpose is to feed the surgical-fix-vs-rebuild call deferred from Session 32 (Cluster 1). Session 32 recorded three candidate routings:

1. **Surgical fix** — wire calibration's resolution path back to `runners.finish_position`; expose `daily_calibration_summary` as canonical settlement-result source via `vps_client`; backfill `betfair_selection_id` onto pre-floor runners where tractable. Forward-routed across §2.4 / §2.6 / §2.10.
2. **Reframe remaining DR-029 scope as designing replacement analytical line** — middle ground; uses inspection findings to size the rebuild rather than committing sight-unseen.
3. **Full ground-up rebuild as own arc, separate from DR-029** — DR-029 closes with current state documented as known-insufficient; rebuild arc opens fresh.

The review is to inform that call, not to make it. Session 34 makes the call.

**Not in scope:**

- No fixes attempted, no code changes written, no refactors proposed.
- No remediation plans, no PR drafts.
- No running of the existing pipeline beyond what's already running.
- No DB writes against `capture.db` (read-only access only, consistent with the original §2.1 brief discipline).
- No external-API documentation reading (Betfair API docs, Racing API docs) beyond what's reachable in code comments.

**Discipline parallel.** The §2.1 inspection brief's discipline was *measure-only, no thresholds, no remediation*. This brief inherits the same shape: **read-only, observation-only, no remediation**. Findings are what the code does and how it's structured, with effort-to-fix as a small fixed scale and risk-to-fix as a qualitative call. No proposals.

---

## 2. Pre-reads (Code, in order)

1. `dr029/2_1_race_data/inspection_report.md` — full. The empirical evidence this review investigates the source of.
2. `dr029/2_1_race_data/brief.md` — original §2.1 inspection brief, for measurement-discipline framing this review inherits.
3. `dr029/dr029_scope.md` §1.2 (two-direct-lines architecture) and §2.1 (the scope item this review supports).
4. `work_in_progress.md` — orientation only; the open-questions section names the three candidate routings Session 34 will weigh against.

These are the only required reads. The review does not need to re-read the schema or re-run the inspection queries — those are documented in the inspection report.

---

## 3. VPS access

SSH to `root@187.77.183.9` with key-based auth (the same path the original §2.1 inspection used, distinct from the macOS launchd tunnel that was the §0.1 hygiene observation). Source tree at `/home/racing/racing-data-capture/`. Read-only file access throughout — no edits, no `git` commits, no service restarts, no DB writes.

If `capture.db` queries are needed to ground a code-reading observation (e.g., to verify a code path's effect against actual rows), they go through `sqlite3 'file:/home/racing/racing-data-capture/data/capture.db?mode=ro'` exactly as in the §2.1 inspection. Probe-not-research — the inspection report covers the substantive measurements.

---

## 4. Source-tree orienting facts (from Session 33 pre-flight)

Captured before drafting so the brief names actual files. These are starting points, not a complete inventory — the review may surface other files that turn out to matter.

**Top-level packages:** `api/`, `betfair/`, `bookmakers/`, `capture/`, `config/`, `matching/`, `scripts/`, `storage/`, `subscription/`. Total ~9.4k LOC of Python plus shell utilities. No tests directory observed.

**Largest files (LOC):**

- `scripts/import_betfair_historical.py` — 1,089
- `capture/orchestrator.py` — 961
- `scripts/health_check.py` — 766
- `storage/database.py` — 719
- `matching/race_matcher.py` — 576
- `subscription/racing_api.py` — 466
- `betfair/client.py` — 380
- `bookmakers/entain.py` — 357
- `scripts/daily_calibration_summary.py` — 298

**Supervision (systemd, no cron):**

- `racing-capture.service` — long-running daemon (`Type=simple`, `Restart=on-failure`), runs `scripts/run_collector.py` which boots `capture/orchestrator.py`. Started daily by `racing-collector-start.timer` at 08:30 Adelaide.
- `racing-api.service` — long-running uvicorn for the local read API at `127.0.0.1:8400`.
- `racing-calibration.service` (`oneshot`) — daily 23:00 Adelaide via timer, runs `scripts/daily_calibration_summary.py`.
- `racing-metadata-backfill.service` (`oneshot`) — daily 23:30 Adelaide via timer, runs `scripts/backfill_race_metadata.py --days 1`. **Currently failing** (PermissionError on log file as of 2026-04-29 14:00 UTC; incidental to this review's questions but flag it in the report so Session 34 has the context).
- `racing-health-check.service` (`oneshot`) — daily 06:00 Adelaide.
- `racing-liveness.service` (`oneshot`) — every 15 minutes.
- `racing-backup.service` (`oneshot`) — daily 05:00 Adelaide.

**Schema migration history:** No formal migration framework observed. Schema lives in `storage/database.py` (`SCHEMA` constant). Three ad-hoc one-shot migration scripts in `scripts/migrate_*.py`. The review should report on what's there; this is one of the §5.5 questions.

---

## 5. Per-area review questions

Five areas, each anchored on a specific inspection-report finding. For each, the review reads the named files (and any others the review surfaces as relevant), and answers the named questions.

### 5.1 Calibration job's result-resolution wiring (Cluster 1, surgical-fix viability)

**Inspection-report anchor:** §H.4. `daily_calibration_summary` is producing `n_winners` daily and continuously through the live-capture window, while `runners.finish_position` is 0% across the same window. The system knows who won; isn't writing it where v3 looks. Cross-tab over the entire `runners` table shows zero rows in 421,651 carry both `finish_position` AND `betfair_selection_id` (§C.2 / §H.1).

**Files to read (starting points):**

- `scripts/daily_calibration_summary.py` (298 LOC) — the calibration job itself.
- `subscription/racing_api.py` (466 LOC) — the Racing API path responsible for `runners.finish_position` writes pre-floor (per its docstring, "post-race sync ... finish positions, margins, winning time").
- `scripts/backfill_subscription.py` (109 LOC) — likely the bulk-historical equivalent of the daily Racing API sync.
- `storage/database.py` — for the writer functions the calibration job and Racing API path call into.

**Questions:**

1. **What is the calibration job's result-resolution path?** Specifically: how does it determine `n_winners` for a given date? What sources does it consult, what fields does it read from `betfair_snapshots` / `runners` / elsewhere, and where are the resolved winner identities held during the run?
2. **Is the resolved winner data written back to any table?** If yes, which fields where. If no, is it derived in-memory and discarded after `n_winners` is summed.
3. **How cleanly could this resolution path be wired to write `runners.finish_position` (and `betfair_selection_id` where missing)?** Effort scale (trivial / small / medium / large / structural-rework). Specifically: is the resolved winner data already keyed in a way that `runners` rows can be matched to it (race_id + selection_id or similar), or would the wiring need additional matching logic?
4. **Is the calibration job idempotent and rerunnable** (per its docstring "INSERT OR REPLACE")? Would back-population of `runners.finish_position` for the existing live-capture window be a single batch run, or does it need per-date re-execution?
5. **Are there other places in the codebase** that resolve race results in a way that could be wired similarly, OR places that already attempt to write `runners.finish_position` and silently fail / get skipped?

The Cluster 1 surgical-fix viability call rests primarily on these answers.

### 5.2 Betfair scrape's intensive-mode trigger and market-discovery logic (Cluster 2 56% finding)

**Inspection-report anchor:** §E.3 — 56% of AU thoroughbred 30d races have no pre-30min Betfair snapshot of any kind. §E.5 — pre-jump intensive p50 is 90-97s vs documented 60s, and gap-rate at 2× documented is 22-39%.

This subsumes the small Code probe Session 32 commissioned for Cluster 2. Treat the 56% diagnostic question as part of this review, not a parallel item.

**Files to read (starting points):**

- `capture/orchestrator.py` (961 LOC) — main loop, market discovery loop. Per docstring: "ticks every 30 seconds. Discovery every 30 minutes."
- `capture/scheduler.py` (272 LOC) — per-race state machine PENDING → CAPTURING (STANDARD → INTENSIVE → POST_START) → SETTLEMENT.
- `betfair/client.py` (380 LOC) — Betfair API wrapper, `MarketSnapshot` / `MarketStatus` / `RunnerData` types.
- `config/settings.py` (138 LOC) — cadence constants. Pre-flight observed: `MAIN_LOOP_TICK=30`, `DISCOVERY_INTERVAL=1800` (30 min), `STANDARD_CAPTURE_WINDOW=60` (start at T-60min), `INTENSIVE_WINDOW=5` (switch at T-5min), `STANDARD_POLL_INTERVAL=300`, `INTENSIVE_POLL_INTERVAL=60`.

**Questions:**

1. **What triggers a race entering CAPTURING state from PENDING?** Specifically: how does a race become known to the orchestrator at all (Racing API discovery, Betfair market catalogue discovery, bookmaker discovery, some merge)? What is the latest a race can be discovered relative to its scheduled jump and still get a pre-30min snapshot?
2. **The 56% no-pre-30min finding — most likely root cause from the code's shape:** is it (a) market-discovery gap (the orchestrator does not see those markets in time — discovery cadence too coarse, or those markets aren't in the discovery query), (b) per-race scheduling gap (the race is known but never enters CAPTURING for some reason — predicate fails, state stuck in PENDING), (c) per-race scheduling gap of a different kind (race enters CAPTURING but the first pre-30min poll lands after T-30 due to phase-transition timing), (d) structural pattern (specific venues / times / market types that the discovery path systematically misses), or (e) something else entirely. The answer is whichever the code most plausibly produces; if uncertain between two, name both with the diagnostic that would distinguish them.
3. **Intensive-mode poll cadence:** `config/settings.py` declares `INTENSIVE_POLL_INTERVAL=60` but measured p50 is 90-97s. What in the orchestrator / scheduler code most plausibly produces that 50% slip? Candidates to consider include: main-loop tick granularity (30s tick can't enforce a 60s interval cleanly), per-source serialised polling (one source's slow response delays all polling), batch-size constraints in `betfair/client.py`, rate-limit handling, but the answer is whichever the code shows.
4. **Discovery interval (30 min)** — does the orchestrator re-discover Betfair markets every 30 minutes for races already in CAPTURING, or only for new-race discovery? If new-race-discovery only, what's the smallest gap between a race being created in Betfair's catalogue and the orchestrator picking it up?
5. **Are there any race-type / venue-type / market-type filters** in the discovery or capture path that would systematically exclude a specific subset of AU thoroughbred races (e.g., trials, jump-outs, low-stakes meetings)?

### 5.3 Snapshot writer for BSP / sp_near / sp_far (Cluster 4 high-value pipeline-write-back)

**Inspection-report anchor:** §E.2 — `bsp_price`, `sp_near_price`, `sp_far_price` columns 0.000% populated across 1,629,309 snapshots, despite Betfair Streaming exposing the values. §H source-exposes-but-pipeline-doesn't-write observation.

**Files to read (starting points):**

- `storage/database.py` (719 LOC) — the snapshot-write functions. The schema as it lives in code.
- `betfair/client.py` (380 LOC) — what's pulled from Betfair in `MarketSnapshot` / `RunnerData`.
- `betfair/models.py` (112 LOC) — the data-class shapes.
- `capture/orchestrator.py` — where snapshots are assembled before write.

**Questions:**

1. **Are the BSP / sp_near / sp_far fields read from Betfair at all?** Specifically: does `betfair/client.py` request these projections (`SP_AVAILABLE`, `SP_TRADED` projection flags or equivalent), and do the resulting `MarketSnapshot` / `RunnerData` objects carry the values?
2. **If the values are read but not written:** where does the data drop on the floor — at the orchestrator's pre-write assembly stage, at the `storage/database.py` writer's INSERT statement, or somewhere else?
3. **If the values are not read:** what would it take to start reading them — is it a price-projection flag change in `betfair/client.py`, or a structural change to which Betfair API endpoint is called, or are these only available via the Streaming API which isn't currently used?
4. **For BSP specifically:** Betfair publishes BSP only after market suspension. Does the post-jump capture path (`POST_START` phase, `SETTLEMENT_POLL_INTERVAL=120`) ever run a final snapshot at a time when BSP would be available, or does the SETTLEMENT phase only check `market_status` and never re-poll prices? If a final-with-BSP snapshot would require a new code path, name what it would touch.
5. **Effort to start writing the three columns** — small fixed scale. Note any tests this would need to pass that don't currently exist (i.e., test-coverage observations for the writer).

### 5.4 Soft-book scrapers' shape (Cluster 3 follow-up + harness/greyhound 99% non-coverage probe)

**Inspection-report anchor:** §G.1 — seven scrapers, all alive, uniform cadence. §G.3 — AU harness 98.9% zero-coverage, AU greyhound 99.0% zero-coverage in the pre-30min window. Plus pointsbet's 30d-rate / lifetime-rate at 0.77 vs others at 0.97-1.04.

This subsumes the small Code probe Session 31 commissioned for Cluster 3 (harness/greyhound config gap). Treat that question as part of this review.

**Files to read (starting points):**

- `bookmakers/base.py` — shared `BookmakerMeta` / `BookmakerRunner` types and conventions.
- `bookmakers/entain.py` (357 LOC) — Ladbrokes/Neds. The largest scraper.
- `bookmakers/unibet.py` (299 LOC) — second-largest.
- `bookmakers/tabtouch.py` (256 LOC), `bookmakers/playup.py` (206), `bookmakers/sportsbet.py` (188), `bookmakers/pointsbet.py` (179).
- `bookmakers/palmerbet.py` (206 LOC) — Cloudflare-blocked per `data_layer_current.md` §5.1, but read enough to confirm the shape matches and observe what's there in case of relevance.
- `capture/proxy.py` — the Decodo proxy interface, for the pointsbet 0.77 question.

**Questions:**

1. **Are the seven scrapers uniform in structural shape?** Specifically: do all seven follow the `bookmakers/base.py` contract (`(BookmakerMeta, list[BookmakerRunner])` return shape, named `fetch` and `discover` functions), or are there structural deviations? Anything that would make adding an eighth scraper significantly harder than adding a seventh.
2. **Are they well-isolated from each other?** Could one scraper be replaced or removed without touching others. Are there shared mutable state surfaces that would surprise an editor.
3. **Harness/greyhound 99% non-coverage — config gap or structural?** From the discover/fetch code: do the seven scrapers' URL patterns / API endpoints / discover queries cover harness and greyhound race codes, or do they hit a thoroughbred-only endpoint per book? If the URL patterns are AU-thoroughbred-only by construction, name what it would take to extend coverage. If the patterns are code-agnostic but the actual discovery results don't include those codes, that's the structural / books-don't-expose-them answer.
4. **PointsBet 0.77 deviation diagnosis:** from `bookmakers/pointsbet.py` and `capture/proxy.py`, is there anything that suggests rate-limiting, proxy issue, or a recently-introduced code path that could explain the 23% drop in 30d-rate vs lifetime-rate? Specifically — is PointsBet routed through Decodo differently from the others, does it have a distinct retry / backoff pattern, are there error-handling branches that silently skip a fraction of races?
5. **Is `capture/proxy.py` doing what its name suggests** (Decodo rotating residential proxy interface), and which scrapers route through it vs which call upstream APIs directly? This feeds the WIP §15 Decodo review parking-lot item; the question here is bounded to "what does the code show" not "is the configuration right."

### 5.5 Supervision config and code-health overall

**Inspection-report anchor:** none directly; this is the "is this a wiring fix or a structural problem" framing question that the surgical-fix-vs-rebuild call rests on.

**Files to read (starting points):**

- `scripts/run_collector.py` (120 LOC) — the orchestrator entry point.
- `scripts/health_check.py` (766 LOC) — flag the size; this is large for a "health check" by name. Read enough to understand its actual scope.
- `scripts/liveness_check.py` (265 LOC) — the every-15-min check.
- `scripts/migrate_*.py` (three migration scripts, 117 / 140 / 149 LOC).
- `config/settings.py` — full read; small enough.
- `storage/database.py` — schema management, init, and migration patterns.
- The systemd unit files inventoried in §4 above (already pre-flighted; full inventory in the review report's overall section).

**Questions:**

1. **Schema-management discipline.** Is there a migration framework (Alembic, raw SQL files, custom), or is schema evolution ad-hoc per the three `scripts/migrate_*.py` files. How does code know what schema version `capture.db` is at — is there a `schema_version` table, an in-code constant, or implicit "the schema is whatever the running code expects."
2. **Code-cleanliness read.** Is the pipeline a series of small focused scripts with clean module boundaries, a monolith with most of the logic in `capture/orchestrator.py`, or somewhere in between? Does `capture/orchestrator.py`'s 961-LOC docstring claim ("single main loop coordinating Betfair market discovery + price capture, multi-bookmaker race discovery + odds capture, cross-source race/runner matching, settlement detection, coverage tracking") match the actual structure or is the file effectively several concerns interleaved.
3. **Test coverage.** Is there a tests directory, are there inline tests, or is the pipeline tested only via observed live behaviour. Note: not "is there enough testing" — just "what's there."
4. **Logging discipline.** Is logging structured (json, key=value) or freeform; centralised or per-module; does the failure mode of the metadata-backfill service (PermissionError on log file) suggest a class of log-handling fragility or just an isolated path issue.
5. **Overall read.** Does fixing the issues surfaced in §5.1–5.4 look like:
   - **Wiring fixes against existing infrastructure** — small additions to existing code paths, no structural rework needed (consistent with surgical-fix routing).
   - **Targeted rework of specific components** — the calibration → `runners` write-back is a structural addition, the 56% finding requires a new discovery path, the BSP write needs new code, but the rest holds (consistent with reframe-as-replacement-design routing).
   - **Underlying structural issues** that mean each individual fix requires touching the orchestrator's main loop or the storage layer in load-bearing ways (consistent with full-rebuild routing).

These are the "weight class" inputs Session 34 needs. The answer to the overall read is not a vote between the three routings — that's Session 34's call. It's a characterisation that lets Session 34 weigh the routings against grounded evidence.

---

## 6. Output format

Output file: `dr029/2_1_race_data/source_review_report.md`. Operator-Claude reads this in Session 34.

**Structure:**

1. **Per-area assessment** (§5.1 through §5.5, in order). For each:
   - **What was found** — bullet-pointed observations grounded in named files and line ranges where useful.
   - **Effort to fix** on the small fixed scale: **trivial / small / medium / large / structural-rework**. Trivial = config change or one-line addition. Small = bounded change to one module, fits in a single small PR. Medium = changes across two or three modules with some test surface. Large = significant rework of an existing module. Structural-rework = the change requires re-thinking how the pipeline composes its concerns. One word per area.
   - **Risk to fix** — qualitative call. What's the regression risk against existing-and-working pipeline behaviour. Is dual-running needed (run new path alongside old, compare). Are there silent-failure modes the change needs to defend against.
   - **What depends on it** — which downstream §5.x findings rest on this one resolving first, if any.
2. **Overall read** — Code's recommendation between the three Cluster 1 routings (or a fourth if the source-code review surfaces one the operator-Claude triage didn't anticipate). Recommendation is from Code's vantage, not binding — Session 34 makes the call. Anchored in concrete evidence from §5, not abstract preference.
3. **Anything surprising** — short section. Things observed during the review that don't fit cleanly into §5.1–5.5 but the operator should know. The §2.1 inspection report's §H is a precedent; do likewise here.
4. **Self-assessment of review completeness** — what was looked at, what wasn't, where the review hit its time budget. Important for §7 below.

**Length guidance:** the §2.1 inspection report was 822 lines, density-shaped by the empirical measurement battery. This report should run lighter — probably 300-500 lines. The substance is structured-observation-and-judgement-call, not raw measurement. If the report is approaching 800+ lines, that's a signal something has slipped from observation into proposal.

---

## 7. Hard limit on session length

The review fits in **one Code session**. If it surfaces that any one area in §5 needs more depth than fits, **Code surfaces that as a finding rather than continuing past budget**. Specifically: name the area, name what's been observed so far, name what remains, name an estimate of further effort. Session 34 either commissions a follow-up review (bounded scope) or makes the surgical-fix-vs-rebuild call with what's available.

The surgical-fix-vs-rebuild call **does not require complete information** — it requires enough to weigh the three routings against grounded evidence rather than instinct. A partial review with clean per-area judgements on the questions that were reachable is more useful than a complete review that stretched past budget and lost coherence.

---

## 8. Discipline notes

- **Read-only.** No fixes attempted, no code changes written, no service restarts, no DB writes.
- **Observation, not proposal.** The report describes what's there and characterises effort and risk on the small fixed scales. It does not propose a remediation plan. Session 34 makes the routing call; subsequent execution sessions design any remediation.
- **Named-file-and-line-range grounding.** Where a finding rests on specific code, name the file and a line range. This lets Session 34's read be auditable, and lets future Code sessions start from concrete pointers if a routing decision goes to surgical fix.
- **No external API documentation reading** beyond what's reachable in code comments. The Betfair API and Racing API field-inventory question is §2.10 of the wider DR-029 scope and is not pursued here.
- **No run of the existing pipeline beyond what's already running.** No starting/stopping services, no triggering manual capture runs, no calling the local API at `127.0.0.1:8400` for diagnostics (unless a specific question requires it; if so, name it).
- **Time-anchor your work.** The review is a Code session; if any timestamp matters in the report (e.g., "as of [timestamp] the X service was in Y state"), use real Adelaide local time per DR-021.

---

## 9. What happens after

1. **Out-of-session execution by Claude Code** against this brief. Code reads the pre-reads, executes against §5.1–5.5, produces `source_review_report.md` per §6.
2. **Session 34 (Chat)** opens with this brief and the report as required reads. Operator-Claude makes the surgical-fix-vs-rebuild call, weighing Cluster 1's three candidate routings against the evidence in the report.
3. **Whichever routing wins,** §2.1 close shape and the framing of remaining DR-029 scope items (§2.4, §2.5, §2.6, §2.10) follow from the call. Surgical-fix path proceeds per `dr029_scope.md` §5 sequencing; reframe-as-replacement-design and full-rebuild paths reshape the remaining scope accordingly.

---

*End of brief.*
