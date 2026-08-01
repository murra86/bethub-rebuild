# Race Watcher Phase 1 — build report

**Session:** S245, 20 Jul 2026. **Executor:** background Code session.
**Brief:** `race_watcher_phase1_build_brief.md`. **Design:**
`race_watcher_design_note.md` §1/§2/§7. **Visual:**
`race_watcher_execute_bar_mock.html`.
**Commit:** `7aab1e8` (on `main`, pushed to `murra86/bethub-v3`);
baseline HEAD was `fdd6c0b`.

---

## What landed

A per-runner **"Call"** on the race screen — STRONG / MOD / LEAVE /
faint-dot — that does at jump-time the cross-check the operator now does in
his head. It reads only data already on the row; it changes no money path.

**Part A — grading engine** (`ui/web/src/ev/raceWatcher.ts`, new, pure, no
React):
- `EV_projected` reruns the EXISTING `evEngine`
  (`calculateFieldProbabilities` + `promoEV`) verbatim with each runner's
  `sp_near` substituted for its best-back price, soft price held fixed. No
  new EV maths — the only change is the input prices.
- A **trust gate** collapses pool coherence × market formation
  (overround + share of runners traded) × time-to-jump window × a per-code
  matched-volume floor into ONE weakest-link factor that **CAPS the grade**.
  Below the volume floor / on an unformed book the field **structurally
  cannot emit STRONG**. Trend agreement can flag a conflict and adjust EV
  but **never raises the tier**. Ceiling is STRONG — there is no CERTAIN.
- One global **execute bar** constant (`EXECUTE_BAR_PCT = 5`), never
  rendered on screen. Near the off (`≤ 2 min`) `sp_near` is treated as a
  stale cross-check and the projection reads the live book (research
  amendment 3).

**Part B — the "Call" column** (`OddsTable.tsx` + `OddsTable.module.css`):
one new column inserted after Promo EV, **every other column untouched**
(operator-locked order preserved). STRONG/MOD/LEAVE render as compact pills
using the existing EV-band palette; no-play is a quiet faint dot; reasons
ride on the `title` (hover/tap), never on the row. Scratched rows render
nothing. The same field-level grade map is computed in `Racing.tsx` so the
log snapshot can read the selected runner's Call.

**Part C — grade-at-log stamping** (the one fenced write): two nullable
companion fields, `grade_at_log` (TEXT) and `promo_ev_projected_at_log`
(REAL), stamped alongside the existing `raw_ev_at_log` / `promo_ev_at_log`
snapshot. Threaded through the exact `promo_ev_at_log` plumbing as inert
metadata — frontend snapshot → `LogBetRequest` → `SoftBookLogRequest` →
`SoftBookRecordInputs` → `BetRecord` → store adapter → `BetRow` → SQLite
column + idempotent migration. No money math reads either field. This is
the calibration substrate: every logged bet now records what the watcher
called, to score against the result later.

## Bet-safety / fences honoured

- **Zero money-path logic changed.** Settlement, reconciliation, stake,
  lay, hedge, promo-credit and cash-flow modules were not touched or
  imported by the grader. Part C only adds two inert companion columns that
  mirror `promo_ev_at_log`'s existing pass-through; no surrounding logic was
  altered, no money field added. No stop condition tripped.
- **`evEngine` reused verbatim** for projected EV — no new EV maths.
- **Client-side only** — the grader is arithmetic on data the race page
  already polls; zero extra Betfair/capture calls.

## S189 live-integration status

**Implemented-not-live.** The grade is computed and rendered, and Part C
persists, but nothing has run against a real open race yet. The trust gate
is **corrected-by-logic** — tested against the four 16 Jul fixtures, it
needs a **live look on the first racing day** to confirm the real
`sp_near` / matched-volume / time-to-jump values land the caps where
expected (in particular that pool coherence and the per-code volume floors
are calibrated to real books, not just the reconstructed fixtures).

## Case-study test results

`raceWatcher.test.ts` — the four 16 Jul live case studies (design note §4),
all asserting the trust cap fires and **no false STRONG**:

| Case | Setup | Result |
|---|---|---|
| Pinjarra all-▼ | back-heavy pool Σ(1/sp_near) ≈ 1.07 | pool incoherent → no runner STRONG; reason "pool incoherent" |
| Kilmore all-▲ | lay-heavy pool ≈ 0.88 | pool incoherent → no runner STRONG |
| Albion R10 | 6/10 runners $0 matched, ~1.15 overround | unformed book → trust tier `none`, structural cap, no STRONG; reason "unformed book" |
| Rays Redemption | fresh steam vs drifting stale pool | conflict flagged, tier not raised; reason "trend contradicts close — flagged" |

Plus a **clean-shortening STRONG control** (coherent pool, formed book,
volume over the thoroughbred floor, 8m out, trend agrees, +2.3% now →
≥ bar projected) proving the engine CAN emit STRONG when trust is genuinely
good — the caps are not simply always-off — and a **Coldstream LEAVE trap**
(EV_now ≥ bar but drifts under projected → LEAVE), plus the no-promo and
out-of-window gates. Column render tests (Call header, LEAVE pill with
hover reasons, faint dot, scratched-empty) and Part C round-trip tests
(frontend payload carries/nulls the fields; router forwards them; SQLite
store round-trips them; plain bet defaults to NULL).

## The bands are a FIRST CUT — not tuned

Every threshold in `raceWatcher.ts` (the +5% bar, the pool coherence band
0.97–1.06, the ≤1.08 overround / ≥0.5 traded-share formation gate, the
15-minute window, the per-code volume floors T/H/G = 50k/15k/10k, the
2-minute late window) is a **first cut**. Honing the Calls is the
analytical-line calibration backtest (design note §6, the four open
empirical questions), scored against the `grade_at_log` metadata this build
begins recording. **The Calls are not yet tuned — do not trade them as
gospel; treat the first live day as a look, not a signal.**

## Suites & build

- Backend: **1522 passed** (baseline 1520 at `fdd6c0b`; +2 new).
- Frontend: **240 passed** (baseline 224; +16 new).
- `npm run build` clean (tsc typecheck + vite build); `dist` rebuilt
  (app-down; `dist` is gitignored).

## Commits

- `7aab1e8` — S245: Race Watcher Phase 1 — active-race "Call" grade
  (pushed to `main` / `murra86/bethub-v3`).

## Not in scope (Phase 2+)

Watchlist, banner, background multi-race grading, the pre-assigned/standing
promo model, TAB hands-free grading — all deferred per the brief. Phase 1
grades only the open race on screen against the top-bar armed promo.
