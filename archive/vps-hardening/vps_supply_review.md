# VPS supply-side review — `capture.db` fit-for-purpose

**Executed:** 2026-06-25 ~20:50 ACST (single bounded read-only Code session, per `vps_supply_review_brief.md`).
**Mode:** READ-ONLY. capture.db opened `file:…?mode=ro` over SSH `python3`, queried in place, never copied. No writes, no service touched, no v3 code edited.
**Scope:** every read v3's `vps_client` makes against `capture.db`, graded schema-truth + data-fitness → one verdict each. Finish-position gap quantified (not fixed). Capture liveness checked.

---

## 1. Run header

| Item | Value |
|---|---|
| Step-0 SSH gate | **PASS** — `ssh racing-vps 'echo ok'` → `ok` (exit 0), via operator `ssh-agent`. |
| capture.db path | `/home/racing/racing-data-capture/data/capture.db` |
| Size | **3.97 GB** (3,975,454,720 bytes); was 2.05 GB at W1 (2026-05-05) — growing. |
| WAL state | Live WAL — `-wal` 4.55 MB + `-shm` 32 KB present; `journal_mode=wal`. |
| RO enforcement | Connection opened `mode=ro` (writes blocked at file-open). `PRAGMA query_only` reports `0` (a separate session toggle, not the RO-URI guarantee); no write statement was issued. |
| VPS wall-clock | `2026-06-25T11:20:43Z` (= 20:50 ACST). Used to validate freshness. |
| `/health` (via tunnel) | `status:ok, collector_active:true`, betfair_last_snapshot `2026-06-25T11:12:35Z`. |
| capture.db stores | UTC ISO strings; all times below converted to ACST (UTC+9:30, no DST in June). |

---

## 2. §5.1 — Schema-truth table (gates everything below)

Every column the eight `vps_client` methods query is **present** in the live schema. No table renamed, no column dropped vs the W1 reference. **Every read can run.**

| Table | Rows (live) | Date span | Client cols req/present | Status |
|---|---|---|---|---|
| `races` | 88,072 | `race_date` 2025-03-03 → 2026-06-25 | 16 / 16 | ✅ all present |
| `runners` | 530,070 | (joined via `races`) | 17 / 17 | ✅ all present |
| `betfair_snapshots` | 3,220,600 | `snapshot_time` 2026-03-02 → 2026-06-25 (live) | 13 / 13 | ✅ all present |
| `betfair_historical` | 163,809 | `meeting_date` 2025-03-01 → **2026-02-28** (frozen) | 3 / 3 | ✅ present, static |

Tables present: `races, runners, betfair_snapshots, bookmaker_snapshots, betfair_historical, snapshot_batch_summary, daily_calibration_summary` (+`sqlite_sequence`). New cols since W1 (e.g. `races.state, race_name, subscription_synced_at, has_subscription_sync`; bookmaker `*_race_id` columns) are additive — no breakage.

**Two store-wide facts that drive every verdict below:**
- **`betfair_win_market_id` — the stamp every §9.1–§9.6 read joins on — is populated on only 19.9% of races** (17,570 / 88,072). Betfair capture began 2026-03-02; pre-March races (incl. all of Jan–Feb 2026: 0% stamped) carry no stamp. Recent months: Mar 45.3%, Apr 28.2%, May 26.3%, Jun 27.5%.
- **`capture_status` is `PENDING` on 81.8%** of races (SETTLED 17.9%, TIMEOUT 0.3%). Three metadata reads treat `PENDING` → `NOT_YET_CAPTURED` (unavailable). Among *stamped* races it inverts: SETTLED 87.6%, PENDING 12.1%.

---

## 3. §5.2–§5.3 — Per-read fit table

