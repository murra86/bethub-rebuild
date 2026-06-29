# Placings backlog-trickle — stop/strike logic fix + meet-ID robustness (Code report)

**Executed:** 2026-06-28, ~21:17 → ~21:43 ACST (single bounded Code session, per `placings_trickle_fix_brief.md`).
**Mode:** READ-WRITE on the one anchor; capture.db reads `mode=ro`; writes only through the unchanged `sync_day()` upsert. Analytical / capture-side only — no v3, no settlement, no money-path, no auto-settle, no Betfair/scraper path. Bet-safety clean by construction (DR-033).
**Outcome:** the trickle stop/strike logic is rewritten exactly per §5 — progress is now measured by *finishing positions gained*, resultless dates strike on their own merit without breaking the walk, transient errors/empties are a separate (non-striking) wall, and a per-night attempt cap is added. Mechanism fully proven (9/9 deterministic + one live pass). **A load-bearing surprise surfaced and is reported, not chased (§6, F1): the live API holds the recoverable placings, but `sync_day()` is not landing them — a downstream write/identity-matching blocker that is separate from, and now exposed by, the unjammed trickle.**

---

## 1. Run header

| Item | Value |
|---|---|
| SSH gate | **PASS** — `ssh racing-vps`, `-o ClearAllForwardings=yes`, via operator ssh-agent. |
| Repo / HEAD | `/home/racing/racing-data-capture`, branch `master`, HEAD **`5f71488`** (unchanged at close). |
| Anchor (only file edited) | `scripts/backfill_race_metadata.py`. `subscription/racing_api.py` / `sync_day()` / `storage/database.py` **read only, not modified**. |
| capture.db | `/home/racing/racing-data-capture/data/capture.db` — **4,091,674,624 B (~4.09 GB)**, live WAL; reads `mode=ro`; writes via `sync_day()` upsert only. |
| State sidecar | `data/backlog_trickle_state.json` (gitignored `data/`; not in the dirty list). After the live pass: **20 dates @ strike 1, 0 exhausted**. |
| VPS wall-clock | session ~`2026-06-28T11:47Z`–`12:13Z` (21:17–21:43 ACST). Nightly timer `racing-metadata-backfill.timer` next fires `2026-06-28T14:00Z` (23:30 ACST) and runs this working-tree code. |
| Timestamps | capture.db stores UTC; report times ACST (UTC+9:30, no June DST) per DR-021. |

---

## 2. §0 baseline gate — PASS (hard STOP if not)

| Check | Required | Found | |
|---|---|---|---|
| Repo / HEAD | `master`, `5f71488` | `master`, `5f71488` | ✅ |
| Anchor working-tree state | `scripts/backfill_race_metadata.py` = `M` (S192 + trickle — build on it) | `M`, trickle code present | ✅ |
| `run_backlog_pass` present | function ~L167; `BACKLOG_WALL_THRESHOLD`/`BACKLOG_EXHAUST_AFTER` ~L106–107 | `def` at L167; constants at L106–107 | ✅ |

Substrate is exactly what the brief was grounded on. Proceeded.

**Working-tree gate.** Dirty list at start = 14×`M` + 8×`??` (incl. the anchor as `M`). **Close-out `git status --porcelain` is byte-for-byte identical** — anchor still `M`, no new tracked files (sidecar gitignored), no git state mutated (no `add/commit/stash/restore/checkout/reset`).

---

## 3. The edit — `git diff --stat` and the named regions

```
 scripts/backfill_race_metadata.py | 267 +++++++++++++++++++++++++++++++++++++-
 1 file changed, 262 insertions(+), 5 deletions(-)   # cumulative vs HEAD 5f71488
```

Three named regions changed, nothing else (verified by full `diff` — no change at or after `def main()`):

1. **Constants (L106–108).** Kept `BACKLOG_WALL_THRESHOLD=3` and `BACKLOG_EXHAUST_AFTER=5` (re-commented to the new model); **added `BACKLOG_MAX_ATTEMPTS=20`** (per-night attempt ceiling); kept `BACKLOG_MIN_DELAY=1.5`.
2. **New read helper `_count_filled(conn, date_str)`** — a single cheap `mode=ro` COUNT of in-scope thoroughbred non-scratched runners with `finish_position IS NOT NULL`, mirroring the `get_backlog_dates` predicate. The direct "fills gained" measure.
3. **`run_backlog_pass()` rewritten** per §5: fills-gained measure (before/after `_count_filled`), three-way attempt classification, strike-on-merit (the `idx < last_fill_idx` gate is gone), per-night cap, no-break-on-resultless, and the §6 logging.

`sync_day()`, `_sync_single_race`, `_sync_single_runner`, `upsert_runner`, `get_unsynced_dates`, the recent-window pass, the `main()` wiring, and the schema are **untouched**. The state sidecar mechanism is unchanged (no schema change).

