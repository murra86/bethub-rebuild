# D1 v3 memo — S267, 5 Aug 2026. **D1 CLOSED: ship no constant.**

Pre-registration: `d1_preregistration_v3_s267.md`, written before any query.
This was the timeboxed final sitting agreed in S266.

## Answer in one line

**On the operator's own races the Call's close projection is a
substantially WORSE price estimate than the live book alone — so no β is
adopted and the projection is not re-tuned. It is also not removed,
because the only thing it drives is LEAVE, and LEAVE's own evidence
points the right way but is too thin to act on.** Cheap version adopted.

## G1 — population, reported before any estimator (the gate v1 skipped)

Registered set: AU + METRO + present in Betfair's own ANZ **Thoroughbreds**
file + a usable snapshot in the ramp window. **579 races**, against the
registered minimum of 200 carried forward from v2.

Matching the ANZ Thoroughbreds file *is* the thoroughbred test, which
removes the code ambiguity that sank v1 — `racing_code` is NULL on 31,995
of 36,045 AU races, so a code filter could never have carried this.

**A constraint the import did NOT remove, stated plainly:** the BSP truth
now spans 17 months, but `sp_near` capture only begins in Apr 2026, so the
usable window is **2026-05 to 2026-07 — three months**. The predictor, not
the outcome, is the binding scarcity. `field_size` is unpopulated across
the set, so no field-size cut was made.

Composition: NSW 26%, WA 26%, VIC 21%, SA 14%, QLD 12%. Belmont 152,
Sandown 74, Doomben 68, Rosehill 50, Flemington 45.

## G2 — the time split is a time split

Train = May+Jun (374 races), holdout = Jul (205). State mix moves modestly
(VIC 16%→28%, NSW 27%→25%) with every state present on both sides. This is
NOT v1's composition collapse (greyhound 0%→52.9%), so the split stands.

## The result

Mean squared error of log(predicted) − log(realised BSP), per race then
averaged, clustered by race.

| estimator | ramp (2–15 min) | late (0–2 min) |
|---|---|---|
| **A — live book alone**, `sqrt(back×lay)` | **0.03994** | **0.02202** |
| **B — the incumbent**, `sqrt(sp_near×lay)` | 0.06565 | 0.03541 |
| C — raw `sp_near` | 0.08673 | 0.05045 |

Paired by race, A − B = **−0.02571 [−0.03120, −0.02101]** in the ramp
window and **−0.01338 [−0.01711, −0.01027]** late. **Projecting makes the
estimate ~64% worse in the ramp window and ~61% worse late**, and the
clustered interval excludes zero by a distance.

Holdout (July, untouched during fitting): A 0.03045, B 0.04663 — same
ordering, same size.

**The β family fitted itself to β = 0.00** on the training window. The best
available member of the family v1 proposed is "do not project".

## G5 — re-derived independently, three other ways

Not by re-running the above. Three different routes, all agreeing:

1. **Bias decomposition.** `sqrt(back×lay)` sits at bias −0.011 with
   spread 0.202. `sp_near` sits at bias **−0.109** with spread **0.281**.
   So sp_near is systematically **~11% LOW against the realised BSP and
   ~40% noisier**. This is not "the market is already right" — it is the
   projection being a poor estimate of the thing it names.
2. **Regression** `log(BSP) ~ log(book mid) + log(sp_near)`: book mid
   **+0.883**, sp_near **+0.132**. sp_near does carry a little independent
   information — it is not noise — but the engine substitutes it for the
   back leg, which weights it roughly **four times** what it earns.
3. **Sign test over races** (non-parametric): the live book beats the
   projection in **359 of 499 races (71.9%), z = 9.8**.

## G4 — what removing the projection would do to LEAVE

`LEAVE ⟺ evNow ≥ bar AND evProjected < bar`. Remove the projection and
evProjected collapses onto evNow, so **LEAVE can never fire again**. This
gate therefore decides the recommendation, and it is the reason the
answer is not simply "rip it out".

On the operator's 282 graded bets:

| grade | n | avg evNow | avg evProj | struck price | actual win | implied win | edge |
|---|---|---|---|---|---|---|---|
| STRONG | 28 | 22.4 | 23.1 | 4.58 | 32.1% | 26.3% | **+5.8 pts** |
| MOD | 230 | 24.6 | 24.4 | 5.45 | 25.7% | 23.9% | **+1.8 pts** |
| LEAVE | 24 | 9.3 | −2.4 | 4.16 | 12.5% | 26.7% | **−14.2 pts** |

The obvious confound is that LEAVE might simply select longer shots. **It
does not** — LEAVE bets were struck at the *shortest* average price of the
three and still won least. The ordering survives the control and gets
stronger.

**But n = 24.** Three wins against 6.4 expected is about 1.6 standard
deviations — roughly p ≈ 0.06 one-tailed. Directionally right, **not
established**. It would be exactly the v1 mistake to act on it.

Note also what LEAVE actually selects: evNow ≈ 9.3 against ≈ 23 for the
other two. **LEAVE fires on marginal bets**, and a projection biased 11%
low is precisely what tips a marginal number under the bar.

## Recommendation — and it ships nothing

1. **Adopt no β and re-tune nothing.** Every route says any positive
   weight on raw `sp_near` makes the price estimate worse. v1's package
   would have made the Call worse on the operator's own tracks.
2. **Do not remove the projection either.** It is the sole source of
   LEAVE, LEAVE's evidence points the right way, and 24 observations
   cannot justify deleting a protective verdict.
3. **Take the cheap version**, as S266 pre-agreed: stamp honesty, full
   coverage, respect LEAVE, stop tuning the projection.
4. **Operational truth for the operator, which costs nothing to know:**
   when the Call says LEAVE, part of that is the projection running
   systematically pessimistic. Read LEAVE as *"this one is marginal"*,
   not as *"the market says no"*.

## What would settle it, and when

LEAVE needs roughly **3–4× its current 24 observations** to separate from
noise at this effect size. Grades are already stamped on every logged bet
(`grade_at_log`), so this accrues by itself — no build required. Revisit
when LEAVE passes ~80 settled bets.

The cheaper unlock, if it is ever wanted: `sp_near`'s −11% bias is a
measured, stable, single-number offset. Correcting it would make projected
EV honest without touching the projection's structure. **Not recommended
now** — it would dissolve some LEAVEs, and G4 says we do not yet know
which way that trades.

## Strategic note, carried forward from S266 and now earned

A perfect Call is worth ~2–3% of turnover against the promos' ~21%. Three
sittings have now returned "change nothing", each for a better-evidenced
reason than the last. **That is the answer, not a failure to find one.**
D1 is closed.
