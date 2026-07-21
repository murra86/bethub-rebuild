# DR-029 §2.1 — race-side data fit-for-purpose: inspection brief for Claude Code

*Drafted Session 28 of the v3 rebuild arc, 2026-04-30 ACST. Hand-off from operator-Claude (Claude Chat) to Claude Code. Operator routing: Chat scoped the inspection question set; Code executes the inspection, produces measurements, and writes a structured report. No remediation decisions in this session; pass/fail interpretation is operator-Claude's job in Session 29 of the rebuild arc.*

---

## 0. What this brief is and is not

**Is.** A measurement-execution brief. Code reads `capture.db` on the VPS, runs the queries below against the actual data, and produces a single inspection report at `dr029/2_1_race_data/inspection_report.md`. Output is **distributions, coverage rates, and gaps** — raw numbers reported by code. No thresholds. No pass/fail. No remediation proposals.

**Is not.** A scoping conversation, a governance discussion, or a place to make design decisions. If the inspection surfaces something genuinely surprising or architecturally consequential (e.g. an entire table missing, schema fundamentally divergent from `agent_review/inputs/data_layer_current.md` §§4–5), report it as a finding in the report and stop. Do not attempt to fix it. Operator-Claude will route the surprise into a governance discussion in the next session.

Reasoning for this discipline: §2.1 sits at the front of nine sequenced execution items in `dr029_scope.md` §5. Several downstream items (2.4 Betfair Streaming spec, 2.6 settlement model, 2.8 bet-schema reframing) depend on what the inspection finds. The architectural decisions belong with operator-Claude reading the inspection report against the wider scope; Code's job is to produce the report.

## 1. Pre-reads (mandatory before measurement)

Read in this order and confirm key facts back at the top of the inspection report:

1. `dr029/dr029_scope.md` — the active governance document for DR-029 execution. **§1.2** (two-direct-lines architecture, the analytical line being VPS→`capture.db`→`vps_client`) and **§2.1** (this scope item) are most load-bearing for the inspection.
2. `v3_data_requirements.md` (rebuild root) **§B.2** — the canonical requirements set the measurements verify against. Each subsection (B.2.1 race metadata, B.2.2 runner metadata, B.2.3 results, B.2.4 Betfair time-series, B.2.5 bookmaker time-series, B.2.6 BSP / calibration) maps onto a measurement section below.
3. `agent_review/inputs/data_layer_current.md` **§3** (current operational reality — the operator-familiarity-decay framing, the analytical-vs-operational distinction) and **§§4–5** (schema-defined fields per category — what the documentation says capture.db captures). §3 is the why-this-inspection-matters context. §§4–5 are the documented schema; the inspection verifies how this matches reality.

**Confirm at top of inspection report:** the three documents read, today's Adelaide local date, and that the brief discipline (measurements only, no remediation) is held.

## 2. VPS access and tooling

**Step 1 of substantive work — restart the VPS tunnel before anything else.** The launchd plist `~/Library/LaunchAgents/com.bethub.vps-tunnel.plist` exists but the tunnel has been down 9+ days. The data API (`racing-api.service` at `127.0.0.1:8400`) is not the access path for this inspection — direct SQLite access is.

**Direct DB access (preferred for this inspection).** SSH to `root@187.77.183.9` with key-based auth. The live capture DB is at `/home/racing/racing-data-capture/data/capture.db`. Query it directly with `sqlite3` and Python (`sqlite3` stdlib module). The DB has WAL — run `sqlite3` in read-only mode (`file:...?mode=ro`) so the inspection cannot accidentally write or interfere with the active capture process.

**While restoring the tunnel, optional bonus task** (do this only if it is genuinely zero-friction; do not let it slow the inspection): note whether the launchd plist's `KeepAlive` and `RunAtLoad` settings would have caught the 9-day outage. This is information for the reachability arc tunnel-auto-restart hygiene component (parked elsewhere in WIP §11). Capture observation in inspection report under a §0.1 *operator-side hygiene observations* heading. Do not implement any fix — observation only.

**Adelaide local time anchoring.** Per DR-021 (the timestamp discipline): all timestamps in the inspection report should be Adelaide local time (ACST/ACDT, UTC+9:30 standard / UTC+10:30 daylight) — anchor with `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`. The DB timestamps may be in UTC or in some other zone; convert to Adelaide local for the report or state the source zone explicitly.

## 3. Step 0 — schema discovery pass before measurement

