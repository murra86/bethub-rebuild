# Placings backlog-trickle — stop/strike logic fix + meet-ID robustness (Code brief)

**Drafted:** 2026-06-28 (Session 196), Adelaide local (DR-021).
**Anchor file (only edit target):** `scripts/backfill_race_metadata.py` (VPS, already dirty `M`).
**Mode:** READ-WRITE on the anchor; capture.db reads `mode=ro`; writes only through the existing `sync_day()` upsert (not modified). Analytical / capture-side only — no v3, no settlement, no money-path, no auto-settle. Bet-safety clean by construction (DR-033: placings are analytics; live settlement is Betfair-only).

---

## 0. Baseline STOP gate — run first, HALT if mismatched

Confirm before any edit. If any check fails, STOP and report — do not proceed.

| Check | Required |
|---|---|
| Repo / HEAD | `/home/racing/racing-data-capture`, branch `master`, HEAD `5f71488` |
| Anchor working-tree state | `scripts/backfill_race_metadata.py` shows `M` (the S192 + trickle work — build on it, do NOT revert) |
| `run_backlog_pass` present | function at ~L167; `BACKLOG_WALL_THRESHOLD`/`BACKLOG_EXHAUST_AFTER` constants at ~L106–107 |

If HEAD moved or the anchor is clean/absent, the substrate is not what this brief was grounded on — STOP.

---

## 1. What this brief is and is not

- A **surgical fix** to ONE function (`run_backlog_pass`) plus its constants and a small read helper, in ONE file. Single bounded Code session.
- It is **not** a rewrite of `sync_day()` (called, never modified), **not** a schema change, **not** a change to the recent-window pass, **not** a touch to anything outside the named anchors.
- Surprises become **findings in the report**, not chased fixes. Remediation routes to the next operator-Claude triage, not Code's report.

---

## 2. Why this work exists

The nightly backlog-trickle (built per `placings_trickle_report.md`) is **wedged**. Three nightly runs (2026-06-25/26/27) each filled **zero** dates; `remaining_backlog_dates` climbed **95 → 96 → 97** instead of falling.

Grounded diagnosis (Session 196, against live code + live API + capture.db):

- The pass walks oldest-first. Its oldest dates' only remaining gaps are **genuinely-resultless races** — e.g. Naracoorte 2026-03-01 R3–R7, an abandoned / never-resulted meeting. The live Racing API returns those races and runners but **null finishing positions** (only scratched=109). Verified directly: 2026-03-01 is 91% filled (50 of 55 thoroughbred races complete); the 5 stuck races are one meet the API has no results for.
- The pass **mis-reads** these as a quota wall: 3 consecutive zero-runner dates → `break` (L213–218), stopping the night before reaching any recoverable date behind them.
- The strike/retire logic **can never fire** for these front dates: a strike requires `idx < last_fill_idx` (L228), but nothing ever fills before the wall breaks, so `last_fill_idx == -1` forever. The front dates are immortal and gate everything.
- Net: leftover quota never reaches recoverable dates, and the front never clears.

