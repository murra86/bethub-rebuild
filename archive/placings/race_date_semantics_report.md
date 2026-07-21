# Report — race_date population-rule diagnostic

**Brief:** `race_date_semantics_brief.md` — LOCKED, sha256 prefix
`c1f53f68` (verified at session start; matched).
**Status:** EXECUTED — read-only diagnostic. No edits, no writes, no
restart, no git ops. `capture.db` opened `mode=ro` throughout.
**Session:** 2026-06-30, ~09:35–09:50 ACST (DR-021 Adelaide, ACST =
UTC+9:30). Target `root@187.77.183.9` : `/home/racing/racing-data-capture`.
**Bet-safety:** CLEAN — analytical layer only (DR-033).

**Headline:** `race_date` has **no single clean real-world-day
semantics**. It is set by whichever of two ingest paths inserts the row
first, and the two paths use *different rules that skew in opposite
directions*. ~73% of rows (that have a start time) align with the
Adelaide-local date of the race; ~27% are off by ±1 day, and a third of
all rows have no `scheduled_start` to cross-check at all. The client
contract (§4) must therefore be a window-plus-refine, not a 1:1 map.

---

## 1 — The population rule (§5.1)

`race_date` is **never derived from the race's start instant**. It is a
*provenance-stamped query/clock date* from one of two writers, both of
which feed `upsert_race()` (`storage/database.py:316`), whose conflict
key is `UNIQUE(race_date, venue_normalised, race_number)` and which
**never updates `race_date` on conflict** (`database.py:334` skips it
from the SET clause). So `race_date` is owned by the *first* inserter.

**Path A — Subscription sync** (the bulk historical/enrichment path):

    # subscription/racing_api.py — sync_day(conn, date_str, ...)
    meets_data = _api_get("/australia/meets", params={"date": date_str})   # L193
    ...
    race_id = upsert_race(conn, race_date=date_str, ...                     # L287
                          scheduled_start=race.get("off_time"), ...)        # L301

`race_date = date_str` = the date passed to the upstream Racing API
`/australia/meets?date=`. It is the **API's own meeting-date grouping**,
copied verbatim — not parsed from `off_time`. Callers
(`scripts/backfill_subscription.py:84`, `backfill_race_metadata.py:270`)
generate `date_str` by iterating `datetime.now().date()` backwards.

**Path B — Live orchestrator** (discovery/capture, live from 2026-03):

    # capture/orchestrator.py
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")            # L204
    matched_races = match_races(..., race_date=today_str)                  # L257
    # matcher stamps it through: race_matcher.py:243 / 336 "race_date": race_date
    race_id = upsert_race(self._conn, **race_fields)                       # via _persist_race L307

`race_date = datetime.now(timezone.utc)` date **at discovery time**.
Discovery runs up to 12 h *ahead* of the race (`to_dt = utc_now +
timedelta(hours=12)`, L210), so a race in the early-UTC hours discovered
the prior UTC evening is stamped with the **previous** UTC date. A
second sub-path (`orchestrator.py:318 race_date=race_data.get("race_date","")`)
carries the same `today_str` through the matched payload.

**Read side** (`api/routes/races.py`, confirmed Brief 1 v2): a bare
string match `WHERE race_date = ?`. No normalisation — the client gets
exactly the rows whose stored string equals what it passes.

**Verdict:** copied-as-is source date, two sources. Path A = upstream
API meeting date; Path B = UTC clock date at discovery (skewable up to a
day early). Neither is the Adelaide-local date of the race by
construction; alignment is incidental.

---

## 2 — Cross-era pattern (§5.2)

Offsets computed read-only over the **58,858 rows that have a
`scheduled_start`** (the other 31,472 have none — see §5). Offset =
`date(start) − race_date` in days. UTC offset is exact (UTC suffix on
every start); Adelaide offset adds +9:30 (DST caveat in §5).

**Adelaide-local date vs `race_date`** (Q2):

| offset (days) | n | share |
|---|---|---|
| −1 (`race_date` = day *after* race) | 7,728 | 13.1% |
| **0 (aligned)** | **42,733** | **72.6%** |
| +1 (`race_date` = day *before* race) | 8,386 | 14.2% |
| −4/−3/+2 (noise) | 13 | <0.1% |

**Not consistent across eras or paths.** The +1 bucket is **absent
before 2026-03 and appears the same month the live path goes live**
(Q3) — and segmenting by provenance flags (Q4) shows the two paths skew
*opposite ways*:

| provenance | −1 | 0 | +1 |
|---|---|---|---|
| subscription-only | 6,263 | 26,113 | **26** |
| live-captured | 84 | 12,686 | **7,192** |

- **Subscription path → offsets 0 / −1 only** (never +1). race_date is
  the Adelaide date or one day *later* (late/overnight meetings the API
  files under the following day).
- **Live path → offsets 0 / +1** (the 12 h-early UTC stamping). race_date
  is the Adelaide date or one day *earlier*.

**State-dependent** (Q10): WA 100% aligned, NZ 100%, NSW 96%, QLD 92%,
SA/TAS ~98%; **VIC is split ~49% offset −1 / ~51% aligned** (6,429 vs
6,598) — VIC night/twilight meetings dominate the −1 tail. International
(HK, NZ, ARG, BRA, US states…) are ~all aligned.

**Sample spans** (Q5) show the spread directly:

| race_date | n | min start (UTC) | max start (UTC) |
|---|---|---|---|
| 2025-03-03 | 74 | 2025-03-02T13:00Z | 2025-03-03T09:21Z |
| 2026-01-01 | 84 | 2026-01-01T01:51Z | 2026-01-01T10:19Z |
| 2026-06-15 | 465 | 2026-06-14T14:00Z | 2026-06-16T11:20Z |
| 2026-06-28 | 560 | 2026-06-28T00:08Z | 2026-06-29T10:09Z |

