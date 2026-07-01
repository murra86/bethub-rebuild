# Placings deficit — fragment-floor measurement report

**Brief:** `placings_deficit_fragment_floor_brief.md` (LOCKED — Session 206).
**Type:** Empirical measurement / inspection. Read-only, capture-side analytical
only (DR-033), bet-safe. **No recommendations, no fix, no verdict** — measurement
only; interpretation is the next operator-Claude session's job (brief §10).
**Measurement wall-clock:** 2026-06-30 12:22 ACST. **DB snapshot:** `now`(UTC)
= 2026-06-30; live recent-window cutoff `date('now','-14 day')` = 2026-06-16.
**Access:** `capture.db` opened `mode=ro`, queried in place via SSH-stdin Python
(`file:…?mode=ro`); the file was never copied (WAL+SHM live). No writes, no
recovery pass, no schema/index/migration, no git operations, no VPS source-tree
edits.

---

## 0. How to read this report

The recoverable placings deficit is decomposed into **GHOST** (the physical race
is already resulted on a *sibling* capture fragment sharing the same race
identity, so the nightly backfill can never clear the NULL-position in-scope
runners) versus **GENUINE** (no resulted sibling exists — truly recoverable). The
**market-stamped** portion (DR-034 Betfair-WIN-market spine) is measured
**precisely**; the **no-market** portion (second-class derived key) is **ranged**
with an explicit error bar, because precise sibling-merging there needs
venue-harmonisation (Fix 5), which is out of scope (brief §5.4 / §9).

---

## 1. §5.1 — Schema + path discovery (grounding)

**Canonical DB path** (confirmed against code, not assumed):
`/home/racing/racing-data-capture/data/capture.db` — the path
`scripts/backfill_race_metadata.py` and the storage layer resolve to
(`PROJECT_ROOT/data/capture.db`). Live `capture.db-wal` + `capture.db-shm`
siblings present; `PRAGMA journal_mode` = `wal`. Opened read-only; never copied.

**Brief-named columns → live columns** (all present; minor name notes):

| Brief reference | Live column(s) | Note |
|---|---|---|
| `races.id`, `race_date`, `venue_normalised`, `race_number` | same | natural-key components |
| `betfair_win_market_id` | `races.betfair_win_market_id` (TEXT) | the DR-034 spine stamp |
| `scheduled_start` | `races.scheduled_start` (TEXT, ISO-8601 UTC, e.g. `2026-06-06T…Z`) | source of the Adelaide-local derived date |
| status field | `races.capture_status` (PENDING/SETTLED…) and `races.state` | "status" in B.5's worked table = `capture_status` |
| `race_class`, trial/jump-out flags | `race_class` (TEXT), `is_trial` (INT), `is_jump_out` (INT) | brief's "non-trial/non-jump-out" = `is_trial=0 AND is_jump_out=0` |
| `runners.finish_position`, `scratched`, `runner_key`, `betfair_selection_id` | same | |
| runner name field | `runner_name`, `runner_name_normalised` | |
| `result_status`, results source | `result_status`, `results_source` (`subscription` / `betfair_only` / NULL) | `results_source` is the cross-source discriminator used in §5 |

**Exact deficit predicate, as live SQL** (mirrors `_recoverable_deficit` /
`get_backlog_dates` in `scripts/backfill_race_metadata.py`, verbatim incl. the
dynamic recent-window cutoff and the exhausted-date exclusion):

```sql
SELECT COUNT(*)
FROM races ra JOIN runners ru ON ru.race_id = ra.id
WHERE date(ra.race_date) >= date('2026-03-15')          -- BACKLOG_RECOVERY_FLOOR
  AND date(ra.race_date) <  date('now','-14 day')        -- recent-window cutoff (= 2026-06-16 today)
  AND ra.is_trial = 0 AND ra.is_jump_out = 0
  AND ra.race_class IS NOT NULL
  AND ru.finish_position IS NULL AND ru.scratched = 0;
-- minus dates flagged "exhausted" in data/backlog_trickle_state.json
```

**Exhausted-date set is empty** at this snapshot (the trickle sidecar holds 20
date keys, none with `exhausted=true`; `BACKLOG_FREEZE_RETIRE=False`). So no date
is excluded by the retirement clause and the baseline is the pure predicate above.

No column or path mismatch required a deviation; nothing was guessed.

---

## 2. §5.2 — Baseline (the number every split reconciles to)

| Scope | Deficit runners | Distinct race_dates |
|---|---|---|
| **Recoverable (predicate above)** | **41,633** | **91** |
| — Regime 1: race carries `betfair_win_market_id` | 34,442 | — |
| — Regime 2: race has no market id | 7,191 | — |
| Regime sum check | 34,442 + 7,191 = **41,633** | ✓ exact |

