# Placings backlog-trickle — nightly results-sync standing change (Code report)

**Executed:** 2026-06-25, ~22:43 → ~22:58 ACST (single bounded out-of-session Code run, per `placings_trickle_brief.md`).
**Mode:** READ-WRITE, capture-side / analytical only. One repo source anchor extended; recovery writes through the existing `sync_day()` upsert; reads `mode=ro`. No v3 / settlement / live-betting / money-path / auto-settle contact. No capture.db schema change, hand-edit, or copy.
**Outcome:** the backlog-trickle pass is wired into the nightly path — recent-first (structural), bounded, idempotent, self-healing, self-stopping. Mechanism fully verified in-session (incl. a strike-logic bug caught and fixed mid-session). One in-session increment ran and filled the oldest backlog date before hitting today's quota wall, as expected.

---

## 1. Run header

| Item | Value |
|---|---|
| SSH Step-0 gate | **PASS** — `ssh racing-vps 'echo ok'` via operator ssh-agent, `-o ClearAllForwardings=yes`. |
| Repo / HEAD | `/home/racing/racing-data-capture`, branch `master`, HEAD **`5f71488`**. |
| Anchor (only file edited) | `scripts/backfill_race_metadata.py`. `subscription/racing_api.py` / `sync_day()` **not touched** (called, not rewritten). |
| capture.db | `/home/racing/racing-data-capture/data/capture.db` (~3.97 GB, live WAL); reads `mode=ro`; writes via `sync_day()` upsert only. |
| State sidecar | `data/backlog_trickle_state.json` (gitignored `data/` — never in the dirty list; no schema change). |
| VPS wall-clock | session start `2026-06-25T13:13:25Z` (22:43 ACST); nightly timer fires 23:30 ACST. |
| Timestamps | capture.db stores UTC; report times ACST (UTC+9:30, no June DST) per DR-021. |

---

## 2. §5.0 baseline gate — PASS (hard STOP if not)

