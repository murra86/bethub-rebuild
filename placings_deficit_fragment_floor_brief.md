# Placings deficit — fragment-floor measurement brief

**Status:** LOCKED — Session 206 (2026-06-30). Code executes against
this contract end-to-end; surprises become findings, not edits.
**Type:** Empirical measurement / inspection (read-only). Session 28
(§2.1 inspection) template: schema-discovery before measurement,
tables-with-prose output, **no recommendations, no fixes, no verdict.**
**Anchored to:** DR-034 stance 4 (fragment-collision; read-time collapse
remediation) + `recovery_run_report.md` R-1/R-2 (the 41,340 recoverable
deficit and its burn-rate caveats).

---

## §1 — What this brief is and is not

**Is:** a single bounded Code session that **measures** how much of the
live placings-recovery deficit is structurally un-fillable because the
physical race is already resulted on a *different* capture fragment than
the one whose in-scope runners carry NULL finishing positions. Output is
a decomposition of the deficit into **ghost** (resulted on a sibling
fragment — the backfill can never clear it) versus **genuine** (no
resulted sibling — truly recoverable).

**Is not:** a fix. Code does **not** collapse fragments, union runners,
change any schema, touch ingest, or modify the backfill. It does not run
a recovery pass. Surprises become findings in the report, not actions.
The collapse remediation DR-034 stance 4 points to remains a **separate
future brief**, unwritten here.

---

## §2 — Why this work exists

The S206 DR-034 review (the backfill cross-check) surfaced that the
nightly placings recovery lands Racing-API finishing positions on
**natural-key fragments** via the subscription path, while DR-034 makes
the **Betfair WIN market id** the canonical race spine. Because one
physical race is fragmented into several capture rows (87% of
market-bearing rows; `vps_endpoint_enrichment_report.md` §4), a result
can land correctly on one fragment while a *sibling* fragment's in-scope
runners stay NULL forever — the backfill never revisits them. Those
permanently-NULL runners would inflate the recovery deficit (R-1:
41,340) and could read as a **stall** (R-2) when the race is in fact
resulted. This brief quantifies that floor so the burndown (first clean
point 1 Jul) and the stall-alert threshold are read against the **true**
recoverable target, not the raw 41,340.

## §3 — Pre-reads

Required, in order:
1. `decisions.md` DR-034 (the locked identity model — stance 4 is the
   anchor).
2. `BETHUB_DATA_REFERENCE.md` §B (the full identity & reconciliation
   model; §B.5 the fragmentation mechanism, §B.7 the fragment-collision
   rule).
3. `recovery_run_report.md` §2 (the exact deficit predicate) + R-1/R-2.
4. `placings_landing_fix_report.md` §2 (the name-key runner identity the
   backfill writes under — `resolve_result_write_key`).

Reference-only (read on demand): `race_date_semantics_report.md`
(fragmentation mechanism), `vps_endpoint_enrichment_report.md` §4 (the
worked duplication example, market `1.259530858`).

## §4 — System access

- **Host:** racing-data-capture VPS (`root@187.77.183.9`), via SSH.
- **DB:** `capture.db` (the one the nightly backfill / `sync_day()`
  writes to), opened **`mode=ro`**. Confirm the canonical path in §5.1;
  **never copy the file** (WAL state is lost) — query in place via
  `start_process` Python at the live path.
- **Read-only throughout.** No writes to capture.db, no recovery pass,
  no source-tree edits.
- **No git operations of any kind** (the `racing-data-capture` tree is
  broadly dirty; this brief touches no tracked file, so `git status`
  must be byte-identical at close).
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for every
  time-of-day reference in the report.

## §5 — Measurement scope

### §5.1 — Schema + path discovery (do this first)

Ground, don't assume. Confirm: the canonical `capture.db` path; the
`races` columns (`id`, `race_date`, `venue_normalised`, `race_number`,
`betfair_win_market_id`, `scheduled_start`, status field, `race_class`,
and any trial/jump-out flag); the `runners` columns (`finish_position`,
`scratched`, `runner_key`, `betfair_selection_id`, name field,
`result_status`). State the exact deficit predicate as live SQL before
measuring. If a named column differs, report the real name and proceed.

### §5.2 — Baseline (the decomposition must sum back to this)

Reproduce the live **recoverable** deficit exactly as
`_recoverable_deficit` / `get_backlog_dates` computes it: in-scope
runners (`race_class IS NOT NULL`, non-trial/non-jump-out,
`finish_position IS NULL`, `scratched = 0`), `race_date ≥ 2026-03-15`,
exhausted/retired dates excluded. Report the total (expected ≈ 41,340 ±
nightly burn) and the date count. Every later split must reconcile to
this number.

### §5.3 — Regime 1: market-stamped ghost deficit (PRIMARY, precise)

For deficit runners whose race row carries a `betfair_win_market_id`:
group all capture rows by that market id (the DR-034 spine). A market id
is a **resulted-sibling group** if ≥1 fragment in the group has
populated finishing positions while ≥1 other fragment contributes
in-scope NULL-position runners to the deficit. Count the deficit runners
sitting on the NULL fragment of such groups — these are **ghost
(market-stamped)**: the physical race is resulted, the positions are on
a sibling, the backfill will never fill this row.