| # | Read (method) | Tier | Verdict | Evidence |
|---|---|---|---|---|
| 1 | Race lookup (`list_meetings`/`list_races`/`resolve_race`) | near DEEP | **fit-with-gap** | Resolves end-to-end (worked ex. §3.1). 87.5% of stamped races (last 30d) resolve to ≥1 runner; runner `betfair_selection_id` coverage 95.9% on snapshotted stamped races. Gaps: (a) only ~20% of all races stamped (recent ~27%); (b) **matched-but-not-snapshotted races resolve to an *empty* runner list** — see Finding A; (c) greyhound/harness venues surfaced & mislabelled — Finding C. |
| 2 | Finish results (`race_results`) | near DEEP | **fit-with-gap** | Query runs; returns settled runners. `result_status` (WINNER/LOSER, Betfair-sourced) **94.9%** of stamped-race runners last 30d → **fit for win/lose auto-settlement (W6.5)**. But `finish_position` **0.0%** recent → **not fit for the place/ordinal (insurance 2nd–4th) trigger**. Intersects §5.4. |
| 3 | Race classification (`race_metadata`) | near DEEP | **fit-with-gap** | For SETTLED enriched thoroughbred races, class/dist/surface/cond populated (worked ex. §3.2). But `race_class`+`distance` on only **28.3%** of stamped races last 30d (harness/greyhound + unsynced thoroughbred carry neither); `track_type` 100% (inferred from venue). `capture_status=PENDING` races return `NOT_YET_CAPTURED` even when fields exist. |
| 4 | Runner detail (`race_runners`/`runner_metadata`) | analytical LIGHT | **fit-with-gap** | Present & correctly shaped — `name`/`selection_id`/`scratched` populated. Enrichment faded with the subscription gap: barrier/weight/jockey **~16–20%**, `form_string` **~0.1%** by Jun (vs ~70–93% through Feb). `driver` always `None` (harness not mapped). |
| 5 | BSP (`runner_bsp`) | analytical LIGHT | **fit** | Present & shaped. Live path works: worked runner `sp_fixed=NULL` → falls back to `betfair_snapshots.bsp_price=160.0` (final snapshot). `betfair_historical` fallback **confirmed frozen at 2026-02-28** (one-shot import stamped `created_at 2026-03-02 11:12`) — covers pre-March only, as documented; recent BSP rides live snapshots. |
| 6 | Price curve (`race_bracketing`) | analytical LIGHT | **fit** | Present & shaped. Worked race: 126 snapshots across 7 runners, 10:04→11:07Z. `betfair_snapshots` 3.22M rows, live to the minute; indices `idx_bf_race_runner`/`idx_bf_race_time` intact. |
| 7 | Identity resolution (`identity_resolve`) | analytical LIGHT | **fit** | Present. `(betfair_win_market_id, betfair_selection_id)` join succeeds on worked race (`resolved=YES`); bogus market → 0 rows → `GENUINE_ABSENCE` (terminal path correct). |

### §3.1 Worked example — race lookup (the "Log Past Bet" path)
`resolve_race("2026-06-25","Ballarat",8)` → mkt `1.259422704`, **7 runners all with `selection_id`** (Etiz Amodel/Easy Rolling/Dot Ball…). `list_meetings("2026-06-25")` → 60 venues; `list_races` → 8 races, 8 stamped. End-to-end date→venue→race→market+runners **succeeds**.