The operator's familiarity with `capture.db`'s exact schema has decayed (per `data_layer_current.md` §3). Code does not assume table names, column names, or schema structure from the documentation in `data_layer_current.md` §§4–5. That document is the schema-defined view; the inspection verifies actual schema against it.

**First measurement section in the report (§A — schema discovery).**

1. List all tables in `capture.db`. Report names, row counts, approximate disk size per table.
2. For each table, show `CREATE TABLE` statement (the `sqlite_master.sql` field) verbatim. Yes, all of them. This is the definitive schema view. Wrap each in a code block in the report.
3. List all indexes per table.
4. Report the freshest and oldest record timestamps per table (use the most plausible timestamp column — pick the one most likely to represent record-write time; if multiple plausible columns exist, report all).
5. Report total row counts and 30-day / 12-month row counts per table.

**Outcome.** §A maps the actual schema. Subsequent sections (§B onward) reference the actual table and column names §A surfaces. If Code finds tables in `capture.db` that aren't in `data_layer_current.md` §§4–5, list them. If documented tables are missing from `capture.db`, list that too. Schema mismatches relative to `data_layer_current.md` §§4–5 are findings, not blockers — note them and continue with the schema as it actually is.

## 4. Time windows and stratification

**Two measurement windows for every section below.** "Last 30 days" (operationally recent) and "last 12 months" (matches Harville calibration window; surfaces drift). Report both side-by-side as columns in any table-shaped output. If the two tell meaningfully different stories — e.g., a field that's 95% populated in the last 30 days but 60% over 12 months, or vice versa — flag the divergence in the section's prose summary.

**Race code stratification.** Most measurements should be reported per-code (thoroughbred, harness, greyhound) plus an "all codes combined" row. Capture systems often have asymmetric coverage across codes; aggregating hides the asymmetry.

**NZ pass-through detection (DR-029 scope §3.9).** Independently of the AU stratification: report whether `capture.db` currently contains any NZ races at all — count of NZ races (any code) over the 12-month window. The detection is by venue/country field, however the schema represents jurisdiction. If NZ races are present, report population rates for §B (race metadata) and §C (runner metadata) on the NZ subset alongside the AU subset, in case NZ enters scope as a backward-compatible later addition. If NZ races are absent or near-zero, that is the answer — note and move on.

**Live-capture floor for time-series sections.** Live scraping on the VPS started ~3 months ago (operator confirmation, Session 29 of the rebuild arc). Before that, `capture.db` was backfilled from the Racing API for race metadata, runner metadata, and results — that backfill covers the full 12-month window perpetually (Racing API offers rolling 12-month historical access). So §B / §C / §D measurements use the full 12-month window as specified. **§E (Betfair time-series), §F (BSP), and §G (soft-book scrapers), however, only have data from the live-capture-start point forward** — those sources don't backfill. For those three sections specifically, Code reports the actual live-capture-start date discovered from the data (the oldest snapshot timestamp in the relevant tables), then runs the §E/§F/§G measurements within "live-capture-start to now" rather than the full 12-month window. The 30-day window is unaffected (live capture has been running well over 30 days). State the live-capture floor explicitly at the top of §E, §F, and §G in the report.

## 5. Measurement battery — the report sections

Each section below has the same structure: what to measure, how to report it, what cross-references the requirement set. Code can adjust the exact query shape based on what §A schema discovery reveals — column names, join paths, etc. The *categories* are the load-bearing thing; the *queries* are Code's call.

### §B — Race metadata coverage (cross-ref `v3_data_requirements.md` B.2.1)

Per race in the measurement window, for each field in B.2.1, report the fraction of races where the field is non-null and non-empty:

- `race_class` — the formal grade *within* a code (e.g., for thoroughbreds: Maiden, Class 1, Benchmark 64, Open Handicap; for greyhounds: Maiden, Grade 5, Free For All; for harness: equivalent class scheme). Distinct from `race_group` and `race_code` below.
- `race_distance` (metres)
- `race_surface` (turf / synthetic / dirt or code-equivalent)
- `race_group` — black-type tier *layered on top of class* for premium races (G1 / G2 / G3 / Listed / Stakes). Most races have no group designation and the field is null; only elite races carry a tier. Distinct from `race_class`.
- `track_condition` at jump
- `track_type` (flat / circle / trotting / pace)
- `scheduled_jump_time`
- `actual_jump_time` (post-jump)
- `race_code` (thoroughbred / harness / greyhound)
- `venue` (canonical)
- `race_number`

Stratify by race code. Two windows side-by-side.