Report: ghost-market-stamped runner count; how many distinct market ids;
and the count of deficit runners on market-stamped rows whose group has
**no** resulted sibling (genuine, market-stamped).

### §5.4 — Regime 2: no-market ghost deficit (SECONDARY, bounded)

For deficit runners whose race row has **no** market id, the spine is
absent and siblings can only be matched by the second-class derived key
(`scheduled_start`→Adelaide-local date + canonical venue + race number).
Precise merging needs venue-harmonisation (Fix 5, not built), so this
is an **approximation with an explicit error bar**, not a precise
count. Use the best available venue normalisation present in the DB;
report ghost-no-market as a **range** (strict exact-venue match as the
lower bound; date+race-number match ignoring venue spelling as the upper
bound) and state the assumption. Do **not** build venue harmonisation to
tighten it — that's Fix 5, out of scope.

### §5.5 — Worked-pattern confirmation

Confirm or refute the specific hypothesised pattern on a sample of
ghost groups: a **Betfair-stamped fragment** whose `selection_id`
runners are NULL, paired with a **subscription sibling** whose runners
carry positions under name keys (`S:<name>` / `N:<n>`,
`results_source='subscription'`). Show 2–3 worked market ids row-by-row
(à la the fix report's Dubbo/Townsville tables). This tells us whether
the ghost floor is exactly the cross-source split DR-034 stance 4's
read-time union must repair.

## §6 — Sequencing within session

§5.1 (schema/path) → §5.2 (baseline) → §5.3 (market-stamped, the
precise primary) → §5.4 (no-market, bounded) → §5.5 (worked pattern).
§5.3 is the load-bearing number; if budget/time runs short, a complete
§5.1–§5.3 with §5.4/§5.5 flagged partial is a coherent result — say so
as a finding rather than rushing all five. (Per the single-bounded-
session rule: partial-but-coherent beats complete-but-lost-coherence.)

## §7 — Success criteria

- The decomposition **reconciles**: ghost-market-stamped + genuine-
  market-stamped + ghost-no-market(range) + genuine-no-market = the
  §5.2 baseline (within the stated no-market error bar).
- A single headline number: of the recoverable deficit, **X is ghost
  (un-fillable), Y is genuine (recoverable)** — with the market-stamped
  portion precise and the no-market portion ranged.
- §5.5 returns a clear yes/no on the hypothesised cross-source pattern,
  with worked rows.

## §8 — Output spec

Single file: `placings_deficit_fragment_floor_report.md` (rebuild root).
Sections: baseline; regime-1 (market-stamped) decomposition table;
regime-2 (no-market) ranged decomposition + stated assumptions;
worked-pattern tables (§5.5); a reconciliation table proving the splits
sum to baseline; self-assessment (what's proven, what's approximate,
what budget/scope limited). Rough length 200–350 lines. **Contains no
recommendations, no fix proposal, no overall verdict** — measurement
only; interpretation is the next operator-Claude session's job.

## §9 — Hard limits (non-negotiable)

- **No fix.** No fragment collapse, no runner union, no read-time or
  write-time identity enforcement — those are the DR-034 stance-4
  remediation, a future brief.
- **No schema change, no migration, no index creation.**
- **No writes to capture.db**; **no recovery/backfill pass**; **no
  ingest changes.**
- **No venue-harmonisation build** (Fix 5) to tighten §5.4 — report the
  range instead.
- **No git operations**; no source-tree edits; `git status` unchanged
  at close.
- **Never copy the DB** (WAL) — query in place, `mode=ro`.
- **No mid-session operator escalation** — run end-to-end, surface
  findings in the report.

## §10 — What happens after Code's session

Next operator-Claude (Chat) session reads the report and decides: (a)
whether the ghost floor is material enough to adjust the stall-alert
threshold / re-read the burndown's nights-to-clear against the corrected
target; (b) whether to prioritise the DR-034 stance-4 collapse
remediation (its own future brief) now or let it wait for §C/§D. Code
does **not** write that next brief.

## §11 — Cross-references

- **DR-034** stance 4 (fragment-collision; read-time collapse) — the
  governing record this measures against.
- **DR-033** (placings analytical, Betfair operational) — the deficit
  is capture-side analytical only; bet-safe.
- `BETHUB_DATA_REFERENCE.md` §B.5 / §B.7 (fragmentation mechanism +
  fragment-collision rule).
- `recovery_run_report.md` R-1 (41,340 deficit), R-2 (timer/quota burn
  caveat) — the burndown this corrects the target for.
- `placings_landing_fix_report.md` §2 (name-key runner identity).
- **Parking-lot excluded:** the fragment-collapse remediation itself;
  Fix 5 venue harmonisation; the 34.8% start-less discovery shells
  (no runners ⇒ contribute no deficit runners); persisting the
  Racing-API race id (DR-034 stance 5 remediation).