### §3.2 Worked example — classification
Ballarat R8 (2026-06-24, SETTLED): `race_class=BM66, distance=2000, surface=turf, condition=Heavy` — fully populated. (Same race's runners carry NULL barrier/weight/jockey — runner enrichment absent; see read #4.)

---

## 4. §5.4 — Finish-position gap (QUANTIFIED — not fixed)

**The fade curve** (runners by race month; `finish_position` is the Racing-API ordinal, `result_status` is mostly Betfair WINNER/LOSER):

| Month | Runners | `finish_position` % | `result_status` % | src=subscription % |
|---|---|---|---|---|
| 2025-11 | 26,833 | 76.9% | 96.5% | 96.5% |
| 2025-12 | 25,058 | 79.2% | 98.1% | 98.1% |
| 2026-01 | 24,611 | 79.5% | 98.0% | 98.0% |
| 2026-02 | 22,721 | 79.9% | 97.4% | 97.4% |
| 2026-03 | 67,297 | **21.2%** | 75.2% | 25.5% |
| 2026-04 | 56,964 | **6.4%** | 80.6% | 7.4% |
| 2026-05 | 53,849 | **0.1%** | 77.1% | 0.2% |
| **2026-06 (current)** | 45,366 | **0.1%** | 78.2% | 0.1% |

Finish positions held ~75–80% through Feb 2026, then collapsed to **~0% by May, and sit at 0.1% now** — matching the S174 diagnosis. `result_status` stays ~78% because Betfair settlement (WINNER/LOSER) keeps filling it; the *ordinal* (1-2-3-4) from the Racing API is what vanished.

**`subscription_synced_at` coverage** (per race month): 100% through Feb → Mar 32.5% → Apr 18.6% → May 16.0% → **Jun 15.6%**; `has_subscription_sync=1` is ~0.2% by May/Jun.

**One-shot-before-results pattern — confirmed still live (read-only inspection):**
- `racing-metadata-backfill.timer` active, last ran 2026-06-24 14:00 UTC; daily cron `30 11 * * *` runs `sync_day(today)` once.
- `scripts/backfill_race_metadata.py::get_unsynced_dates()` selects only `WHERE subscription_synced_at IS NULL`.
- `subscription/racing_api.py::sync_day()` sets `subscription_synced_at = now_iso` on **first** touch (regardless of whether results had published).
- ⇒ each date is synced once, stamped, and **never re-pulled** — finish positions that publish after that single sync never land. The March inflection coincides with Betfair capture starting to create race rows the once-only subscription path could not keep current.

**Backfillability (diagnostic):** the gap window is 2026-03-01 → 2026-06-25 — ~4 months, **inside** the Racing-API AU window. `sync_day()` upserts existing race rows (idempotent), and `backfill_race_metadata.py` already exposes `--date` / `--days` to force a re-pull past the `IS NULL` filter. So the data **is** re-fetchable in principle. *(Remediation is a separate brief — not actioned here.)*

---

## 5. §5.5 — Capture liveness

| Source | Latest (UTC) | Latest (ACST) | Age @ review | Read |
|---|---|---|---|---|
| Betfair (`betfair_snapshots`) | 2026-06-25T11:18:10Z | 2026-06-25 20:48 | **~2.5 min** | **live** |
| Betfair (`races.betfair_last_snapshot_at`) | 2026-06-25T11:18:10Z | 20:48 | ~2.5 min | live |
| Racing-API subscription (`subscription_synced_at`) | 2026-06-24T14:05:47Z | 2026-06-24 23:35 | ~21 h | nightly one-shot (see §4) |
| Bookmaker/soft-book (`bookmaker_snapshots`) | 2026-06-25T08:34:55Z | 18:04 | ~2.7 h | running; **not used by v1.0 surfaces** |

`/health` `collector_active:true`; `racing-liveness.timer` fired 5 min before review. Betfair scraper live; soft-book scraper current within hours; subscription sync is the once-daily path.

**Timestamp-semantics oddity — RESOLVED.** `snapshot_time` / `betfair_last_snapshot_at` are **capture wall-clock instants in UTC**, *not* market-start times. Proof: Penrith R8 snapshot `11:16:35Z` had `minutes_to_start=-0.6` vs `scheduled_start=11:16:00Z`; Penrith R9 snapshot `11:18:10Z`, `minutes_to_start=28.82`, `scheduled_start=11:47:00Z` (11:47−11:18 = 28.8 ✓). The offset-to-jump lives in the separate `minutes_to_start` column. Max snapshot (`11:18:10Z`) sits ~2.5 min behind VPS wall-clock (`11:20:43Z`) — the draft-time "~90 min ahead" reading **does not reproduce**; freshness should be read directly off `snapshot_time` as capture-time UTC, converted to ACST.

---

## 6. Findings (surprises → findings, not edits)

- **Finding A — `resolve_race` empty-runner edge.** A race matched to a Betfair Win market but never snapshotted (`capture_status=PENDING`, `betfair_last_snapshot_at=NULL`, runners carry no `betfair_selection_id`) passes the loggability check (win_market_id present) and returns a `FreshEnvelope[ResolvedRace]` with **`runners=[]`** rather than `GENUINE_ABSENCE`. Demonstrated: Gatton R5 (2026-06-02), 4 runners, 0 with selection_id. Frequency: **12.5%** of stamped races last 30d (569 / 4,570) resolve to an empty runner list. The picker would show the race selectable but with no runners to pick.
- **Finding B — finish ordinal absent for any recent bet.** Because `finish_position` is ~0% since May, any race logged for a recent date returns `race_results` with `finish_position=None` on every runner; only Betfair WINNER/LOSER is present. Win/lose settlement is fed; the 2nd–4th place/insurance trigger is not.
- **Finding C — multi-code contamination vs hardcoded `THOROUGHBRED`.** capture.db `races` now holds harness ("…Pace/Trot…", e.g. Globe Derby Park, Gloucester Park) and greyhound (Angle Park, Albion Park) meetings — Betfair-side capture is no longer thoroughbred-only. The client hardcodes `RaceCode.THOROUGHBRED` (W1 Finding F2) and `list_meetings` returns these venues labelled thoroughbred. ~14% of stamped races last 30d are `Pace/Trot`-named; ~72% carry no `race_class`/`distance` (non-thoroughbred + unsynced).
- **Finding D — runner enrichment shares the subscription fade.** barrier/weight/jockey ~16–20% and `form_string` ~0.1% on recent races (vs ~70–93% through Feb) — same `subscription_synced_at` root cause as the finish-position gap, hitting `runner_metadata` too.

---

## 7. Self-assessment — what could not be tested, and why

- **No live envelope execution.** capture.db lives on the VPS; `vps_client` opens a local file path. Rather than copy the DB (forbidden) or stage v3 on the VPS (out of scope), I mirrored each method's **exact SQL** read-only against the live file. Verdicts reflect the queries and data, not the Python wrapper's branch logic end-to-end (envelope `fresh`/`stale`/`unavailable` behaviour is inferred from each method's documented heuristic, not run).
- **`bookmaker_snapshots` not assessed for shape** — no v1.0 surface reads it; liveness only.
- **`stewards_status`/`sectional_times`** confirmed structurally absent (W1 F4/F5) — client hardcodes `OFFICIAL`/`None`; not re-litigated.
- **Code-mix sizing is heuristic** (venue + `Pace/Trot` name markers + null enrichment) — capture.db has no explicit thoroughbred/harness/greyhound discriminator column, so the harness/greyhound share is an estimate, not an exact count.
- **Worked examples are time-of-day biased** — review ran 20:50 ACST, so "most recent" races skew to night harness/greyhound; thoroughbred examples were selected explicitly to compensate.
- **Coverage windows are data-relative** (anchored to max `snapshot_time`), not wall-clock, to stay robust to capture lag.

*This report states what is, per read. Remediation, backfill planning, demand-side wiring, and any cutover go/no-go are explicitly out of scope and route to operator-Claude triage next session.*