**Additionally for `actual_jump_time`:** of races that have completed (results known, see §D), what fraction have `actual_jump_time` populated? This is a different denominator than "all races in window" because incomplete races shouldn't penalise the rate.

**Sanity-check distribution:** for `race_distance`, report min / median / p95 / max per code — sanity check against expected ranges (e.g., greyhound 280m–700m, thoroughbred 800m–4000m). Wildly out-of-range values are findings.

### §C — Runner metadata coverage (cross-ref `v3_data_requirements.md` B.2.2)

Per runner per race in the measurement window, for each field in B.2.2, report fraction populated:

- Runner name (canonical)
- Barrier / box / draw
- Weight carried (where applicable per code)
- Jockey / driver / trainer
- Form indicators (per Racing API exposure)
- Finishing position (post-result, only for completed races)
- Beaten margin (post-result, only for completed races)
- BSP (post-jump, only for completed races) — also report in §F
- Scratching events (`scratched_at`, `late_scratch` flag)

Stratify by code, two windows.

**For scratching events specifically** (B.2.2 explicitly names `scratched_at` and `late_scratch`): of all races where at least one runner was scratched, what fraction have a `scratched_at` timestamp? Of races where late scratchings happened (a runner scratched within ~30 minutes of jump), what fraction have the `late_scratch` flag set correctly? This is the most directly verifiable signal of scratching-capture *timing* completeness from B.2.1's specific ask. If the schema does not have these exact fields, report what it does have and how scratching information is represented.

### §D — Results coverage (cross-ref `v3_data_requirements.md` B.2.3)

For races whose scheduled jump was at least 24 hours before the inspection runs (so genuinely complete), for each field in B.2.3, report fraction populated:

- Finish positions for all starters
- Dead-heat indication
- Stewards' inquiry status
- Margin between positions
- Race time / sectional times
- Result `observed_at` timestamp
- Source identifier (Betfair / Racing API / Racing Australia / Racenet)

Stratify by code, two windows.

**Settlement-relevant lag** (informs §2.6 settlement model in the wider scope): of completed races, what is the distribution (median / p50 / p95 / p99 / max) of (result observed-at timestamp) minus (actual jump time)? In other words: how long after the race finishes does the result actually populate in `capture.db`? Report per source if multiple sources contribute. This measurement directly informs whether `capture.db` is fast enough for v3's auto-settlement path or whether there is a structural lag that needs handling.

**Source identifier distribution:** report the count and fraction of completed races where each source is the primary results source (Betfair Win, Racing API, Racing Australia, Racenet, others). This shows which sources are actually carrying weight versus nominally configured.

### §E — Betfair time-series cadence (cross-ref `v3_data_requirements.md` B.2.4)

*Window note (per §4 above):* §E uses "live-capture-start to now" rather than the full 12 months. State the discovered live-capture-start date at the top of this section.

This is the cadence-sufficiency-for-analytical-bracketing question, which is the one B.2.4 explicitly carves out as a DR-029 verification item. The brief's framing for this is empirical-cadence-distribution; the bracketing-sufficiency interpretation belongs to operator-Claude.

**Per race in the measurement window** (sample-bound if needed for tractability — see *sampling* below), for the snapshots stored against each Betfair market within ±30 minutes of `scheduled_jump_time`:

- Number of snapshots per race in the 30-minute pre-jump window.
- Number of snapshots per race in the last 5 minutes pre-jump (the documented "intensive" window).
- Number of snapshots in-running (between actual jump time and result observed-at, where both available).

**Inter-snapshot interval distribution.** For each of those three windows, compute the inter-snapshot interval per market (timestamp differences between consecutive stored snapshots). Report the distribution: median / p50 / p95 / p99 / max. Two windows (30d / 12m). Per code if material.

**Documented cadence vs reality.** Documented cadence per `data_layer_current.md` §4.4 is: 5-minute standard outside pre-jump, 60-second pre-jump intensive in last 5 minutes, 60-second in-running, 2-minute settlement checks. Report measured cadence side-by-side with documented and flag any material divergence (e.g., median pre-jump-window interval well above 60s).

**Gap rate.** Fraction of races where any inter-snapshot interval in the last-5-minutes-pre-jump window exceeds 120s (i.e., 2× documented cadence). Same for 30-minute window exceeding 600s (2× standard). Per code, two windows.

**Snapshot field coverage.** For a representative sample of stored snapshots, report fraction populated for each B.2.4 field:

- Best back price + size
- Best lay price + size
- Top-3 back depth
- Top-3 lay depth
- Total matched

If any of these have a structurally low population rate, that's a finding.