The recovery-run report (R-1, 2026-06-29) recorded **41,340 / 90 dates**. This
snapshot reads **41,633 / 91 dates**, **+293 / +1 date** — consistent with the
brief's "≈ 41,340 ± nightly burn": the dynamic `date('now','-14 day')` cutoff has
advanced from 2026-06-15 to 2026-06-16, pulling one more formerly-recent date into
the recoverable window, and the nightly burn has been ≈0 (R-1/R-2: quota-walled).
The decomposition below reconciles to **41,633**, this snapshot's baseline.

The 34,442 market-stamped deficit runners sit on **3,550 distinct race rows** but
only **3,506 distinct market ids** — i.e. fragmentation is already visible inside
the deficit itself (44 markets contribute deficit runners from more than one
fragment). Of the 3,506 markets, **3,448 (98.3%) are fragmented** (>1 capture row
shares the market id) — confirming DR-034's 87%-fragmentation backdrop holds, and
is in fact higher, within the deficit population.

---

## 3. §5.3 — Regime 1: market-stamped ghost deficit (PRIMARY, precise)

**Method.** Group all capture rows by `betfair_win_market_id` (the DR-034 spine).
A deficit runner is **GHOST (market-stamped)** iff a **sibling** capture row
(distinct `races.id`, same market id) carries ≥1 finishing position — the physical
race is resulted on a sibling fragment, so the backfill (which writes per
race-row) can never fill this NULL row. Otherwise the runner is **GENUINE
(market-stamped)**. "Resulted" = the fragment has ≥1 runner with
`finish_position IS NOT NULL`. Own-row results do **not** make a runner ghost
(that is a fillable same-fragment partial, isolated in §3.1).

### Regime-1 decomposition

| Class | Deficit runners | Distinct market ids |
|---|---|---|
| **GHOST — resulted sibling exists (un-fillable)** | **104** | **9** |
| **GENUINE — no resulted sibling (recoverable)** | **34,338** | 3,497 |
| **Regime-1 total** | **34,442** | 3,506 |

Sum check: 104 + 34,338 = **34,442** ✓.

The market-stamped ghost floor is **104 runners (0.30% of regime 1)** concentrated
in **9 market ids**. The 9 ghost groups are, by hand from §3.2, Gatton R5 (11) +
Swan Hill R1–R8 (7+14+14+6+12+12+14+14 = 93) = **104** ✓.

### 3.1 — Why "genuine" is genuine: the result isn't anywhere yet

Of the 34,338 genuine market-stamped runners:

| Sub-class | Runners | Reading |
|---|---|---|
| **No fragment in the market group is resulted at all** | **34,312** | the physical race is **not resulted anywhere** — a true backlog miss, fully recoverable |
| Own fragment partially resulted (runner-level duplicate, no resulted sibling) | **26** | result landed on a *different runner row of the same fragment* (the RC-2 within-fragment duplicate; see note) |

Only **19** of the 3,506 deficit-bearing market ids are resulted **anywhere** in
their group: **9** with the result on a *sibling* (→ ghost) and **10** with the
result only on the deficit fragment's *own* row (→ the 26 within-fragment-partial
runners). The remaining **3,487** markets carry **no finishing position on any
fragment** — the race simply has not been resulted yet. This is the empirical
signature of R-1/R-2: the backfill is quota-walled (≈0 burn), so the deficit is
overwhelmingly *un-run*, not *un-fillable*.

> **Note (within-fragment duplicate, 26 runners).** These are a runner-level, not
> race-level, phenomenon: one race row holds both a resulted runner (e.g. an
> `S:`/subscription row) and a NULL in-scope incumbent (e.g. a Betfair `N:` row) —
> the exact RC-2 corruption-avoidance case from `placings_landing_fix_report.md`
> §3.2. They are **not** ghosts under the brief's sibling definition (no distinct
> sibling row carries the result), so they remain inside GENUINE for reconciliation.
> Flagged here because they share the ghost's "result lands on a different identity
> than the NULL runner" character at the runner grain.

---

## 4. §5.5 — Worked-pattern confirmation (the cross-source split)

**Hypothesis (brief §5.5):** a **Betfair-stamped fragment** whose `selection_id`
runners are NULL, paired with a **subscription sibling** carrying positions under
**name keys** (`S:<name>`/`N:<n>`, `results_source='subscription'`).

