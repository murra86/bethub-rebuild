# Call/Trend quality + TAB latency — research brief (S250, operator-flagged)

Operator observation (22 Jul, Doomben R1 / Sandown R1 screenshots):
Call column "giving moderate recommendations on ones that look way
off and leaving ones that look pretty good"; Trend column "a lot of
noise"; TAB column good but wants cadence tightened in the final
minutes "where all the money comes in". Commissioned as RESEARCH —
no engine changes yet.

## 1. What the screenshots actually show (traced through the code)

**Montostratus MOD @ ~4m (Sandown R1)** — the "way off" call.
The watcher projects field probabilities off `sp_near` (BF CLOSE)
except in the final 2 min. Montostratus: live book 220–230, sp_near
**88.88**, TAB soft 126. If the close really crashed to ~89, TAB 126
is a huge overlay → projected EV cleared the +5% bar → MOD (trust
gates blocked STRONG). The maths did what the design says; the INPUT
was the problem — a ~60s-cached BSP projection on a $143-matched
longshot, 2.6× away from the live book, with **no sanity guard**
against live-book divergence. This is the exact "sp_near trust"
question the race-price-pressure project flagged (Cycle-1: best NOW
signal = projected-SP convergence gap — i.e. the GAP is information,
but only when sp_near itself is trustworthy).

**Had It All LEAVE @ 5m (Doomben R1)** — the "pretty good" one.
+5.2% promo EV now (the only green on the page), BF CLOSE 2.52 vs
back 2.48 → projected EV at close dips under the 5% bar → the
designed "tempting-but-trap" branch: LEAVE = "playable this second,
projected to fade by jump — don't chase" (the Coldstream case).
Working as designed; the open question is whether a 2.48→2.52
projection deserves the authority to kill the only positive-EV call
on the card. Label is also opaque — operator read LEAVE as noise,
not as a deliberate trap warning.

**Dots everywhere else**: EV deep-negative → NONE. Correct.

**Trend column**: raw % change of best BACK over a rolling 5-min
window (±0.5% flips the arrow; $$ = matched volume +25% in-window).
On longshots one Betfair tick is ±10–20% → big scary numbers on thin
runners; two ticks apart 24s showed 21.1% → 15.8%. Not implied-prob
based, not volume-weighted, no per-runner tick normalisation —
exactly the naive form Cycle-2 rejected in favour of matched-flow +
tick rule (C2, spoof-resistant WoM).

**Design doc's own caveat** (`raceWatcher.ts` header): every band and
constant is a FIRST CUT — "the analytical-line backtest against
logged `grade_at_log` outcomes is what tunes them. Do not read the
current thresholds as tuned." Grades have been logged since S241;
the calibration data now exists and has never been used.

## 2. Proposed research plan (analytical line, bethub-analytical)

R1. **Grade backtest** (the designed calibration path): pull logged
    `grade_at_log` + captured race outcomes; score STRONG/MOD/LEAVE
    against realised EV. Output: are the bars (5% / 3% margin), the
    trust gates, and the LEAVE branch earning their keep?
R2. **sp_near trust rule**: measure sp_near-vs-live-book divergence
    against eventual BSP across captured races (data in hand from
    the capture DB). Candidate: clamp/ignore sp_near when it
    diverges >X% from the live mid outside the final window, or
    weight by runner matched volume. The Montostratus artifact is
    the red-before case.
R3. **Trend v2**: implied-prob delta (not price %), matched-flow
    weighting per Cycle-2 C2, tick-normalised for longshots,
    volume-conditioned display (suppress % on runners under a
    matched floor). Piggy-backs on race-price-pressure Cycle-3
    candidates (tick-rule backtest, NOW A-cluster spec).
R4. **Label pass** (UI, cheap, after R1): LEAVE → something that
    says what it means ("FADING" / "TRAP"?); reasons string is
    already built per runner — consider surfacing it on hover/tap.