**Sampling.** If full per-race snapshot computation across 12 months is intractable (likely — could be tens of millions of snapshot rows), sample. Reasonable approach: sample 500 races per code per window (so 500 × 3 codes × 2 windows = 3000 race samples max), stratified across the window to avoid recency bias. State the sampling approach in the report. Do not sample if the full computation is feasible — measure exact distributions where possible.

### §F — BSP and calibration (cross-ref `v3_data_requirements.md` B.2.6)

*Window note (per §4 above):* §F uses "live-capture-start to now" rather than the full 12 months. BSP is captured post-jump from live Betfair API; pre-live-capture races will not have BSP regardless of completion status.

For completed races in window, fraction with BSP populated per runner per code, two windows. For races without BSP populated, are they clustered (specific source dropped, specific code dropped, specific time period missing)?

Calibration outputs (daily summaries, batch summaries per `v3_data_requirements.md` B.2.6 / `data_layer_current.md` §4.5): are they being produced — most-recent daily summary timestamp, most-recent batch summary timestamp, gap pattern. Cluster pattern (specific gaps in specific weeks) is more useful than aggregate population rate.

### §G — Soft-book scrapers — health and cadence (cross-ref `v3_data_requirements.md` B.2.5; `data_layer_current.md` §§5.1–5.2)

*Window note (per §4 above):* §G uses "live-capture-start to now" rather than the full 12 months. Soft-book scrapers do not backfill; pre-live-capture races have no soft-book data.

This section covers the §2.1 brief-extension scope decided this session: soft-book cadence sufficiency for DR-014's hot-path use case, plus a quick scrapers-still-running health pass.

**Per scraper** (Entain / Ladbrokes-Neds, PointsBet, Unibet, PlayUp, TABtouch, Sportsbet via Racing API; if `capture.db` has additional scrapers configured, include them; if any of the listed scrapers has no representation, flag that):

- Last write timestamp.
- Total snapshot count, 30 days and 12 months.
- Number of distinct races covered, 30 days and 12 months.
- Within-window write volume change: 30-day rate vs 12-month rate (rate = snapshots per day). Material divergence flags scrapers that have died or degraded inside the 30-day window.

**Cadence per scraper for DR-014 hot-path.** Per `data_layer_current.md` §5.2, documented soft-book cadence is 5-minute standard, 90–120-second intensive in pre-jump window. Same shape as §E above:

- Inter-snapshot interval distribution per scraper per race in the ±30 min window.
- Last-5-minutes-pre-jump intensive window distribution.
- Gap rate (intervals >2× documented cadence).
- Two windows, per code where sufficiently populated.

**Cross-scraper coverage at races.** For each race in window, how many of the configured scrapers produced at least one snapshot in the pre-jump window? Distribution: report fraction of races covered by 0, 1, 2, 3, 4, 5, 6+ scrapers. This shows whether DR-014's hot-path multi-book price comparison has the books it expects at decision time.

### §H — Cross-section anomalies and surprises

Free-form section. Anything Code surfaced during the inspection that doesn't fit cleanly into §§A–G but seems worth naming. Examples of what could land here (illustrative, not prescriptive):

- A whole code (e.g., greyhound) is materially under-populated relative to others.
- A scraper writes data but the data has a systematic field-population issue.
- Timestamp columns reveal a clock-skew or DST-handling issue.
- A documented field exists in the schema but is universally null.
- The `bookmakers` / scraper-config table (or equivalent) lists scrapers that aren't writing.
- Jurisdiction handling reveals NZ in unexpected ways.
- **Source-exposes-but-schema-doesn't cases that are naturally apparent during schema discovery.** If the existing scraper code or capture pipeline surfaces evidence of source-side fields the schema doesn't store (e.g., a Racing API response payload field with no corresponding column, a Betfair API field present in raw responses but dropped before persistence), note it here. **Hard limit:** observation only, no survey. Do not read API documentation, do not probe live API responses for new fields, do not enumerate what's available beyond what the schema discovery surfaces by accident. The systematic Betfair / Racing API field-inventory survey is §2.10 of the wider scope and lands as its own session arc — pre-empting it here would be scope creep.

This section exists because the operator's familiarity has decayed and "what's surprising about the data" is genuinely useful information. Up to four items max for the non-source-survey content; the source-survey-adjacent observations can be additional and are short by construction (no exhaustive lists). Do not pad.

## 6. Output format

**Single file, single delivery.** `dr029/2_1_race_data/inspection_report.md` at the rebuild root.

