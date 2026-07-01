# Brief — race_date population-rule diagnostic

**File:** `race_date_semantics_brief.md`
**Status:** LOCKED
**Anchored:** 2026-06-30 09:35 ACST (DR-021 Adelaide)
**Sequence:** Brief 1.5 of 2 — read-only diagnostic, precursor to Brief 2.
**Bet-safety:** CLEAN — read-only inspection only. No file edits, no DB
writes, no service restart, no Betfair / settlement / money-movement /
lay / live-betting path. `capture.db` opened read-only throughout.

---

## §1 — What this brief is and is not

A **read-only diagnostic**. Code reads source + samples the DB to
answer one question — how is `races.race_date` populated, and what must
the client query to retrieve races for a given real-world day. Single
bounded session. **NO edits to any file. NO writes. NO restart.**
Surprises become **findings** in the report, not blockers, not
mid-session pings. This brief does **not** fix anything — if the data
looks wrong, that is a finding for operator-Claude, not a Code repair.

## §2 — Why this work exists

Brief 1 v2's §7 timezone probe found `races.race_date` is **decoupled**
from `scheduled_start`: rows filed under `race_date = 2026-06-28` carry
`scheduled_start = 2026-06-29` UTC — a ~full-day offset from both the
UTC and the Adelaide-local date of the race instant. Brief 2 (the Mac
`vps_client` rewrite) must compute a `?date=` value to fetch "the races
that ran on Adelaide-local day D". It cannot do that correctly until we
know the rule that produced `race_date`. This diagnostic pins the rule
so Brief 2 is built on a known contract, not a guess.

## §3 — Pre-reads (the ingest path)

Required (read-only):
- this brief
- `subscription/racing_api.py` — the Racing API feed ingest (where a
  source record becomes a row)
- `capture/orchestrator.py` — the scheduling / write driver
- `storage/database.py` — the `races` write path (the INSERT/UPSERT
  that sets `race_date`)
- `api/routes/races.py` — confirm the read side treats `race_date` as a
  bare `YYYY-MM-DD` string match (it does, per Brief 1 v2)

Reference-only:
- `vps_date_endpoint_report.md` — §4 timezone-basis findings (the
  starting evidence)

## §4 — System access

VPS via SSH: `root@187.77.183.9`. Repo: `/home/racing/racing-data-capture`.
- **ALL FILES READ-ONLY.** No edits to any file, full stop.
- **capture.db: READ-ONLY** (`mode=ro`). No writes, no schema change.
- **NO service restart.** `racing-api.service` and
  `racing-capture.service` both untouched.
- Report timestamps Adelaide local (ACST/ACDT) per DR-021.

## §5 — Scope (read-only investigation)

**5.1 Trace the `race_date` population rule.** Follow the path from
feed record → stored row. Identify the exact source field (or computed
expression) that becomes `races.race_date`. Name the file + line where
it is set, and quote the transform (verbatim, a few lines). Is it: a
source "meeting date" field copied as-is? a date parsed from a source
timestamp (and in which timezone)? something derived/computed? State
which, with the evidence.

**5.2 DB cross-check across eras.** Read-only, sample races spanning
the data range (e.g. a late-June 2026 date, a Jan 2026 date, an early
date near 2025-03). For each sample, line up `race_date`,
`scheduled_start`, `venue`, and any source-id / meeting field present.
Characterise the relationship: is the ~1-day offset consistent across
all eras, or only some? Is it venue/source-dependent? Document the
pattern — do not explain it away.

**5.3 `scheduled_start` encoding inventory.** Brief 1 v2 found ≥3 string
encodings (`+00:00`, `Z`+millis, 7-digit fraction). Enumerate the
distinct formats present, each with a rough date range / source era, so
Brief 2's parser is specified to handle all of them. Read-only.

**5.4 State the client query contract.** The deliverable that matters:
given the rule from 5.1–5.2, state — in one explicit sentence — what a
Mac client must compute and pass as `?date=` to retrieve the races that
ran on a given **Adelaide-local calendar day D**. If the rule is clean,
give the exact mapping. If it is ambiguous or the data is internally
inconsistent, say so plainly and lay out the candidate mappings with
the evidence for each — do **not** force a single answer that the data
doesn't support. This is the input Brief 2 builds on.

## §6 — Sequencing within session

1. Read the ingest-path source (§3) and establish the 5.1 rule from
   code first.
2. Run the §5.2 read-only DB cross-checks to confirm (or contradict)
   the code-derived rule against real rows.
3. Inventory the §5.3 encodings.
4. Synthesise the §5.4 contract last — it depends on 1–3.

If the work doesn't fit one session, that's a finding — stop and
report, don't continue.

## §7 — Success criteria

The report answers, with evidence, all four: (5.1) the population rule
named at file+line; (5.2) the offset pattern characterised across eras;
(5.3) the encoding set enumerated; (5.4) the client query contract
stated (or the ambiguity laid out with candidates). "Could not
determine X" is an acceptable finding **if** the report says what was
checked and why it was inconclusive — silent omission is not.

## §8 — Output spec

Single file:
`/Users/tim/Desktop/Projects/bethub-rebuild/race_date_semantics_report.md`
Sections:
1. The population rule (5.1) — file+line, quoted transform, verdict
2. Cross-era pattern (5.2) — the sample table + characterisation
3. `scheduled_start` encoding inventory (5.3)
4. **Client query contract (5.4)** — the one-sentence mapping, or the
   ambiguity + candidates
5. Self-assessment — anything odd, anything inconclusive, data-quality
   observations (e.g. the `n_runners:0` past-race subset, if it
   intersects)

Length ~100–200 lines. Does NOT contain: any fix or repair, Brief-2
work, recommendations beyond stating the contract.

## §9 — Hard limits (non-negotiable)

- **READ-ONLY on everything.** No edits to any file. No new files in
  the repo (an off-repo `/tmp` scratch note is permitted but not
  required).
- **NO writes to capture.db**, no schema change, no migration.
- **NO service restart**, no touching `racing-api.service` or
  `racing-capture.service`, the collector, or the scrapers.
- **NO git operations whatsoever.** The dirty tree is the operator's
  in-flight work; read `git status --porcelain` only if needed for
  orientation, change nothing.
- **NO fixing the `race_date` data** even if 5.1/5.2 reveal it is
  wrong. Diagnosis only; any repair is a separate operator-Claude
  decision downstream.
- **NO Brief-2 work** (the Mac `vps_client` rewrite).
- Single bounded session.

## §10 — What happens after Code's session

Operator-Claude reads `race_date_semantics_report.md`, confirms the
client query contract (or resolves the ambiguity), then drafts
**Brief 2** (Mac `vps_client` API rewrite + launcher fixes) with that
contract baked in. Code does **not** write Brief 2.

## §11 — Cross-references

- **Builds on:** `vps_date_endpoint_brief.md` (LOCKED v2) + its report
  §4 (timezone-basis findings); investigation report C-1 (past-date
  gap).
- **Feeds:** Brief 2 (Mac `vps_client` rewrite) — the §5.4 contract is
  its input.
- **DRs:** DR-033 (racing data = analytical layer), DR-028 (single
  integration boundary), DR-027 (two-DB), DR-021 (Adelaide anchors —
  the whole point of the offset question).
- **Excludes:** Brief 2; any `race_date` repair; all parking-lot items.