| Check | Required | Found | |
|---|---|---|---|
| HEAD | `5f71488` | `5f71488` | ✅ |
| `get_unsynced_dates` form | post-S192 bounded recent-first (`date(race_date) >= date('now', ?)`, `ORDER BY race_date DESC`, `trailing_days=14`) | exactly that | ✅ |
| anchor working-tree state | `M` (S192 forward fix — build on it, don't revert) | `M`, S192 fix present | ✅ |

Substrate is the post-S192 form. Proceeded. The S192 forward fix was left intact and is the base the backlog pass extends.

## 3. Working-tree gate

Dirty list at start matches `placings_backfill_report.md` §2 (the March rework: 14×`M` + 8×`??`) **plus** `scripts/backfill_race_metadata.py` as `M` (the S192 fix). No anchor collision with unrelated work. **Close-out `git status` is identical to start except the anchor** — no new tracked files (sidecar is gitignored), no git state mutated (`no add/commit/stash/restore/checkout/reset`).

---

## 4. The backlog selector (§5.1)

**Chosen predicate (surfaced as a finding):** a date is *backlog-incomplete* when, within `[2026-03-01, today − 14d)`, it has a **thoroughbred** race carrying a non-scratched runner with `finish_position IS NULL`. Thoroughbred is proxied by **`race_class IS NOT NULL`** — only the Racing API sets `race_class`, so Betfair-matched greyhound/harness rows are excluded **without** keying on the permanently-unbounded `subscription_synced_at IS NULL` set (F2). Bounded below by the gap floor `2026-03-01`; bounded above by the recent window (the S192 recent pass owns those dates — no overlap; a date *ages into* the backlog as the window slides, a self-healing handoff). Oldest-first (`ORDER BY race_date ASC`). Exhausted dates (sidecar) excluded.

**What it returns (verified read-only before wiring):**
- **95 dates, oldest-first**, `2026-03-01 … 2026-06-10` (boundary `< 2026-06-11`, floor `2026-03-01`). 102 gap dates in-window → 95 still incomplete.
- Samples on the oldest date are unmistakably thoroughbred (BM66 / BM58 / 0-56 handicaps); **0 `race_class`-bearing races match harness names** (`Pace/Trot`) — no greyhound/harness contamination.
- `2026-06-20` (recovered in S192) is **correctly absent** — its thoroughbred finishing positions are filled, so the date self-drops. Date-level self-stop confirmed.

---

## 5. The backlog pass (§5.2) — the edit

Three additions to the anchor (`git diff --stat`: `scripts/backfill_race_metadata.py | +198 / −5`):
1. `import json`.
2. **`get_backlog_dates()`** (the §4 selector) + **`run_backlog_pass()`** + sidecar helpers + constants (`BACKLOG_FLOOR="2026-03-01"`, `WALL_THRESHOLD=3`, `EXHAUST_AFTER=5`, `MIN_DELAY=1.5`).
3. **`main()` wiring** — argless nightly path only, after the recent loop:

```diff
     logger.info("Backfill complete: %d races, %d runners across %d dates", ...)
+    # Nightly (argless) path only: after the recent window above, trickle the
+    # historical backlog off whatever Racing-API quota is left. Recent-first is
+    # structural — this runs strictly after the recent pass. Manual --date /
+    # --days recovery bypasses it (left working and unchanged).
+    if not args.date and not args.days:
+        run_backlog_pass(conn, max(args.delay, BACKLOG_MIN_DELAY))
     conn.close()
```

**Behaviour (all per §5.2):**
- **Recent-first is structural** — the pass is *only* reachable after the recent loop, and only in the argless path. `--date` / `--days` never trigger it (manual recovery untouched, still bypassing).
- **Leftover-only, stop-on-wall** — walks the selector oldest-first, fills each date via the idempotent `sync_day()` upsert (commits per-date, lines 293/409 — no long write-lock against the live collector); stops the night after **3 consecutive zero-runner dates** (the S192 quota-wall signal).
- **Idempotent** — `sync_day()` upsert; no duplicate rows (proven S192).
- **Self-healing** — a quota-blocked date is simply still in the selector tomorrow; no manual nudge.
- **Don't-retry-resultless-forever** — a zero-date earns a *strike* **only if a later date in the same pass filled** (`idx < last_fill_idx`, i.e. quota was provably available when it was tried); after **5** such strikes it is classified "no results available" and dropped (logged). Persistence is a minimal **gitignored JSON sidecar** (no existing-table schema change, per §9).
- **Self-stopping** — empty selector ⇒ clean no-op + `BACKLOG COMPLETE`; `--delay` floored at 1.5s, single-threaded (no rate-limit relaxation).

## 6. Per-night logging (§5.3)

Appends to the existing `metadata_backfill.log` (and stdout):
`BACKLOG PASS: attempted=N filled=M runners=R oldest_remaining=YYYY-MM-DD remaining_backlog_dates=K`, plus per-date `BACKLOG <date> -> R runners`, a `BACKLOG quota wall …` line on stop, `BACKLOG dropped (no results available): …` on exhaustion, and `BACKLOG COMPLETE` when the backlog empties. This is the operator's read on the leftover-quota rate and the closing signal (`remaining_backlog_dates → 0`).

---

## 7. Pre / post coverage

`finish_position` coverage by month (in-session writes were one quota-limited increment — bulk recovery is the multi-night job by design, §2 "speed is not the priority"):

| Month | Runners | finish_pos % PRE (S192 end) | finish_pos % POST |
|---|---|---|---|
| 2026-03 | 67,379 | 21.2% | **21.3%** |
| 2026-04 | 56,964 | 6.4% | 6.4% |
| 2026-05 | 53,849 | 0.1% | 0.1% |
| 2026-06 | 45,372 | 3.4% | 3.4% |

The only movement is March, from the in-session increment filling the oldest backlog date: **`2026-03-01` now 470/680 runners with `finish_position`**. The trickle closes the rest over nights.

---

## 8. Mechanism verification (+ carve-out)

- **Order is recent → backlog.** The backlog call sits after the recent loop, gated to the argless path (§5 diff) — structural, not a runtime preference.
- **Selectors:** recent window returns **15** dates (newest-first, `2026-06-25 … 2026-06-11`); backlog returns **95** (oldest-first, `2026-03-01 … 2026-06-10`). No overlap.
- **Self-stop path (empty selector):** demonstrated — `BACKLOG PASS: attempted=0 … remaining_backlog_dates=0` then `BACKLOG COMPLETE`, no writes.
- **One real increment:** oldest-first walk `2026-03-01 → 03-02 → 03-04 → 03-05`; **`2026-03-01` filled 82 runners**, then 3 consecutive zeros → `BACKLOG quota wall … stopping for tonight`; final line `attempted=4 filled=1 runners=82 oldest_remaining=2026-03-01 remaining_backlog_dates=95`. Stops cleanly on leftover quota — exactly the intended leftover-only behaviour.
- **Strike logic (deterministic unit proof, no quota):** scripted `sync_day` (fill, 0, fill, 0, 0) → **PASS** on all three: (a) only the zero *before* the last fill is struck; the trailing wall zeros are not; (b) 5 strikes ⇒ `exhausted`/dropped; (c) a pure-wall night (no fills) strikes nobody.
- **Carve-out (out-of-session, S36 precedent):** the true multi-night leftover-quota rate and full gap closure can only be proven by the nightly runs (and a quota reset). In-session I proved the **mechanism** + **one increment**; the live rate is read from `metadata_backfill.log` over the following nights (`remaining_backlog_dates` trending to 0).

---

## 9. Findings (surprises → findings)

- **F1 — strike-logic bug caught and fixed mid-session.** My first implementation struck *any* zero-date on a night where `filled > 0`. The real increment exposed it: `2026-03-01` filled then the quota wall zeroed `03-02/04/05`, which were wrongly struck — those zeros were the wall, not resultlessness. A date perpetually behind the wall would have accrued strikes and been wrongly dropped. Corrected to strike **only** zeros with a *later* fill in the same pass (`idx < last_fill_idx`); the wrongly-written sidecar was cleared; unit-proven (§8).
- **F2 — predicate choice = `race_class IS NOT NULL` thoroughbred proxy** (not `subscription_synced_at IS NULL`, per the brief's F2 prohibition). Trade-off: the backlog only covers dates with at-least-once-synced thoroughbred races; a thoroughbred race that was *never* synced (no `race_class`) is not picked up. Acceptable — the gap dates were all synced once (race_class set on the pre-results touch), so this covers the actual Mar–Jun collapse.
- **F3 — persistence = a gitignored JSON sidecar** (`data/backlog_trickle_state.json`), per §5.2's explicit permission. No existing operational/capture table was altered. Absent from `git status` (gitignored), so the dirty-list close-out stays clean.
- **F4 — a small, bounded residual is expected, by design.** Partially-fillable dates (e.g. `2026-03-01` at 470/680 — the rest greyhound/harness/scratched/genuinely-absent) and thoroughbred *trials* (`*-TRL`, which the API may never result) stay in the selector. The conservative strike rule (only strike on a proven-quota-available zero) means such dates are **never wrongly dropped**; the cost is that a *trailing cluster of purely-resultless dates that never co-occurs with a fill* (so `filled` stays 0 in their pass) is retried nightly rather than struck — a tiny bounded quota waste, visible to the operator as a non-zero `remaining_backlog_dates` plateau in the log.
- **F5 — today's quota is near-exhausted** (consistent with S192 F3): the increment filled only `2026-03-01` before the wall. The 95-date backlog will trickle closed over nights off leftover quota.

---

## 10. Self-assessment — what could not be tested, and why

- **Multi-night closure / live rate not proven in-session** — requires the nightly runs and quota resets (carve-out, §8). The first live run is tonight's 23:30 ACST timer, which executes this code from the working tree.
- **In-session increment was quota-limited to 1 filled date** — expected (F5), not a fix shortfall; the mechanism (oldest-first, wall-stop, log line, sidecar) was fully exercised regardless.
- **The "genuine-resultless ⇒ strike" path was proven by a scripted unit test, not live** — manufacturing the live fill-then-genuine-zero pattern needs available quota I didn't have; the unit test is deterministic and covers the three cases exactly.
- **Predicate may miss never-synced thoroughbred races** (F2) — rare for the gap window; out of scope to chase here.
- **Scope held:** capture-side / analytical only; no v3 / settlement / money-path / auto-settle; `sync_day()` called not rewritten; no schema change (sidecar is a gitignored file); recent window never starved (structural); `--delay ≥ 1.5`, single-threaded; manual `--date`/`--days` untouched and still bypassing; no git state mutation; dirty list unchanged except the anchor; scrapers / Betfair path / harness-greyhound mapping untouched.

*Routing (per §10 of the brief) is the next operator-Claude session's job: confirm the mechanism and the first nightly increment, then let the trickle run and spot-check the log rate. This report states what is and proposes no remediation or next brief.*
