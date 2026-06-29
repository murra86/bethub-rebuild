# Session 34 — Surgical-fix-vs-rebuild call landed

**Open:** 2026-04-30 14:54 ACST
**Close:** 2026-04-30 15:25 ACST
**Duration:** ~31 min
**Shape:** read-and-decide; routing-call substantive load-bearing work

## Required reads completed

- `work_in_progress.md` (project state through Session 33 close)
- `sessions/SESSION_33.md` (full Session 33 outcomes)
- `dr029/2_1_race_data/source_review_report.md` (Code's source-review report, 252 lines)
- `dr029/2_1_race_data/source_review_brief.md` (the brief Code executed against)
- Pre-flight directory listing of rebuild folder root — clean (seven canonical .md at root, dr029/ artefacts present including source_review_report.md and source_review_brief.md)

## The call landed

**Routing 1 — surgical fix.** Cluster 1 result-population + identifier-overlap, Cluster 2 cadence, Cluster 4 BSP / sp_near / sp_far write-back all routed to surgical fix. Routing 2 (reframe as replacement-design) and Routing 3 (full ground-up rebuild) explicitly considered and not adopted.

## Evidence anchoring the call

Code's per-area reads from `source_review_report.md`:

- **§5.1 (Cluster 1 — the load-bearing finding).** The 0% `finish_position` AND `betfair_selection_id` overlap is path-not-taken, not join-key collision. Calibration job (`scripts/daily_calibration_summary.py`) resolves winners daily; orchestrator settlement path writes `result_status` (1286 WINNERs over 2026-04-20→2026-04-29 verified empirically). The `finish_position` write path exists at `subscription/racing_api.py:_sync_single_runner` (lines 261-310), invoked via `sync_day()`, called by `scripts/backfill_subscription.py` and `scripts/backfill_race_metadata.py --days 1`. The `--days 1` is structurally insufficient — the daily service never catches up after a miss. Fix: one-shot `backfill_subscription.py --from <live-capture-start>` over the 60-day live-capture window (existing code, idempotent); plus rework `racing-metadata-backfill.service` to use `get_unsynced_dates()` instead of `--days 1`. Effort: small. Risk: low.
- **§5.2 (Cluster 2 cadence).** 56% no-pre-30min-snapshot finding has a small-cost surgical path: lower `DISCOVERY_INTERVAL` from 30 min, plus add fast-discovery-if-race-within-next-hour check at the bottom of `_maybe_discover`, plus log the `_register_race` silent-drop branch. Intensive p50 90-97s slip (vs documented 60s) is structural-leaning at the per-race async level — `MAIN_LOOP_TICK=15s` plus per-race-stagger reduction would mostly close the gap; full async-per-race rework not adopted as part of surgical fix. Effort: medium. Risk: medium.

- **§5.3 (Cluster 4 BSP write-back).** `bsp_price` is orphan column — schema declares it but the orchestrator's INSERT doesn't write it; `betfair/models.RunnerData` doesn't have a `bsp_price` field. Three field changes across four files (`betfair/client.py`, `betfair/models.py`, `capture/orchestrator.py`, `storage/database.py` INSERT column list) plus a post-suspension price-fetch path. Schema column already exists; no DDL needed. Effort: small. Risk: low.

- **§5.4 (Cluster 3 scrapers).** Seven scrapers tidy, well-isolated, conform to `bookmakers/base.py` contract. Adding an 8th: small (six touchpoints across four files). Harness/greyhound 99% non-coverage is structural per-platform (every scraper hard-codes thoroughbred filtering at upstream API filter), but DR-029 §3.x parks that scope to v3.1 — not part of surgical fix. PointsBet 0.77 is runtime-probing not source-diagnosable; trivial diagnostic-logging addition would surface root cause in 1-2 days of running. No rebuild case from §5.4.

- **§5.5 (overall shape).** "Targeted rework of specific components." Orchestrator file (961 LOC `capture/orchestrator.py`) is large but coherent; storage layer clean; scrapers tidy. Real-but-bounded debt: no migration framework (schema-as-Python-string-constant via three ad-hoc `migrate_*.py` scripts), no tests (zero test files in project tree), monolithic orchestrator file. None blocks the §5.1-§5.4 fixes. Schema column for `bsp_price` exists but writer doesn't use it (the surgical fix surfaces this; no DDL needed).

## Why Routing 2 and Routing 3 were not adopted

Routing 2 (reframe as replacement-design) requires evidence that the surgical path leaves load-bearing brokenness behind. Code engaged with what such evidence would look like (orchestrator entanglement that risks regressions across surgical fixes; schema-management as a recurring failure source) and found neither. Orchestrator's methods are coherent units; schema-management is a slow-burn concern not a hot-path break.

Routing 3 (full rebuild) requires evidence the existing pipeline cannot be evolved. The contracts (`BookmakerMeta`/`BookmakerRunner`, `MarketSnapshot`/`RunnerData`, `RaceState`, `compute_runner_key`) compose cleanly. Tests are absent — but rebuild doesn't fix that unless the rebuild lands with tests, which is independent of rebuild-vs-surgical.

The operator's strategic instinct from Session 32 — "scrap and rebuild from ground up" — was reasonable from the inspection report alone. The source-code review re-shaped the read: what looked architectural is wiring. Operator agreed with the surgical-fix call once the diagram and plain-language framing landed.

## Three pieces of debt named as deferred-but-tracked

1. No test coverage (zero `test_*.py` files in project tree).
2. No migration framework (schema as `SCHEMA` constant in `storage/database.py`; three ad-hoc `migrate_*.py` scripts with detect-by-existence-check pattern).
3. Monolithic orchestrator file (961 LOC `capture/orchestrator.py`; coherent per-method but six concerns interleaved at file level).

All three land in DR-029 close governance paragraph alongside the periodic data-fitness re-verification component already scheduled there. Do not block surgical-fix execution.

## Two acknowledgements Code flagged that accompany the surgical fix

1. `racing-metadata-backfill.service` `--days 1` → `get_unsynced_dates()` rework is mandatory not optional — surgical-fix `finish_position` story rests on the Racing-API path catching up, which `--days 1` structurally cannot do. Folded into surgical fix 2.
2. `_register_race` silent-drop branch needs a log line — observability for the 56% root-cause hypothesis. Folded into surgical fix 3.

## Operator-driven mid-session corrections

**Operational/analytical line drift surfaced once.** Mid-presentation of the routing call I conflated execution-line and analytical-line in the framing. Operator corrected explicitly: VPS = analytical only; operational/execution is a direct line into Betfair via `betfair_client`. Restated cleanly thereafter and held for the remainder of the session. Per Session 32 standing instruction (operational/analytical line discipline drift watch) — the watch fired and corrected.

**Plain-language framing tightening.** Operator surfaced explicit instruction: "I'm just an operational person, I'm not good at techy speak. You just need to give it to me in plain language: this is what's happening, this is the effect it has, these are the choices you have, with the risks." Per Session 31 standing instruction (plain-language operational/gambling-framed cluster summaries), but applied this session at the routing-call layer not just cluster summaries. Restated the call in decision-maker-level summary form (~10 lines) before getting operator confirmation. **Standing instruction continues to apply across all session-shape work, not just cluster triage** — folded into operator-instructions discipline going forward.

## Diagram produced

Visualizer SVG of the VPS analytical line — what's captured, what the surgical fix changes (3 amber boxes), what's NOT the VPS (operational/execution line, separate). Inline in chat, not saved as a file. Operator's response: "yes, that's fine."

## §2.10 touch-point logged

Operator surfaced the API-field-inventory question mid-session: "is there anything else that the Betfair API or the Racing API have available that we might want to capture?" Recognised as already in §2.10 of `dr029_scope.md` (carried through from Session 28). Confirmed: §2.10 stays separate from surgical fix, runs *after* surgical fix lands, against a cleaner data layer. Touch-point logged in the §2.10 carry-in framing in `dr029_scope.md`.

## Substantive deliverables this session

1. **§2.1 close entry** in `dr029/dr029_scope.md` after §2.1 (closed-with-known-debt-named).
2. **§2.4 surgical-fix carry-in** (cadence + BSP write-back).
3. **§2.6 surgical-fix carry-in** (result population resolution as centrepiece).
4. **§2.10 surgical-fix carry-in plus Session 34 touch-point** (API-field-inventory framing logged).
5. **WIP §1 open question** rewritten as "§2.1 close landed" historical anchor.
6. **WIP §2 rebuild question** marked RESOLVED Session 34 with historical pointer.
7. **WIP "Where we are"** updated for Session 34 close, Session 33 entry pushed down.
8. **WIP table row** for Session 34 promoted from anticipated to DELIVERED; new Session 35 row added; Post-35 framing replaces Post-34.
9. **This session log.**

## What Session 35 will do

Draft the Code brief for the first surgical-fix execution session. Most likely shape: fixes 1+2 combined (backfill `runners.finish_position` over live-capture window via existing `backfill_subscription.py` + rework `racing-metadata-backfill.service` from `--days 1` to `get_unsynced_dates()`). Brief structure parallels Session 28 §2.1 brief and Session 33 source-review brief. Tool routing: Chat. Anticipated short — 15-30 min. After Session 35, Code executes against the brief out-of-session. Subsequent surgical-fix sessions (BSP capture, cadence fix) handled as subsequent bounded Code sessions or rolled into relevant scope-item work.

## Tool routing

Session 34 = Claude Chat (delivered).
Session 35 = Claude Chat, Code-brief drafting.
Out-of-session post-35 = Claude Code, surgical fix 1+2 execution.

## New standing instructions

None new this session. Session 31 standing (plain-language framing) explicitly applied at the routing-call layer not just cluster summaries — extension noted in operator-instructions in WIP. Session 32 standing (operational/analytical line discipline drift watch) fired once mid-session and corrected.

## Close-out lesson — silent write to bash sandbox

Mid-close-out the `create_file` tool reported "File created successfully" for SESSION_34.md and SESSION_35_OPENING_PROMPT.md but the writes landed in the bash sandbox at the same nominal path, NOT the Mac filesystem. Caught via post-write directory listing through Desktop Commander: the listing showed historical session files but not the two new ones, while `bash` `stat` against the sandbox path showed they "existed." This is the filesystem discipline standing instruction firing exactly as written: "bash sandbox can't reach `/Users/tim/Desktop/Projects/bethub-rebuild`; use Desktop Commander or projects-filesystem MCP server for all rebuild folder file operations." Recovery: re-wrote both files via Desktop Commander's `write_file`. **Lesson reinforced for future sessions:** for new files in the rebuild folder, use Desktop Commander's `write_file` directly. The `create_file` tool's "successfully" message is misleading because it writes to the sandbox path namespace which is distinct from the Mac filesystem path namespace despite identical-looking paths. Add to operator-instructions as a Session 34 lesson alongside the existing Sessions 15/16/19/20/30 close-out failure lessons.

## Session shape

Read-and-decide. Code's source-review report was unusually unambiguous, which made the call tractable inside one session's context budget. Operator's strategic instinct from Session 32 was honoured by explicit consideration of Routings 2 and 3 against the evidence rather than defaulting to surgical fix. Mid-session corrections (operational/analytical line drift, plain-language framing tightness) surfaced and held. Close-out hit a silent write-to-sandbox failure caught via state-snapshot verification per the Session 20 standing instruction; recovered cleanly. Ninth consecutive non-early-close session.
