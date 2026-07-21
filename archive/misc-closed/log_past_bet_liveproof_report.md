# Report — Log Past Bet: live-proof + drop-counter floor recalibration (S209)

**Brief:** `log_past_bet_liveproof_brief.md` (S209, operator-approved).
**Status:** EXECUTED — live route-bridge resolve proven on the duplicate
market; drop-counter floor recalibrated to an empirical band. All tests
green; one checkpoint committed.
**Session:** 2026-06-30, ~15:02 → 15:08 ACST (DR-021 Adelaide, ACST =
UTC+9:30). Single bounded Code session.
**Bet-safety:** CLEAN — read-only GET over the 8400 tunnel + one
observability band constant. No settlement, money, lay, capture.db
open/copy/mount, VPS-side, or credential path.

**Re-anchor (before any edit):** the §5.2 floor lived in
`clients/vps_client/v1/_lookup_api.py` as the pair
`NO_MARKET_FLOOR_LOW = 0.003` (line 48) / `NO_MARKET_FLOOR_HIGH = 0.019`
(line 49), consumed by the `above_floor` property (line 129) and the
`.log()` line — confirmed present at those lines before editing. The
8400 tunnel was up (`GET /racing/races/today` → 200) at session start.

---

## 1. Live route-bridge resolve (§5.1)

Driven through the **real FastAPI app** (`TestClient` over the in-process
request path: route → client → live tunnel → DR-034 collapse), with
`BETHUB_CAPTURE_API_URL=http://127.0.0.1:8400` (the real tunnel — not a
mock, not a dead port). `TestClient` default raises on 500, so a silent
500 would have failed loudly.

**1a — the duplicate-market day lists the race once.**
`GET /api/v1/bets/lookup/races?race_date=2026-06-29&venue=Emerald` → **200**;
7 Emerald races, **R7 appears exactly once** (one logical race — no
fragment inflation):
```
{"race_number": 7, "jump_time": "2026-06-29T16:13:00+09:30",
 "code": "thoroughbred", "win_market_id": "1.259530858"}
```

**1b — the resolve returns 200 + the populated fragment, not the shell.**
`GET /api/v1/bets/lookup/race?race_date=2026-06-29&venue=Emerald&race_number=7`
→ **200**:
```
win_market_id = 1.259530858   event_id = 1.259530858   venue = Emerald
runners = 13                  event_name = "Flexihire Emerald Hcp (55)"
sample = [Desert Star/1136309, Cryptology/85016637, Jetpack Verdi/54704423]
```
The 3-fragment group (`1.259530858`) had a 0-runner PENDING shell at the
lowest id (2652588, venue "Emerald Downs"); the route returns the
**most-complete** fragment — 13 mappable runners (15 minus 2 null-
selection rows) at the canonical venue "Emerald", **never the empty
shell**. This is the live-proven evidence: the DR-034 read-time collapse
holds in the running request path on live data, not just the client-layer
smoke Brief 2 showed.

**1c — a clean single-fragment race still resolves.**
`…/lookup/race?race_date=2026-06-29&venue=Albury&race_number=1` → **200**,
`win_market_id = 1.259533736`, **9 runners**, "Surdex Steel Country
Boosted Mdn Hcp".

*(A literal click-through in the launched desktop app is available but not
required — the route returns the shape-stable models the UI renders.)*

---

## 2. Drop-counter floor recalibration (§5.2)

**Measured** the no-market drop fraction over the last 14 captured days
(the counter's own kept-set semantics, via `logical_races_for_day` per
date):

| date | kept | logical | no_mkt | empty_grp | fraction |
|---|---:|---:|---:|---:|---:|
| 2026-06-16 | 507 | 61 | 387 | 8 | 0.7633 |
| 2026-06-17 | 516 | 52 | 424 | 9 | 0.8217 |
| 2026-06-18 | 563 | 42 | 453 | 26 | 0.8046 |
| 2026-06-19 | 585 | 85 | 398 | 27 | 0.6803 |
| 2026-06-20 | 586 | 146 | 303 | 7 | 0.5171 |
| 2026-06-21 | 639 | 98 | 446 | 0 | 0.6980 |
| 2026-06-22 | 498 | 53 | 399 | 9 | 0.8012 |
| 2026-06-23 | 492 | 72 | 359 | 8 | 0.7297 |
| 2026-06-24 | 438 | 68 | 320 | 1 | 0.7306 |
| 2026-06-25 | 447 | 46 | 356 | 8 | 0.7964 |
| 2026-06-26 | 586 | 105 | 371 | 18 | 0.6331 |
| 2026-06-27 | 486 | 110 | 253 | 31 | 0.5206 |
| 2026-06-28 | 626 | 90 | 445 | 8 | 0.7109 |
| 2026-06-29 | 539 | 59 | 412 | 10 | 0.7644 |