**Top-of-report header** (~half a page):

- Inspection date (Adelaide local).
- Confirmation pre-reads done.
- Confirmation brief discipline held (measurements only, no remediation).
- VPS tunnel restart outcome (succeeded / required additional work / partial — short).
- The §0.1 operator-side hygiene observation re launchd `KeepAlive`/`RunAtLoad`, if captured.
- Scope reminder (one paragraph): the seven measurement sections, the two windows, the per-code stratification, the NZ pass-through.

**Then §A through §H in order**, with consistent shape per section:

1. **Measurement summary** — ~3–6 sentences naming the headline numbers. Plain language. No analytical interpretation, no remediation.
2. **Detailed numbers** — tables, one row per stratification × window cell. Markdown tables.
3. **Anomalies** within the section, if any — bullet list, factual.

**No conclusions, no recommendations, no overall verdict.** The report ends after §H.

**Length and density.** Aim for ~400-800 lines depending on how much the data has to say. Numbers are the point — prose is the thinnest possible scaffolding around tables. Resist the temptation to write interpretive paragraphs.

## 7. Discipline notes for Code

These are governance-shaped instructions. Hold them.

- **Read-only on the DB.** Open `capture.db` in read-only mode (URI `file:...?mode=ro`). Active capture is running concurrently. Do not write, do not vacuum, do not analyze, do not anything that mutates state.
- **Schema discovery before measurement** (§3 above). Don't assume `data_layer_current.md`'s schema-defined view matches reality. Verify, then measure.
- **No remediation in this session.** If something is broken, report. Do not fix. The report goes to operator-Claude (Session 29 of the rebuild arc), who decides what to do about each finding against the wider scope.
- **No scope creep.** The brief covers §2.1 only. Several adjacent items (§2.4 Betfair Streaming spec, §2.6 settlement model — see `dr029_scope.md` §5 for the full sequencing) will benefit from this inspection's findings, but they are separate execution items in their own sessions. Resist pre-empting.
- **Standing instructions to honour.**
  - DR-021 timestamp discipline (Adelaide local; explicit zone).
  - DR-027/028 cross-DB boundary discipline (the inspection reads `capture.db`; v3 will read it via `vps_client`; nothing here writes to it or assumes its data lives anywhere else).
  - Filesystem note: rebuild folder paths via Desktop Commander or filesystem MCP server, not bash sandbox. Code typically operates in its own filesystem mode and does not have this constraint.
- **Backup hygiene.** No edits to existing canonical files. Code creates `dr029/2_1_race_data/inspection_report.md`. If Code creates intermediate scratch files (query outputs, sampled data), put them in `dr029/2_1_race_data/scratch/` and clean up at end-of-session, leaving only `inspection_report.md` and a tiny `notes.md` if anything didn't fit the report (logs of weird query behaviour, intermediate decisions made during execution that future sessions might want to know).

## 8. What happens after Code's session

Operator-Claude opens Session 29 of the rebuild arc with the inspection report in hand. Reads it against `dr029_scope.md` §2.1 and the wider scope. Triages findings by category:

- *Fit-for-purpose confirmed* on a category — record in the running DR-029 scope-progress log.
- *Insufficiency flagged* on a category — open governance discussion on resolution path. Resolution paths are explicitly **not pre-decided** per §2.1's framing. Possibilities include: tune cadence, extend capture window, accept staleness with operator-visible indicator (the three named in `v3_data_requirements.md` B.2.4), capture additional fields, surface as known limitation, or other paths the data shape suggests.
- *Surprise* (§H content) — case-by-case routing.

NZ pass-through (§4) decided: in scope as backward-compatible later addition (if data exists), or out of scope as day-one limitation (if it doesn't).

**This brief is information-passing only, not a delegation of governance work.** Code measures, operator-Claude interprets.

## 9. Cross-references

- `dr029/dr029_scope.md` — full DR-029 scope with §2.1 specification at the requirement level.
- `v3_data_requirements.md` (rebuild root) §B.2 — canonical requirements set.
- `agent_review/inputs/data_layer_current.md` §§3–5 — operational reality framing and schema-defined view.
- `decisions.md` — DR-027 (two-database architecture), DR-028 (integration boundary discipline), DR-029 (data layer fit-for-purpose before build), DR-021 (timestamp discipline), DR-014 (soft-book hot-path use case).
- `work_in_progress.md` (rebuild root) — Open questions §1 (this work item), §9 (VPS tunnel hygiene), §11 (reachability arc components, including the optional bonus tunnel-launchd observation).
