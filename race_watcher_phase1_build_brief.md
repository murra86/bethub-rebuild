# Build brief — Race Watcher Phase 1 (active-race grade)

**Session:** S245, 20 Jul 2026. **Author:** Chat (grounded on the live
code + the operator walkthrough). **Executor:** a background Code
session. **Design source of truth:** `race_watcher_design_note.md`
(esp. §1 engine, §2 grading, §7 locked walkthrough outcomes) +
`race_watcher_research_report.md` (the v2 amendments). **Approved visual:**
`race_watcher_execute_bar_mock.html` (the row-level take — one new
"Call" column).

Read this whole brief + the design note §1/§2/§7 and confirm
understanding **before editing any file**. Ask about anything ambiguous.

## 0. What this is

Add a per-runner **"Call"** to the race screen — STRONG / MOD / LEAVE /
faint-dot — that synthesises signals already on the row (Promo EV,
BF Close/`sp_near`, Trend, market trust) into one verdict on whether to
take the bet, judged at **jump time**, not just now. It does the
cross-check the operator now does in his head. **Display-only** on the
row, plus **one small metadata write** (grade-at-log, Part C) so we can
calibrate the Calls against real results later.

**Scope = Phase 1 only.** OUT: the watchlist, the banner, background
multi-race grading, the pre-assigned/standing promo model, TAB
hands-free grading (all Phase 2+). Phase 1 grades **only the open race
on screen**, against **the promo armed in the top promo bar**.

## 1. Fences (non-negotiable)

- **Bet-safety.** Do not touch or import any money calculation,
  settlement, reconciliation, stake, lay, hedge, promo-credit or
  cash-flow logic. The grade is decoration computed from data already
  fetched. The ONLY write (Part C) persists two metadata fields
  (`grade_at_log`, `promo_ev_projected_at_log`) **alongside the existing
  `raw_ev_at_log` / `promo_ev_at_log` snapshot** — no money math, no new
  money field, no change to stake/EV computation. If anything else in a
  money module would need to change, STOP and report.
- **Reuse `evEngine` verbatim.** EV_projected must call the SAME
  `calculateFieldProbabilities` (evEngine.ts:221) + `promoEV`
  (evEngine.ts:469) — no new EV maths. The only substitution is the
  input prices (§2).
- **Client-side.** Phase 1 grading is arithmetic on data the race page
  already polls — zero extra Betfair/capture calls.
- **`bethub-v3` git autonomy:** commit + push a GREEN tree only, co-author
  trailer. Frontend gate is `npm run build` (vitest does not typecheck);
  rebuild dist app-down (S232).

## 2. Part A — the grading engine (new client-side module)

New module `ui/web/src/ev/raceWatcher.ts` (+ test). Pure functions, no
React. Per active runner, given data already in the OddsTable render
loop (`promo` EV-now, `back`, `lay`, `sp_near`, `matched`, field
`confidence`, `trend`, overround, minutes-to-jump from
`catalogue.market_start_time`), produce
`{ grade, evNow, evProjected, reasons }`.

**EV_projected** = rerun the promo EV with the *projected close*
substituted for current Betfair prices, **soft price held fixed**:
1. Build a "projected field": each runner's `sp_near` in place of its
   `best_back` price.
2. `calculateFieldProbabilities(projectedField)` → `promoEV(...)` with
   the operator's typed soft odds and the armed promo config unchanged.
   (The operator's position locks the soft price; the moving part is
   market truth at jump.)

**Trust gate (design note §1 + research amendments — this CAPS the
grade; EV maths alone never sets it):**
- **Pool coherence:** Σ(1/`sp_near`) across active runners near 100% →
  trust; far off → distrust (the Pinjarra ≈107% all-▼ / Kilmore ≈88%
  all-▲ artifacts are the reference failures).
- **Market formation:** overround band (~≤106%), spread tightness, share
  of runners carrying matched volume (an unformed book — e.g. Albion R10,
  6/10 runners $0 matched, 115% overround — means `sp_near` merely
  echoes the back price → no independent info → cannot support STRONG).
- **Time-to-jump ramp:** projection weight rises inside ~15 min.
- **Collapse the above into ONE liquidity/trust factor** before grading
  (research amendment 1: correlated-signal overconfidence). Below a
  per-code matched-volume floor, the market **structurally cannot emit
  STRONG**, whatever the EV says — hard cap.
- **Trend agreement:** price-memory trend (matched money) agreeing with
  the close direction → confidence boost; contradiction → **prefer the
  trend and flag the conflict** (Rays Redemption: fresh steam vs stale
  pool). **Movement signals may adjust projected EV but NEVER raise the
  tier** (research amendment 4).