A single `race_date` value can span **~45 h of real start times** (e.g.
2026-06-15: 2026-06-14T14:00Z → 2026-06-16T11:20Z). The 2026-06-28
"Redcliffe" rows that triggered this brief (start 2026-06-29 morning
UTC, filed under 06-28) are the live-path +1 case, confirmed.

---

## 3 — `scheduled_start` encoding inventory (§5.3)

Three distinct string encodings, **all explicit-UTC** (Q7/Q8). A Brief-2
parser must accept all three:

| len | format | example | n | era / source |
|---|---|---|---|---|
| 24 | `Z`, 3-digit millis | `2025-03-02T22:00:00.000Z` | 29,824 | all eras (Racing API off_time) |
| 28 | `Z`, **7-digit** fraction | `2025-03-02T13:00:00.0000000Z` | 12,232 | all eras (Racing API off_time, alt field) |
| 25 | `+00:00`, no fraction | `2026-03-02T05:34:00+00:00` | 16,802 | **from 2026-03** (live/Betfair path) |

**Parser hazard:** the 28-char **7-digit fractional-seconds** form is
**not accepted by Python `datetime.fromisoformat()`** (it takes 3 or 6
fractional digits only, even on 3.11+). Brief 2 must truncate the
fraction to ≤6 digits (or regex-strip it) before parsing, and must
handle both `Z` and `+00:00` zone suffixes. All three are UTC, so once
parsed the instant is unambiguous.

Empty/unset `scheduled_start`: **31,472 of 90,330 (34.8%)** — see §5.

---

## 4 — Client query contract (§5.4) — AMBIGUOUS; candidates laid out

The data does not support a single clean mapping, so per the brief I lay
out the candidates rather than force one.

**Candidate A — single call `?date=D` (D = Adelaide-local date).**
Cheapest. Catches the ~73% of a day's races whose `race_date` already
equals D; **misses** the ±1-day tail (notably ~half of VIC, and all
post-2026-03 live-only/shell rows that skew early) and **includes** some
spill from the neighbouring real days. Recall is venue-dependent:
~95–100% for WA/NSW/QLD/NZ/SA/TAS, **~50% for VIC**.

**Candidate B — window + refine (RECOMMENDED).** In one explicit
sentence:

> To retrieve the races that ran on Adelaide-local day **D**, the client
> should call the endpoint for **D−1, D, and D+1**, union the results,
> then **keep a row when**: (a) its `scheduled_start` is present and,
> converted from UTC to Adelaide local, falls on day D; **or** (b) its
> `scheduled_start` is empty, in which case fall back to keeping only
> rows whose stored `race_date == D`.

Rationale: `scheduled_start` is the **one trustworthy field** (always
explicit UTC) and exists on essentially all enriched rows (subscription
+ live capture). The ±1-day window guarantees the tail is fetched; the
UTC→Adelaide refine removes the spill precisely. The empty-start
fallback (clause b) is unavoidable — those 31k rows have no instant — and
is low-cost because they are overwhelmingly the non-enriched discovery
shells (no runners; §5), which a "what ran today" client view will
mostly drop anyway.

**Do not** trust `race_date` alone as a real-world-day key for anything
requiring completeness across VIC or post-2026-03 live rows.

---

## 5 — Self-assessment

**The empty-`scheduled_start` third (intersects Brief 1's `n_runners:0`
note).** 31,472 rows (34.8%) have no start. They are almost entirely the
`- -` provenance class (30,948) — neither subscription-synced nor
live-captured — and appear **only from 2026-03** (0 before; ~10k/month
after). These are live-orchestrator **discovery shells**: a row was
upserted with `race_date = UTC-today` but capture/sync never completed,
so no `off_time` and (per Brief 1, e.g. Healesville 2026-06-28) no
runners. They are addressable only by `race_date`, and that `race_date`
is the skew-prone live value. Whether they should exist at all is a
data-quality question for operator-Claude — **not fixed here** (§9).

**DST caveat (declared limitation).** The Adelaide offset (§2 Q2/Q3/Q10)
uses a fixed +9:30 (ACST) and does **not** model ACDT (+10:30, ~Oct–Apr)
or VIC/NSW AEDT. This can mis-place a race within ~1 h of Adelaide
midnight in summer months by one day. It does **not** affect the
structural findings: the +1 bucket tracks the 2026-03 *path* change, not
season (it would otherwise appear symmetrically every summer, which it
does not), and Australian races rarely run near local midnight. The
exact ±1 boundary for a handful of near-midnight summer races is the one
thing this probe cannot pin precisely — flagged, not silently dropped.

**Outliers.** 13 rows at offset −4/−3/+2 (Q1/Q2) — negligible noise
(likely backfill re-files or bad source `off_time`); not characterised
further.

**Confidence.** §5.1 rule: high (read from source, both paths quoted).
§5.2 pattern: high (full-table counts, segmented by era/provenance/state).
§5.3 inventory: high (exhaustive by length+suffix). §5.4 contract: the
*ambiguity* is certain; Candidate B is the robust resolution but its
exact recall on near-midnight summer rows carries the DST caveat above.

**Scope adherence.** Read-only throughout: `cat`/`sed`/`grep` on source,
`sqlite3 -readonly` on the DB. No file edits, no DB writes, no schema
change, no service restart, no git operations, no `race_date` repair, no
Brief-2 work. One off-repo scratch SQL file was used locally (not on the
repo). Single bounded session.

*Report landing complete — this unblocks Brief 2 (the §4 contract is its
input).*