**Verdict: CONFIRMED in substance, REFUTED in its precise key-form.** All 9 ghost
groups are one physical race split across **two `race_date` fragments** (the B.5
±1-day drift), same venue, same race number; the result sits on the
`results_source='subscription'` fragment while the NULL in-scope runners sit on a
`results_source='betfair_only'` sibling that shares the market id — un-fillable by
a per-row backfill. **But the runners on *both* fragments use `N:<number>` keys —
no `S:<name>` keys appear in any ghost group.** The split axis is
`subscription` vs `betfair_only` across a date-drifted sibling, not the
`S:`/`N:` runner-key collision the hypothesis named.

**Worked market 1 — Gatton R5, market `1.258793562`** (the resulted sibling is a
pure subscription/natural-key row — no Betfair selection ids):

| Fragment | id | race_date | status | `results_source` | runner rows (sample) |
|---|---|---|---|---|---|
| **Resulted sibling** (`has_subscription_sync=1`) | 1890793 | 2026-06-02 | PENDING | subscription | `N:3 Spotted` fin=1, `N:4 Underpin` fin=2, `N:1 At Church` fin=3 — `selection_id=None` |
| **Deficit/NULL** (`betfair_only`) | 1901925 | 2026-06-03 | SETTLED | betfair_only | `N:1 Waverley` sel=28406568 fin=NULL, `N:2 Whatjeudoin` sel=98925547 fin=NULL … (11 runners, **11 in-scope NULL → ghost**) |

**Worked market 2 — Swan Hill R1, market `1.258933045`** (here the subscription
sibling *also* carries selection ids — fully Betfair-matched — yet the
date-drifted Betfair sibling still stays NULL):

| Fragment | id | race_date | status | `results_source` | runner rows (sample) |
|---|---|---|---|---|---|
| **Resulted sibling** (`sub=1`) | 1996123 | 2026-06-06 | SETTLED | subscription | `N:2 Iron Legacy` sel=3213453 fin=1, `N:7 Baudin` fin=2, `N:6 Spicy Apple` fin=3 … (10 runners resulted) |
| **Deficit/NULL** (`betfair_only`) | 2025741 | 2026-06-07 | SETTLED | betfair_only | `N:1 Boyd` sel=99242550 fin=NULL, `N:2 Induction` fin=NULL, `N:3 Scoobartie` fin=NULL … (**7 in-scope NULL → ghost**) |

**Worked market 3 — Swan Hill R3, market `1.258933061`:** identical shape —
resulted subscription fragment `1996125` (2026-06-06), NULL `betfair_only` sibling
`2025743` (2026-06-07), **14 in-scope NULL → ghost**.

The 9 ghost groups are essentially **two meetings**: Swan Hill 2026-06-06/-07
R1–R8 (8 markets, 93 runners) and Gatton 2026-06-02/-03 R5 (1 market, 11 runners).
This is a narrow, localized date-drift artefact at this snapshot, not a broad
systemic floor.

---

## 5. §5.4 — Regime 2: no-market ghost deficit (SECONDARY, ranged)

**Method & assumptions.** The 7,191 no-market deficit runners (871 races) have
**no Betfair spine**, so siblings can be matched only by the second-class derived
key: **`scheduled_start`→Adelaide-local date** (UTC→`Australia/Adelaide` via
`zoneinfo`, DST-correct across the 2026-04-05 ACDT→ACST change, per DR-021/B.4) **+
venue + race number**. All 871 races have `scheduled_start` populated (0 NULL), so
**none falls to B.6's weak path** — every one is matchable in principle. A
no-market deficit runner is **ghost** iff a distinct race row sharing the derived
key is resulted (the resulted sibling may itself be market-stamped or no-market).
Precise venue-merging needs Fix 5 (not built); the result is therefore a **range**:

| Bound | Venue-match rule | Ghost runners | Ghost races |
|---|---|---|---|
| **Lower** | **exact** `venue_normalised` string | **7** | 1 |
| **Upper** | **spelling-tolerant** same venue (bookmaker-prefix / suffix-token strip) | **707** | 89 |
| *(loose ceiling, flagged)* | date+race# **venue ignored entirely** | *2,472* | *322* |

**The defensible range is [7, 707].** The lower bound (exact venue) catches only
date-drift siblings whose venue string is byte-identical (the single case:
Devonport Tapeta R7, 2026-06-14, 7 runners). The upper bound (707) adds
venue-**spelling**-drift siblings — validated as genuine same-race pairs, e.g.
`sportsbet longreach` R1–R5 ↔ `longreach` R1–R5 (same Adelaide date 2026-03-21,
same race numbers, bookmaker-prefixed deficit row vs clean-venue resulted sibling,
sib `market_id=None`), and `sportsbet mount isa` ↔ `mount isa`.