- **`sp_near` is ~60s-cached** → near the off use the live best-back as
  the BSP estimator and demote `sp_near` to a cross-check + staleness
  flag (research amendment 3).

**Grade mapping (design note §2 table — first cut, thresholds as named
operator-tunable constants):**
- **STRONG** — EV_projected comfortably ≥ bar at good trust (the
  +2.3%→+8.5% shortening case), OR EV_now ≥ bar and holding/firming.
- **MOD** — EV_projected ≥ bar at LOW trust (thin/early/conflicted), OR
  EV_now marginal + firming.
- **LEAVE** — a *tempting* runner that fails: EV_now looks ≥ bar but
  EV_projected drops under it (drifting), i.e. the Coldstream trap.
- **(faint dot)** — everything else: drifting/below-bar/no soft typed/no
  play. Not a pill, just a quiet marker.
- **Execute bar = ONE global tunable constant** (default +5%). Not
  per-promo. Never rendered on screen.
- **Ceiling is STRONG — no CERTAIN tier** (research amendment 2).

**Reasons string** (shown on hover/tap, Part B), compact, e.g.:
`+2.3% now → ~+8.5% @ 2.70 proj · pool coherent · trend agrees · 8m`.
On a trust cap or conflict, say so: `… · thin book — capped at MOD`,
`… · trend contradicts close — flagged`.

## 3. Part B — the "Call" column (OddsTable.tsx)

- Add ONE column **"Call"** to the existing table — **move nothing
  else** (column order is operator-locked; the operator's explicit
  requirement is that the current screen is untouched but for this one
  addition). Follow the mock (`race_watcher_execute_bar_mock.html`).
- Render the grade as a compact pill: STRONG / MOD / LEAVE; **faint dot**
  for no-play. Reasons on **hover/tap** (title attr or a small popover —
  your call; keep it one tap, no row growth).
- Grades only for ACTIVE runners with a soft price typed and a promo
  armed; otherwise faint dot. Scratched rows: nothing.
- Colours consistent with the existing EV bands (green/amber/grey);
  reuse `OddsTable.module.css` patterns, don't invent a new palette.

## 4. Part C — grade-at-log stamping (the one write, fenced)

When a back bet is logged, stamp the runner's **grade + projected EV**
alongside the EV-at-log that's already captured:
- Frontend: extend the log snapshot that today carries `rawEv`/`promoEv`
  (ConfirmCard.tsx ~165, HedgeModal.tsx ~576) with `grade` and
  `promoEvProjected`; pass them as `grade_at_log` and
  `promo_ev_projected_at_log`.
- Backend: add the two nullable fields to `LogBetRequest`
  (racing.py:475) and persist them next to `raw_ev_at_log` /
  `promo_ev_at_log` (follow that exact pattern — same table/column
  style, nullable, no money math). This is the calibration substrate:
  every logged bet from now records what the watcher called, to score
  against the result later.
- **Strictly metadata.** Do not let the grade influence any stake, EV,
  settlement or promo-credit computation. If the existing EV-at-log
  columns live in a money module, add the two fields as inert
  companions only — do not alter surrounding logic.

## 5. Tests
- `raceWatcher.ts` unit tests against the **four 16 Jul live case
  studies** (design note §4): Pinjarra all-▼ (back-heavy pool → distrust,
  no false STRONG), Kilmore all-▲ (lay-heavy pool → distrust), Albion R10
  (unformed book → cannot STRONG), Rays Redemption (trend-vs-pool
  conflict → prefer trend, flag, no tier raise). Use realistic fixtures;
  assert grade + that trust caps fire.
- Column render tests (pill vs dot vs LEAVE; hover reasons present).
- Part C: snapshot carries the fields; payload round-trips; OFF/absent
  cases null cleanly.
- `uv run pytest` + `npm run build` green. Beat baseline **1520 / 224**
  at HEAD `fdd6c0b`.

## 6. Stop conditions
Stop and report if: grading would need a real money module changed
(beyond the two inert log fields); EV_projected can't reuse `evEngine`
without new maths; `sp_near`/trend/market-start data isn't actually on
the render as the map claims; or the column can't be added without
disturbing the locked column order.

## 7. Report
`race_watcher_phase1_report.md` in bethub-rebuild: what landed,
live-integration status per the S189 taxonomy (the grade is
**implemented-not-live** until exercised on a real open race; the trust
gate is tested against the four fixtures = corrected-by-logic, needs a
live look the first race day), the case-study test results, suite
numbers, commits. Be explicit that the grade **bands are a first cut**
awaiting the analytical-line calibration backtest — do not overclaim the
Calls are tuned.