**Central value & spread:** min **0.517**, max **0.822**, mean **0.712**,
median **0.730**, spread 0.305 (n=14). The low days are Betfair-rich metro
meetings (06-20: 146 logical races, 0.517; 06-27: 110, 0.521); the high
days are greyhound/harness-dominated (~0.82). All 14 are *normal* — the
high no-market fraction is the correct steady state (DR-032 / DR-034
stance 3: non-Betfair races are legitimately un-loggable and dropped).

**Chosen band:** `NO_MARKET_NORMAL_LOW = 0.40`,
`NO_MARKET_NORMAL_HIGH = 0.90` — flag when the fraction falls **outside**
[0.40, 0.90].
- *Reasoning:* the band brackets the observed normal [0.517, 0.822] with
  margin on both sides (≈0.12 below the min, ≈0.08 above the max), so it
  does not fire on any normal day, yet catches a genuine regression in
  either direction: **> 0.90** → enrichment stale / WIN market ids
  dropping out (fraction climbs toward 1.0 — the case Brief 2 §5.2 named);
  **< 0.40** → a whole non-Betfair meeting source vanished from capture
  (fraction collapses). A two-sided band is required because "flag when
  outside the normal range" (§5.2) is inherently two-sided; the prior
  0.003–0.019 floor predated this data and fired on every normal day.

**Fire / no-fire demonstration:**
```
frac=0.7644 (normal 2026-06-29)      outside_normal_band = False
frac=0.5171 (normal metro 2026-06-20) outside_normal_band = False
frac=0.8217 (normal greyhound)        outside_normal_band = False
frac=0.9700 (ABNORMAL enrichment break) outside_normal_band = True
frac=0.3000 (ABNORMAL source vanished)  outside_normal_band = True
```
Live counter line on a normal date now reads sensibly:
```
…race_date=2026-06-29 … no_market_fraction=0.7644 normal_band=0.40-0.90 outside_normal_band=False
```

---

## 3. Test / regression confirmation

- **`ruff check clients/vps_client/v1/_lookup_api.py`** → All checks passed.
- **`tests/clients/vps_client/`** → **71 passed** (unchanged; the band is
  observability-only — no test asserts on it).
- **Full repo** `uv run pytest -q` → **1202 passed, 1 xfailed** before and
  after (identical to the Brief 2 close — no regression). The 1 xfail + 4
  warnings are pre-existing and unrelated.
- **Checkpoint commit** landed after green (tree clean on `main`).

---

## 4. Self-assessment

**Anchor re-confirm:** the floor constants were at the stated lines
(`NO_MARKET_FLOOR_LOW`/`_HIGH`, lines 48–49) before editing; no drift.

**Scope adherence:** the edit is confined to the §5.2 drop-counter band in
`_lookup_api.py` — the two band constants (values + names →
`NO_MARKET_NORMAL_LOW/HIGH`), the property that consumes them (`above_floor`
→ `outside_normal_band`, now a two-sided range check), and its log line.
This is exactly the floor→band recalibration §5.2 commissions ("prefer a
band … flag when the fraction falls outside an empirically grounded normal
range"); a one-sided floor cannot express "outside the range", so the
comparison necessarily became two-sided. **Nothing else moved:** the
parser, Candidate-B window, fragment-collapse, and ordering are byte-for-
byte unchanged; finding #1 (the accepted runner-count→source→recency
ordering) was **not** re-opened; the four non-migrated surfaces, the broken
by-market route, capture.db, the VPS, schema, and all settlement/promo/
cash-modal paths were untouched.

**Anything odd:** the band's upper margin (0.822 observed max → 0.90 bound,
≈8pp) is tighter than the lower (≈12pp), reflecting the real distribution
(the lower tail runs wider, down to ~0.52 on metro-heavy days). 0.90 still
sits clear of every observed normal day while an enrichment break drives
the fraction toward 1.0; recorded for the operator's confirmation per §10.
The 14-day window is a single fortnight — if a seasonal mix shift (e.g. a
metro carnival week) pushed many days toward the 0.52 floor, the lower
bound could warrant a small review; the band is intentionally generous to
avoid that.

**Bet-safety statement:** CLEAN. Read-only GETs over the operator-managed
8400 tunnel for the live resolve and the 14-day measurement, plus one
observability band constant. No Betfair settlement, money-movement, lay-
placement, or live-betting path was read or written; capture.db was never
opened/copied/mounted; no VPS file/service/git change; no new
auth/credential.

---

*Live-proof complete: the route-bridge resolve returns the populated
fragment (200, 13 runners) on the Emerald duplicate market, the day lists
it once, and a clean race resolves 200 — the S189 live-proven gate is
satisfied for operator-Claude to mark Log Past Bet live-proven. The
drop-counter floor is recalibrated to [0.40, 0.90]; operator to confirm
the band per §10.*
