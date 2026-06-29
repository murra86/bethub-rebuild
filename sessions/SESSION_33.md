# Session 33 — VPS analytical pipeline source-code review brief drafted

**Open:** 2026-04-30 13:18 ACST
**Close:** 2026-04-30 13:27 ACST
**Duration:** ~9 min
**Shape:** scope-document drafting; pre-flight-heavy, focused output

## Required reads completed

- `work_in_progress.md` (project state through Session 32 close)
- `sessions/SESSION_32.md` (full Session 32 outcomes — six clusters triaged, rebuild question surfaced)
- `dr029/2_1_race_data/inspection_report.md` (822 lines, full)
- `dr029/dr029_scope.md` §2.1 and §5 sequencing
- Pre-flight directory listing of rebuild folder root — clean (seven canonical .md files, expected directories)

## Pre-flight VPS source-tree probe

Per opening prompt's pre-step (~10 min). SSH to `root@187.77.183.9` for file inventory, line counts, supervision config, head-of-file scan of consequential files. Goal of the pre-step (know which files to name with confidence in the brief) achieved.

**Source tree state captured:**

- ~9.4k LOC Python plus shell utilities. Top-level packages: `api/`, `betfair/`, `bookmakers/`, `capture/`, `config/`, `matching/`, `scripts/`, `storage/`, `subscription/`. No `tests/` directory.
- Largest files: `scripts/import_betfair_historical.py` (1,089 LOC), `capture/orchestrator.py` (961), `scripts/health_check.py` (766), `storage/database.py` (719), `matching/race_matcher.py` (576), `subscription/racing_api.py` (466), `betfair/client.py` (380), `bookmakers/entain.py` (357), `scripts/daily_calibration_summary.py` (298).
- Supervision via systemd (no cron). Eight units: `racing-capture.service` long-running (started daily 08:30 ACST by `racing-collector-start.timer`), `racing-api.service` long-running (uvicorn on `127.0.0.1:8400`), `racing-calibration.service` oneshot daily 23:00 ACST, `racing-metadata-backfill.service` oneshot daily 23:30 ACST, `racing-health-check.service` oneshot daily 06:00 ACST, `racing-liveness.service` oneshot every 15 min, `racing-backup.service` oneshot daily 05:00 ACST, `racing-collector-start.service` oneshot.
- **Schema management:** no migration framework; schema in `storage/database.py` `SCHEMA` constant; three ad-hoc `scripts/migrate_*.py` files.
- **Cadence constants** confirmed in `config/settings.py`: `MAIN_LOOP_TICK=30`, `DISCOVERY_INTERVAL=1800` (30 min), `STANDARD_CAPTURE_WINDOW=60` (T-60min), `INTENSIVE_WINDOW=5` (T-5min), `STANDARD_POLL_INTERVAL=300`, `INTENSIVE_POLL_INTERVAL=60`, `BOOKIE_INTENSIVE_POLL_INTERVAL=105`. The 60s declared intensive vs 90-97s measured (inspection §E.5) gap is named directly in brief §5.2.
- **Incidental finding (not in brief's §5 questions, named in brief §4):** `racing-metadata-backfill.service` failing every night since 2026-04-29 14:00 UTC with PermissionError on `/home/racing/racing-data-capture/logs/metadata_backfill.log`. Racing API metadata backfill path silently not running. Flagged for Code's "anything surprising" section if confirmed during §5.5.

## Substantive deliverable

`dr029/2_1_race_data/source_review_brief.md`

- 249 lines, 25,439 bytes
- SHA256 prefix `d0c8e9ef6c8409861c984cf54b294d9648a19eef`

Structured like the §2.1 inspection brief was (250 lines / 25,264 bytes for reference). Numbered sections: what-this-is-and-isn't, pre-reads, VPS access, source-tree orienting facts (from Session 33 pre-flight), per-area review questions §5.1–§5.5, output format, hard limit on session length, discipline notes, what-happens-after.

## Five areas commissioned

Each anchored on a specific inspection-report finding:

- **§5.1 — Calibration job's result-resolution wiring** (Cluster 1 surgical-fix viability). Anchored on §H.4 (`daily_calibration_summary` produces `n_winners` daily but `runners.finish_position` 0% in same window) and §C.2 / §H.1 (zero rows in 421,651 carry both `finish_position` AND `betfair_selection_id`). Files: `scripts/daily_calibration_summary.py`, `subscription/racing_api.py`, `scripts/backfill_subscription.py`, `storage/database.py`. Five questions on resolution path, write-back, wiring effort, idempotency, other resolution sites.
- **§5.2 — Betfair scrape's intensive-mode trigger and market-discovery logic** (Cluster 2 56% finding). Anchored on §E.3 (56% AU thoroughbred 30d races no pre-30min snapshot) and §E.5 (intensive p50 90-97s vs documented 60s). Files: `capture/orchestrator.py`, `capture/scheduler.py`, `betfair/client.py`, `config/settings.py`. Five questions on PENDING→CAPTURING trigger, 56% root-cause hypothesis from code shape, intensive-cadence slip mechanism, discovery-interval scope, race-type filters. **Subsumes Session 32's separately-commissioned 56% diagnostic probe.**
- **§5.3 — Snapshot writer for BSP / sp_near / sp_far** (Cluster 4 high-value pipeline-write-back). Anchored on §E.2 (three columns 0.000% across 1.6M snapshots) and §H source-exposes-but-pipeline-doesn't-write. Files: `storage/database.py`, `betfair/client.py`, `betfair/models.py`, `capture/orchestrator.py`. Five questions on whether values are read, where they drop on the floor, what reading would take if not, BSP post-jump capture path, effort-to-write.
- **§5.4 — Soft-book scrapers' shape** (Cluster 3 follow-up + harness/greyhound 99% probe + PointsBet 0.77). Anchored on §G.1 (seven scrapers all alive, uniform cadence) and §G.3 (AU harness 98.9% / AU greyhound 99.0% zero-coverage in pre-30min window). Files: `bookmakers/base.py`, `bookmakers/entain.py`, `bookmakers/unibet.py`, plus all other `bookmakers/*.py`, `capture/proxy.py`. Five questions on uniformity, isolation, harness/greyhound config-vs-structural, PointsBet 0.77 diagnosis, Decodo proxy routing. **Subsumes Session 31's separately-commissioned harness/greyhound config probe and the PointsBet 0.77 question (which carries separately into WIP §15 Decodo review parking lot but fits this scope without conflict).**
- **§5.5 — Supervision config and code-health overall.** Framing-input for the surgical-fix-vs-rebuild call. Files: `scripts/run_collector.py`, `scripts/health_check.py`, `scripts/liveness_check.py`, `scripts/migrate_*.py`, `config/settings.py`, `storage/database.py`, systemd units. Five questions on schema-management discipline, code-cleanliness read, test coverage, logging discipline, **and the load-bearing overall read** — wiring fixes against existing infrastructure / targeted rework of specific components / underlying structural issues — explicitly mapped onto the three Cluster 1 routings.

## Output spec for Code

`dr029/2_1_race_data/source_review_report.md`. Per-area assessment with effort scale (trivial / small / medium / large / structural-rework) + qualitative risk + dependencies; overall read with recommendation between the three Cluster 1 routings (or a fourth surfaced by review); anything-surprising section; self-assessment of completeness. 300-500 lines anticipated.

## Hard limit on session length

Named explicitly in brief §7. If review needs more than one Code session, Code surfaces that as a finding rather than continuing past budget. Partial-but-coherent review beats complete-but-lost-coherence.

## §2.1 close — still held open

§2.1 close gated on Session 34's surgical-fix-vs-rebuild call, which rests on Code's source-review report. No change from Session 32's framing.

## Tool routing

Session 33 = Claude Chat, brief-drafting (delivered).
Out-of-session = Claude Code executes review against this brief.
Session 34 = Claude Chat, reads source-review report, makes the call.

## Two probes subsumed

The Cluster 2 56% diagnostic probe (originally a separate Code commission Session 32) → into §5.2. The Cluster 3 harness/greyhound config-gap probe (originally a separate Code commission Session 31) and the PointsBet 0.77 question → into §5.4. Both subsumptions per operator's call in the opening prompt and substantive fit (both probes ask source-code questions that the broader review naturally absorbs).

## Directory placement decision

Brief sits at `dr029/2_1_race_data/source_review_brief.md` alongside `brief.md` (original §2.1 inspection brief) and `inspection_report.md`. Reasoning per opening prompt: source-code review is technically a follow-up to §2.1's findings rather than a new scope item, so the §2.1 chain stays intact. Filename `source_review_brief.md` disambiguates from existing `brief.md`.

## New standing instructions

None this session. Standing instructions from Sessions 30, 31, 32 (REPL discipline / plain-language framing / operational-vs-analytical line discipline) all held without surfacing.

## Session shape

Scope-completed-as-load-bearing — same shape as Sessions 27, 28, 29, 32. Pre-flight-heavy by design (10 min VPS source-tree probe before drafting, per opening prompt's pre-step) so the brief names actual files with grounded confidence rather than speculative pointers. Drafting proper was tight (~15 min); deliberate.

Eighth consecutive non-early-close session, but shorter than recent sessions (9 min total vs Session 32's 16 min) — reflects the well-anchored opening prompt that pre-specified the brief's structure and the pre-flight scope.