Operator wants: (a) the trickle unjammed so the recoverable historical placings actually come in; (b) a **fill-rate readout** — what % of runners have placings, with the unfilled remainder classified (acceptable if it's just small / abandoned / no-placer races).

---

## 3. Pre-reads

Required: this brief; `placings_trickle_brief.md` (original spec — §5 selector, §5.2 backlog pass, §9 hard rules); `placings_trickle_report.md` (what was built; F1 strike-logic history, F4 resultless-plateau caveat).
Reference-only: `data_sources.md`, `decisions.md` DR-033 (placings analytical, settlement Betfair-only).

## 4. System access

- VPS via SSH (operator ssh-agent unlocked; run from the logged-in Mac session). `-o ClearAllForwardings=yes`.
- READ-WRITE: `scripts/backfill_race_metadata.py` — **named anchors only**.
- capture.db `/home/racing/racing-data-capture/data/capture.db` — reads `mode=ro`; writes only via the unchanged `sync_day()` upsert.
- Racing API GETs via the existing `_api_get` (loads creds from project `.env`).
- **Dirty tree** — NO `git add/commit/stash/restore/checkout/reset`. Read `git status` at start; after each edit `git diff` the anchor; at close confirm the dirty list is unchanged except the anchor. Adelaide timestamps (DR-021).

---

## 5. The fix — §5.1 measure progress by fills, not by `runners_synced`

The root error is treating "0 runners synced" as the progress/stop signal. `runners_synced` counts all runners upserted, is unreliable across transient empty / duplicate-meet responses, and says nothing about whether a *finishing position* was actually written.

Replace it with a **direct fills-gained measure** per date:

- `before` = count of in-scope thoroughbred non-scratched runners on the date with `finish_position IS NOT NULL`.
- run `sync_day(date)` (unchanged), capturing whether it returned an `error`, and `races_synced`.
- `after` = same count re-read.
- `gained = after - before`.

Use a single cheap capture.db COUNT for `before`/`after` (the same predicate `get_backlog_dates` uses: `race_class IS NOT NULL AND is_trial=0 AND is_jump_out=0 AND scratched=0 AND finish_position …`).

## 5.2 Classify each attempt, and act on the class

Per date, in the oldest-first walk:

- **Progress** — `gained > 0`: fill it, log `BACKLOG <date> -> +<gained> placings`, clear any strikes for the date, reset the wall counter, continue.
- **Resultless** — `gained == 0` AND `sync_day` returned cleanly (no `error`) AND `races_synced > 0`: the API answered but had no new placings for this date. **Strike the date on its own merit** (drop the `idx < last_fill_idx` gate entirely). After `BACKLOG_EXHAUST_AFTER` resultless strikes, mark it `exhausted` (retire — drops from the selector). **Do NOT break the walk** — continue past it.
- **Wall / transient** — `sync_day` returned an `error`, OR `races_synced == 0`, OR a detectable rate-limit: treat as a genuine quota/connectivity wall. Do **not** strike (recoverable). Increment a `wall` counter; after `BACKLOG_WALL_THRESHOLD` consecutive wall hits, stop the night.

**Stop the night** when: the selector empties; OR `BACKLOG_WALL_THRESHOLD` consecutive wall hits; OR a new per-night attempt cap `BACKLOG_MAX_ATTEMPTS` is reached (rate-limit ceiling — default 20, tune against observed leftover quota). Resultless dates never count toward the wall and never break the walk — that is the core unjam.

## 5.3 Why this is safe against the meet-ID wrinkle

The operator's question surfaced that the same date can return runners one moment and "0 runners" another, and that meet IDs duplicate / 404 (two Naracoorte meet IDs on 2026-03-01; a 404 on a 03-04 meet). Because retire now requires `BACKLOG_EXHAUST_AFTER` *clean-API-but-no-new-fills* attempts — and an `error`/empty response is classed wall-not-resultless (no strike) — a transient empty or a flaky meet cannot wrongly retire a recoverable date. A date only retires once the API has repeatedly, cleanly confirmed it has no more placings to give.

**Report-only (do NOT chase):** while running, note in the report whether duplicate/unstable meet IDs appear to be blocking *recoverable* results (vs genuinely-abandoned meets). Flag as a finding for operator-Claude; do not rewrite `sync_day`'s meet loop in this brief.

---

## 6. Logging changes

Keep the per-night summary line, with the counters renamed to reflect the new model:
`BACKLOG PASS: attempted=N filled=M placings=P resultless=R walled=W retired=[…] oldest_remaining=<date> remaining_backlog_dates=K`
Keep `BACKLOG COMPLETE` on empty selector. Replace the misleading "quota wall (consecutive zero dates)" wording with a line that distinguishes a real wall (`BACKLOG wall: <N> consecutive fetch errors/empties — stopping`) from retirement (`BACKLOG retired (no results available): <dates>`). `remaining_backlog_dates` stays the closing signal.

## 7. Sequencing within session

1. Baseline STOP gate (§0).
2. Read `git status`; confirm anchor dirty, capture the dirty list.
3. Edit the constants (add `BACKLOG_MAX_ATTEMPTS`; keep `BACKLOG_WALL_THRESHOLD`, `BACKLOG_EXHAUST_AFTER`).
4. Edit `run_backlog_pass` per §5 (fills-gained measure, attempt classification, strike-on-merit, per-night cap, no-break-on-resultless) and the logging per §6.
5. `git diff` the anchor — confirm only the named regions changed.
6. Dry-run the selector + one pass read-only first (no quota burn beyond one real increment is fine), then capture the fill-rate readout (§8).
7. Run the test/lint baseline if one exists for this script; report it.

## 8. Empirical verification + FILL-RATE READOUT (operator requirement)

This is a load-bearing deliverable, not a footnote. Capture and tabulate:

**(a) Overall fill rate — thoroughbred, the trickle's target population.** Non-scratched, non-trial, `race_class IS NOT NULL`, `race_date >= 2026-03-01`. Report, by month and windowed-total:
`filled / total = %` where filled = `finish_position IS NOT NULL`.

**(b) Classify the UNFILLED remainder** (this answers "is the gap just small/abandoned races?"). Per race, bucket: `fully_unresulted` (0 runners resulted — abandoned / no-placer), `partial` (some resulted, some not — individual non-finishers), `fully_resulted`. Report counts of races and runners per bucket across the window. The acceptable residue is `fully_unresulted` + the stragglers in `partial`.

**(c) By-code note.** State plainly what the thoroughbred number excludes — greyhound/harness rows (no `race_class`) are not in the Racing-API placings population; say what their coverage looks like so the operator isn't misled by a blended figure.

**(d) Carve-out.** The trickle's full multi-night effect cannot be proven in one session (per the S36 in/out-of-session precedent). Report the **current baseline** fill rate + remainder classification (the starting picture); the post-fix climb is read from `metadata_backfill.log` + capture.db over the following nights (operator-Claude daily check-up). Prove the **mechanism** in-session (selector unjams; a resultless front date strikes without breaking the walk; the walk reaches a date behind it).

---

## 9. Output spec

Single file: `placings_trickle_fix_report.md` (rebuild root, same place as the prior trickle artefacts). Adelaide timestamps. Sections:

1. Run header (HEAD, dirty-anchor confirmation, capture.db path/size, VPS wall-clock).
2. §0 baseline gate result.
3. The edit — `git diff --stat` of the anchor; the named regions changed.
4. Mechanism proof — selector unjams; resultless front date strikes without breaking the walk; the walk reaches a date behind it; one real increment if quota allowed.
5. **Fill-rate readout** (§8 a–c) — the tables. This is the section the operator reads first.
6. Findings (incl. the report-only meet-ID observation §5.3).
7. Self-assessment — what could not be tested in-session and why (the multi-night carve-out).

Rough length 120–200 lines. The report does **not** contain: recommendations, a next-brief, any change outside the anchor, or a verdict on whether to cancel the Racing API subscription.

## 10. Hard limits — what is NOT in scope

- No rewrite of `sync_day()` or `_sync_single_race`/`_sync_single_runner` — called, not modified.
- No change to the recent-window pass or `get_unsynced_dates` (the S192 fix stays intact).
- No schema change; the strike state stays in the existing gitignored JSON sidecar.
- No chasing the meet-ID/duplicate issue — observe and flag only (§5.3).
- No v3 / settlement / money-path / auto-settle contact. No Betfair path, no scraper path, no harness/greyhound mapping.
- No git history operations (dirty tree). Edits confined to the named anchors.
- `--delay` floored at `BACKLOG_MIN_DELAY` (1.5s), single-threaded — no rate-limit relaxation.
- Recent-first stays structural — the backlog pass remains reachable only after the recent loop, argless path only.

## 11. What happens after + cross-references

After Code's session, the next operator-Claude session **auto-triages** `placings_trickle_fix_report.md` (no confirmation gate): confirm the mechanism unjammed, read the fill-rate baseline, confirm the remainder is the acceptable small/abandoned-race residue. Then the operator-Claude **daily** check-up reads `metadata_backfill.log` + the fill-rate query against capture.db until the rate plateaus (the real "it's working" signal). Code does not write the next brief.

Cross-references: `placings_trickle_brief.md` / `placings_trickle_report.md` (the build this fixes); DR-033 (placings analytical, settlement Betfair-only); DR-027/028 (capture-side boundary); the S192 forward-fix (recent-window bounding — left intact); parking-lot: the duplicate/unstable meet-ID question (flagged here, not chased).