**Why the loose ceiling is excluded from the range.** Ignoring venue entirely
yields 2,472, but **1,765 of those runners match *only* across a different venue**
(a genuinely different physical race that happens to share the Adelaide date and
race number) — spurious by construction. 2,472 − 1,765 = 707, exactly the
spelling-tolerant figure. So 2,472 is reported only as an over-counting absolute
ceiling, not as the upper bound. The spelling-tolerant comparison is a deliberately
crude proxy (lowercase, strip a fixed bookmaker-prefix list and a small
track-suffix word list, compare the residual token) — **not** a Fix-5 harmonisation
build; it exists only to bracket the range.

| Class | Ghost runners | Genuine runners |
|---|---|---|
| Regime 2 at lower bound | 7 | 7,184 |
| Regime 2 at upper bound | 707 | 6,484 |

---

## 6. Reconciliation (splits sum to baseline)

| Regime | Ghost (un-fillable) | Genuine (recoverable) | Regime total |
|---|---|---|---|
| **1 — market-stamped** (precise) | **104** | **34,338** | 34,442 |
| **2 — no-market** (ranged) | **7 … 707** | **7,184 … 6,484** | 7,191 |
| **TOTAL** | **111 … 811** | **41,522 … 40,822** | **41,633** |

- Market-stamped: 104 + 34,338 = 34,442 ✓
- No-market: [7..707] + [7,184..6,484] = 7,191 ✓ (complementary within the regime)
- Grand total ghost+genuine = 34,442 + 7,191 = **41,633** = §5.2 baseline ✓

**Headline.** Of the **41,633** recoverable placings deficit at this snapshot:
- **GHOST (un-fillable — resulted on a sibling fragment): ≈ 111 – 811 runners**
  (market-stamped portion precise at 104; no-market portion ranged 7–707), i.e.
  **0.3% – 1.9%** of the deficit.
- **GENUINE (recoverable): ≈ 40,822 – 41,522 runners (98.1% – 99.7%)** — of which
  34,312 market-stamped races are not resulted on *any* fragment.

---

## 7. Self-assessment

**Proven (precise).**
- The baseline (41,633 / 91 dates) reproduces `_recoverable_deficit` exactly, incl.
  the dynamic cutoff and the (empty) exhausted-date exclusion; it reconciles to
  R-1's 41,340 within the stated nightly-burn / cutoff-advance tolerance.
- The regime split (34,442 / 7,191) and the **market-stamped ghost = 104 / 9
  markets** are exact set computations, hand-verified against the per-fragment
  deficit counts.
- §5.5 returns a clear yes/no: the cross-source sibling pattern is **confirmed**
  (subscription-resulted sibling vs `betfair_only` NULL sibling, same WIN market,
  un-fillable) and the specific `S:`-name-key form is **refuted** (both fragments
  use `N:` keys; the split is `race_date` drift + `results_source`).

**Approximate (bounded, by design).**
- The no-market ghost is a **range [7, 707]**, not a point: exact-venue is a hard
  floor; the spelling-tolerant 707 depends on a crude venue proxy that could both
  miss harder spelling variants (under-count) and, less likely, over-merge
  (the validated samples were all genuine same-race pairs). Tightening this is
  Fix 5, explicitly out of scope. The 2,472 venue-ignored figure is an over-count
  (≈1,765 spurious) and is not part of the range.

**Scope / limits.**
- This is a **single snapshot** (2026-06-30 12:22 ACST). The ghost floor is small
  *now* largely because so few races are resulted *anywhere* yet (R-1/R-2 quota
  wall): only 19 market-stamped groups and ≤89+1 no-market races are resulted on a
  sibling. As the backfill lands more subscription results on natural-key
  fragments, each newly-resulted fragment whose date/venue-drifted sibling stays
  NULL would convert genuine→ghost — so 111–811 is a *floor at this moment*, not a
  structural ceiling. Re-measuring after material burn would show the trend.
- "Resulted" was defined as `finish_position IS NOT NULL` on any runner of a
  fragment; a fragment with only scratched/void results is treated as resulted if
  any position is non-NULL (consistent with how the deficit predicate itself reads
  positions).
- No fragment collapse, runner union, venue harmonisation, schema/index change,
  recovery pass, or git operation was performed. All `capture.db` access was
  `mode=ro`, in place, via SSH-stdin Python; nothing was written to the VPS
  source tree (every query ran from stdin, no file created on the host), so the
  racing-data-capture tree is byte-identical and no git command was issued.

*Measurement only — no recommendation, no fix proposal, no overall verdict. The
next operator-Claude session reads this and decides on the stall-alert threshold /
burndown re-read and on prioritising the DR-034 stance-4 collapse remediation
(brief §10).*