## 3. TAB latency — the honest budget and the levers

Today (post-S250 checks): TAB's own edge updates ~7s (their site
polls the same endpoint at ~7s; no push channel exists — proven
S249). Our live pool polls 8s inside T-5m, 15s T-30m→T-5m; fetch
+ tunnel ≈ 0.5–1s. Display age in the final minutes: avg ~8–12s,
worst ~16s (phase-stacking of two independent clocks: edge refresh
+ our poll).

- **Milliseconds is not on the table** via this API — there is no
  live wire to TAB. The floor is the edge's own ~7s refresh.
- **Lever 1 (biggest, zero extra TAB load): decouple.** A VPS-side
  background poller owns the active race's TAB fetch on its own
  clock; the UI reads the VPS's latest copy every 1–2s (like the
  Betfair 1s poll). Kills phase-stacking → avg display age ≈
  edge_age + ~1s ≈ 4–5s. Same number of TAB requests.
- **Lever 2: final-window interval 8s → 7s or 6s** — matches the
  site's own cadence, so the traffic shape stays browser-like.
  Modest gain (~1s avg). Never poll FASTER than the site does
  (fingerprint conservatism after the 21-Jul lesson).
- **Lever 3 (research first): edge-TTL probe** — capture response
  headers (Age / Cache-Control) on a near-jump race to learn the
  actual edge refresh period. If the object only refreshes every
  ~7s, faster polling buys nothing; if it's origin-fresh per
  request, lever 2 is worth more. One probe run, probe script
  already does the fetching (add header logging).

## 4. S250 addendum — the anticipation commission (operator, same day)

Operator's goal, verbatim intent: calls should fire BEFORE the book
reprices — a negative-EV-now runner whose numbers say it's moving to
positive should already be MOD/STRONG; use the information as fast as
the bookmakers do.

Corrective finding first: the engine ALREADY calls on projection —
`evProjected ≥ bar` grades STRONG/MOD even when EV-now is negative.
The operator hasn't seen it behave that way because the projection
INPUT (sp_near) is untrusted garbage on thin runners and the movement
signal is tick noise — i.e. the forward-looking design exists; its
eyes are bad. The research goal is therefore NOT "add anticipation"
but "make the anticipation trustworthy and fast".

The decisive data insight: the capture DB holds WEEKS of paired
Betfair + TAB snapshots with timestamps. Betfair leads; TAB reprices
after. The edge the operator describes IS the lag window between a
Betfair move and TAB's reprice — and its size, frequency, and
exploitability are measurable offline TODAY:

- **A1 (new, highest value): Betfair→TAB lead-lag measurement.**
  Align both snapshot streams per runner; for every TAB reprice, how
  long before did Betfair's implied prob move, and was the direction
  predictable from matched-flow (Cycle-2 C2 tick rule)? Output: lag
  distribution by time-to-jump band + a hit-rate curve → "when BF
  moves X%, TAB reprices within Ys, Z% of the time". That number IS
  the actionable window.
- A2 = R1 grade backtest (unchanged). A3 = R2 sp_near trust rule.
- **B (signal design):** an anticipatory tier built from measured
  ingredients: EV-now off CURRENT TAB price (already transiently
  positive inside a lag window), BF matched-flow direction, TAB
  staleness-vs-BF gap, drift-since-open + TAB flucs cadence (flucs
  are in the payload we now parse opens from — the fluc TIMES tell
  how fast this market's TAB desk reprices).
- **C:** re-tune bars on A2's calibration, add the tier, then run it
  SHADOW (log-only grades vs outcomes) for a race day or two before
  the operator acts on it.

## 5. Status

Research commissioned S250; no engine or transport changes made.
Screenshots archived in operator's Desktop (12:05 / 11:57 / 11:51
pair). First sitting: R1 backtest + the edge-TTL probe run (both
data-in-hand, no live risk).