**Logging (§6).** Summary line is now
`BACKLOG PASS: attempted=N filled=M placings=P resultless=R walled=W retired=[…] oldest_remaining=<date> remaining_backlog_dates=K`.
Per-date: `BACKLOG <d> -> +<g> placings` / `… 0 new placings (resultless, strike n/5)` / `… wall (<reason>)`. The misleading "quota wall (consecutive zero dates)" wording is replaced by `BACKLOG wall: <N> consecutive fetch errors/empties — stopping` and `BACKLOG retired (no results available): <dates>`. `BACKLOG COMPLETE` on empty selector retained.

---

## 4. Mechanism proof

**(a) Deterministic unit proof — 9/9 PASS** (monkeypatched `sync_day`/`_count_filled`/sidecar; no DB/API/quota; logging redirected off the real log):

| Scenario | Result |
|---|---|
| A — resultless front strikes **without breaking**; walk reaches a date behind it | all 3 attempted; the behind-date filled (+20); both front dates struck; `walled=0` ✅ |
| B — retire after `BACKLOG_EXHAUST_AFTER` clean-but-no-fill strikes | 5th strike sets `exhausted`, date in `retired` ✅ |
| C — wall (error/HTTP-429) stops the night, strikes **nobody** | stops at `WALL_THRESHOLD`; sidecar untouched ✅ |
| D — clean response but `races_synced==0` is a wall (no strike) | classed wall, `resultless=0`, sidecar untouched ✅ |
| E — resultless **never breaks** the walk | runs to the attempt cap (20), not stopping at 3 ✅ |

**(b) One live pass (real API + capture.db, sanctioned `sync_day()` write path), 21:17:52–21:18:59 ACST:**
`BACKLOG PASS: attempted=20 filled=0 placings=0 resultless=20 walled=0 retired=[] oldest_remaining=2026-03-01 remaining_backlog_dates=98`.
The walk **attempted all 20 oldest dates without breaking** (the old code would have `break`ed at 3 consecutive zeros and struck nobody). Every date classified **resultless** (clean API, `races_synced>0`, `gained==0`), each struck once, `walled=0` (no quota wall). **The unjam mechanism is proven live: the selector no longer wedges on a resultless front.**

> The live pass also exposed F1 (below): `filled=0` is **not** because the dates are genuinely resultless — the API has the results; they are not landing.

---

## 5. Fill-rate readout (operator requirement — read this first)

Population = the trickle's target: thoroughbred (`race_class IS NOT NULL`), `is_trial=0`, `is_jump_out=0`, `scratched=0`, `race_date >= 2026-03-01`. `filled = finish_position IS NOT NULL`. Read-only against capture.db at session close (after the live pass).

**(a) Overall fill rate — by month + windowed total**

| Month | filled / total | % |
|---|---|---|
| 2026-03 | 7,831 / 14,404 | **54.4%** |
| 2026-04 | 1,077 / 15,469 | 7.0% |
| 2026-05 | 0 / 14,836 | 0.0% |
| 2026-06 | 2,838 / 13,894 | 20.4% |
| **Window total (≥ 2026-03-01)** | **11,746 / 58,603** | **20.0%** |

**(b) Classification of the unfilled remainder** (per in-scope race)

| Bucket | races | runners | unfilled runners |
|---|---|---|---|
| `fully_resulted` (all runners resulted) | 1,277 | 11,625 | 0 |
| `partial` (some resulted, some not) | 16 | 154 | 33 |
| `fully_unresulted` (0 runners resulted) | 4,977 | 46,824 | 46,824 |

Naïvely the "acceptable residue" is `fully_unresulted` + the 33 `partial` stragglers. **That framing is wrong here (see F1):** the bulk of the 4,977 `fully_unresulted` races are **recoverable, not abandoned** — the API holds their results; they are blocked from landing. The genuinely-resultless residue is small (e.g. the abandoned Naracoorte meet, 2026-03-01 R3–R7 = 39 runners). Until F1 is fixed, `fully_unresulted` is dominated by recoverable-but-blocked, not by true residue.

**(c) By-code note.** The figures above are **thoroughbred-only** and exclude greyhound/harness rows (`race_class IS NULL`), which are not in the Racing-API placings population. Their coverage is **12 / 123,932 = 0.0%** finish_position — effectively none, as expected. A *blended* figure would read ~11,758 / 182,535 ≈ **6.4%** and badly mislead the operator; the 20.0% thoroughbred number is the meaningful one.

---

## 6. Findings (surprises → findings; report-only, not chased)

