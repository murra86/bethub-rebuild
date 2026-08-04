# D1 pre-registration v3 — S267, 5 Aug 2026

Written BEFORE any query is run. v1 and v2 both failed; this is the
timeboxed final sitting agreed in S266. The two prior attempts are
retained as the record (`d1_preregistration_s266.md`,
`d1_preregistration_v2_s266.md`, `d1_memo_s266.md`).

## What changed since v2, and why this attempt can succeed

v1 and v2 died on POPULATION, not on method. The fit universe was ~61%
greyhound and harness while the operator bets 93% thoroughbred and 71%
metro; on his own tracks the recommended constant was **worse than no
projection**. The v2 gate then failed because metro held 196 races
against a registered minimum of 200.

S267's Betfair import removes that constraint: `betfair_historical` now
holds **17 unbroken months (Mar 2025 – Jul 2026, 232,980 runner rows)**
of settled BSP for AU thoroughbreds, joined to `races`/`runners`, with
99.8% place BSP and 99.99% actual off times. Truth is no longer scarce.

## The decision this serves

The Call's LEAVE verdict — the only Call output that changes the
operator's behaviour — exists **only** because the projection moves the
number: `LEAVE ⟺ evNow ≥ bar AND evProjected < bar`. So "how should the
Call project?" and "should the Call project at all?" are the same
question as "when should the Call say LEAVE?".

Everything else the Call renders (STRONG vs MOD) is money-inert: S267
confirmed the tiers stake identically by operator decision and nothing
in the code branches on them.

## The estimators being compared

At a snapshot taken `m` minutes before the jump, predict that runner's
realised Betfair SP.

| id | estimator | what it is |
|----|-----------|------------|
| `A` | `sqrt(back × lay)` | the live book alone — **what "don't project" means** |
| `B` | `sqrt(sp_near × lay)` | **what the engine does today** (`raceWatcher` substitutes `sp_near` for the back leg) |
| `C` | `sp_near` | the raw close projection, no blend |
| `D` | `back × (sp_near / back)^β` | the β family v1 proposed, fitted here |

`A` is the null. `B` is the incumbent — v1's fatal error was treating
`β = 1` as the incumbent when the live path has always been `B`.

## Registered population

**Unit of analysis: the RACE.** Runners inside a race share a book and a
pool; treating them as independent is what let v1's "imbalance kill"
survive (it inverted under a clustered test that was never run).

Registered set: `country = 'AU'`, `meeting_type = 'METRO'`,
`racing_code` thoroughbred-or-null, race has a matched `win_bsp` in
`betfair_historical`, and at least one usable snapshot in the window.

**Minimum: 200 races** (carried forward unchanged from v2 — the bar that
v2 failed at 196, restated here so it cannot be moved after seeing the
count).

## Gates, declared now

**G1 — POPULATION BEFORE FITTING.** The composition report runs and is
read FIRST: race counts by code, meeting type, state, month, field size,
and the share with usable BSP. **No estimator is evaluated until G1 is
reported.** If metro thoroughbreds fall below 200 races, the sitting
STOPS and the cheap version is adopted. This gate exists because it is
exactly the one v1 skipped.

**G2 — a time split must be a TIME split.** The out-of-time holdout is
the most recent complete months. Its composition must be reported beside
the training window's; a material composition shift (v1's greyhound
0% → 52.9%) invalidates the split rather than the finding.

**G3 — clustered inference.** Standard errors clustered by race. A
difference that does not survive clustering is not a finding.

**G4 — LEAVE preservation is a reported quantity.** Any recommendation
must state the number of LEAVE verdicts it dissolves, measured on the
operator's own logged bets. A package that dissolves LEAVE converts
protective verdicts into FIREs, which S266 priced at −$65 to −$130/week.

**G5 — no re-running of my own scripts as verification.** The headline
number must be re-derived independently, by a different route, before it
is reported. Re-running a script only proves the code agrees with itself.

## Windows

Matching the engine's own constants, not invented ones:
- `late`: 0 ≤ m ≤ 2 (`LATE_WINDOW_MIN` — the engine already ignores
  `sp_near` here and projects off the live book)
- `ramp`: 2 < m ≤ 15 (`TIME_RAMP_START_MIN`)
- `early`: 15 < m ≤ 60 (context only; the Call does not grade here)

## Metric

Mean squared error of `log(predicted) − log(actual BSP)`, per race then
averaged, so a 20-runner race does not outvote a 7-runner race. Reported
with a clustered CI. Scratched runners and any runner without a settled
BSP are excluded; the exclusion count is reported.

## Decision rule, fixed in advance

- **`B` beats `A`** (clustered, in the ramp window) → the projection
  earns its place. Report whether `D` beats `B` by enough to justify a
  constant nobody can re-derive; default to keeping `B`.
- **`A` beats `B`** → at metro meetings the market is already right.
  Recommend the Call stop projecting there — but only after G4 reports
  what that does to LEAVE, because removing the projection removes LEAVE
  entirely.
- **Indistinguishable** → change nothing. Adopt the cheap version:
  stamp honesty, full coverage, respect LEAVE, stop tuning.

Two of these three outcomes end in shipping no new constant. That is the
expected result and it is not a failure — S266's strategic note prices a
perfect Call at ~2–3% of turnover against the promos' ~21%.