- **F1 — LOAD-BEARING: recoverable placings exist in the API but `sync_day()` is not persisting them (a write/identity-matching blocker separate from the trickle).** Probed live, read-only, for 2026-03-15: the Racing API returns **589 runners with real finishing positions** across the meets; capture.db holds **263** in-scope filled; yet the live pass wrote **0 new placings** and advanced `subscription_synced_at` to 11:48 on every race. Drill-down on Dubbo: the API meet `met_aus_626943265490` (course "Dubbo") R-payload carries positioned runners (e.g. number 1 "I'm A Beaut", `position='1'`), but DB "Dubbo R1" (`race_id=179226`, that same `subscription_meet_id`, synced 11:48) contains **entirely different runners** (Karinya Haz, Oursurfinsafari …, keys `N:2…N:10`, no `N:1`, all `finish_position` NULL). So the re-sync touches the race row's metadata but the finishing-position-bearing runners from the API payload never reconcile onto it. `upsert_runner` itself is correct (`ON CONFLICT(race_id, runner_key) DO UPDATE … COALESCE`), so the failure is upstream of it — a race/runner **identity mismatch** between the API meet payload and the DB race row. **Consequence:** the operator's goal (recoverable historical placings actually coming in) will **not** be met by this trickle fix alone; the data is recoverable but blocked. **Out of scope here** (no `sync_day`/`_sync_single_*` rewrite, §10) — routes to operator-Claude triage.

- **F2 — the §5.3 "clean-API-but-no-fills ⇒ genuinely resultless" assumption is empirically violated by F1, so strike-on-merit will retire *recoverable* dates.** The fix was built exactly to spec (strike a clean, races-answered, zero-gain attempt on its own merit). But because F1 makes recoverable dates *look* resultless (clean API, races answered, zero fills land), those dates now accrue strikes. The live pass left **20 dates at strike 1/5**; at the current cadence they would be **retired after ~4 more nights** and dropped from the selector — wrongly, since they are recoverable. This is a direct, time-sensitive consequence of F1, not a defect in the implemented logic. **Operator decision required:** fix the F1 write-path blocker before the strikes mature, or the trickle will quietly retire recoverable history. (I did not alter the strike logic or clear the sidecar — remediation routes to operator-Claude, per §1/§10.)

- **F3 — duplicate / unstable meet IDs are present (the §5.3 wrinkle), but are not the whole story.** On 2026-03-15 the API returned **10 meet_ids for 8 venues** — `bet365 Swan Hill` ×2 (one with 82 positions, one with 7 runners / 0 positions) and `Grafton` ×2. This duplication is real and is a plausible contributor to the F1 identity mismatch (a venue's runners split across two meet_ids; the "empty" duplicate can shadow the populated one). However, F1 reproduces even on single-meet venues, so the blocker is broader than meet-ID duplication alone. Flagged for operator-Claude; **not chased** (no rewrite of `sync_day`'s meet loop, §5.3/§10).

- **F4 — per-runner exceptions are swallowed at `logger.debug` in `_sync_single_race`.** Any matching/constraint failure during runner upsert is invisible at the INFO log level the nightly runs at — exactly the kind of silent failure that would hide F1 from the existing `metadata_backfill.log`. Observation only.

- **F5 — the thoroughbred-only readout corrects the prior blended picture.** The earlier trickle report's March figure (21.3%) was a blended all-runner number dragged down by greyhound/harness rows; the thoroughbred-only March figure is **54.4%**. The corrected denominator (F-c) is what the operator should track going forward.

---

## 7. Self-assessment — what could not be tested in-session, and why

- **Multi-night closure / live trickle rate — not provable in-session** (S36 carve-out, §8d). I proved the *mechanism* (the selector unjams; a resultless front strikes without breaking; the walk reaches dates behind it; the per-night cap bounds it) plus one real live pass. The multi-night climb is read by operator-Claude from `metadata_backfill.log` + the §5 fill-rate query over the following nights — **but see F1/F2: that climb will not happen, and recoverable dates will start retiring, until the `sync_day` write-path blocker is fixed.** The "starting picture" baseline is §5.
- **F1 root cause not isolated to a single line** — I confirmed the *effect* decisively (API has results; nothing lands; race row touched; runners mismatched) and the most likely locus (race/runner identity matching upstream of the correct `upsert_runner`), but did **not** chase it further: the brief forbids rewriting `sync_day`/`_sync_single_*` and scopes this session to the trickle anchor. Exact remediation is operator-Claude's.
- **Sidecar left as-is** — the live pass's 20 strike-1 entries are honest output of the real run; I did not clear them (remediation routes out, §1/§10). They are the time-sensitive signal in F2.
- **Scope held:** capture-side / analytical only; no v3 / settlement / money-path / auto-settle / Betfair / scraper / harness-greyhound contact; `sync_day()` and the schema untouched; recent window never starved (backlog pass remains argless-only, after the recent loop); `--delay ≥ 1.5`, single-threaded; manual `--date`/`--days` untouched and still bypassing; no git state mutated; dirty list unchanged except the (already-`M`) anchor; one file edited, three named regions only.
