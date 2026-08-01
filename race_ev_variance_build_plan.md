# Race-level EV & variance indicator — build plan (S253)

Proposal for operator sign-off. Nothing built yet.

## 1. What we're building (confirmed)

A **read-only panel on the race page**. Two states:

- **Standing:** given the promo bets you already hold on this race (marked to
  their locked prices), show race-level **EV in $ and %**, total **exposure**,
  and a **consistency** read (chance the race turns a profit; likely P&L range).
- **At the margin:** when you type a price for a candidate runner C (before
  placing), show the **ΔEV and Δvariance** adding C would cause — does it lift
  EV, and does it *steady* or *concentrate* the race.

Point-in-time at current prices, recomputed as prices move. No money-path
writes, no forecasting of drift. It sits beside the odds table / promo bar.

## 2. Calculation spec

### 2.1 Inputs, all available at view time
- **Placed bets on this market** — runner, promo spec, stake, **locked price**.
  From `bet_legs` (by `betfair_market_id`) joined to `bets` (`promo_template_id`,
  stake, `matched_price`, `promo_ev_at_log`).
- **Candidate C** — runner, promo, stake, typed price (from the arm state the
  page already holds).
- **Live field** — Betfair back/lay per runner → de-vigged win probs → Harville
  place probs. The race page **already computes this** (`fieldProbs`).

### 2.2 Per-bet EV — mark-to-market
Each bet's EV = `evEngine.promoEV` run with the bet's **own locked price** (or
C's typed price) and the **current** field probabilities. This is the one real
correction over reading the screen: a placed bet is valued at the price you
hold, not the drifted screen price. EV of a bet already reflects only its own
runner (proven additive), so this is exact.

### 2.3 Race EV — a sum
Race EV$ = Σ placed-bet EV$. With C armed: + C's EV$. **ΔEV = C's own EV.** No
interaction term. Race EV% = race EV$ ÷ total staked (stake-weighted — flagged
below as a display decision).

### 2.4 Variance & consistency — Plackett-Luce Monte Carlo
Variance is the part that is *not* additive, so it needs the joint finishing
order. Method:
- Sample K≈8,000 finishing orders from the live win probs via Gumbel-max
  Plackett-Luce (the fast, vectorised method already used in this session's
  scripts).
- For each sample, compute every bet's realised P&L (win → `stake·(odds−1)`;
  insured place → `−stake·(1−conv)`; else → `−stake`) and sum to a portfolio
  P&L. This handles any mix of promo types and runners uniformly.
- Report from the K outcomes: **P(race P&L > 0)**, the **10th–90th percentile
  range**, and std (secondary).

### 2.5 Marginal deltas — common random numbers
When C is armed, recompute the portfolio P&L on the **same K sampled orders**
(same seed) with C added. Δvariance and ΔP(profit) then reflect **only C**, not
Monte-Carlo noise — the delta is stable as you type. Seed is derived from the
market id so the standing numbers don't flicker between 1-second polls.

### 2.6 What to display — **needs your decision (§6)**
Recommended: "**chance this race profits: 52%**", "**likely between −$140 and
+$260**", "**race EV +$14 (5.6%)**", and on arming C: "**+$8 EV, profit-chance
50%→57%**". Std hidden behind a hover. Confirm what you actually want to see.

### 2.7 Known approximation (honest note)
EV uses the tool's corrected Harville marginals (to match the screen exactly);
the variance MC uses standard Plackett-Luce, whose implied 2nd/3rd marginals
differ slightly. Variance is a *read*, not a settlement figure, so this is
acceptable — but it's recorded so no one later "finds a bug" that is really this
choice. Reconcilable later by reweighting if ever wanted.

## 3. How it embeds in the tool
- **New pure module** `ui/web/src/ev/racePortfolio.ts`, beside `evEngine.ts` /
  `raceWatcher.ts`. Pure functions, fully unit-testable. Reuses `evEngine`.
- **Data wiring** — one new read-only query for placed bets on the open market;
  the field probs already exist on the page.
- **UI** — one read-only panel component; no writes to the money path.
- **Performance** — the MC is ~8k×(≤16) trivial ops (sub-millisecond); still,
  wrap it in a `useMemo` keyed on (field snapshot, placed bets, candidate),
  debounce the candidate price input, and use the stable seed so it doesn't
  churn on every poll.
- **Gates** — engine unit tests (vitest) + `npm run build` (the frontend gate);
  Fri = sanity only, Sat = no deploy, target **Sun/Mon deploy**.

## 4. Development model — spec-first, small team

I do **not** recommend a large agent organisation. This is a modest, well-
specified feature; the risk is not the coding, it's (a) agreeing what to display
and pinning the maths, and (b) verifying the engine matches the validated Python.
So the model over-invests in **spec** and **verification** and keeps the build
lean.

**Shape: hub-and-spoke around a frozen contract, not a chat-room of agents.**

**Phase 0 — Freeze the contract (me + you, no agents).** Produce two things all
builders treat as read-only truth: this spec (the §6 decisions resolved) and an
interface stub `racePortfolio.ts` (types + function signatures, no bodies). This
is the single source of truth. *This phase is 80% of the value and risk.*

**Phase 1 — Build in parallel against the frozen interface (4 agents):**

| Agent | Owns | Input | Output | Depends on |
|---|---|---|---|---|
| **Engine** | `racePortfolio.ts` bodies — EV sum, PL Monte-Carlo variance, marginal deltas | spec + interface | module + unit tests | contract only |
| **Data** | the read-only query assembling placed bets + locked prices + field probs for the open market | spec + interface | a hook/selector | contract only |
| **UI** | the read-only panel + its states (no bets, one bet, candidate armed, loading) | spec + interface **types** | component | contract only |
| **Verify** | golden fixtures from the Python investigation; assert TS engine matches to tolerance; adversarial edge cases (scratchings, missing lay, same-runner double, single bet) | spec + Python scripts | test suite + report | contract only |

Every agent reads the **same frozen contract** and builds against the interface
boundary — so the UI agent builds before the engine is finished, and the verify
agent derives truth independently from the Python. **They do not talk to each
other; alignment comes from the frozen contract, not live chat.** If a build
reality forces a spec change, it routes through **me** (single owner), I amend
the contract once, and re-broadcast. That is the information-sharing mechanism,
and it is deliberately a shared document, not inter-agent messaging.

**Phase 2 — Integrate & verify (me).** Wire engine + data + UI, reconcile, run
the verify suite and `npm run build`, sanity-check on a live race, then it's
ready for the Sun/Mon deploy window.

Runs cleanly as a **Workflow** (deterministic: contract → parallel build → integrate),
or as four spawned agents I coordinate. Either way it's ~4 build agents + me,
not an org.

## 5. My honest recommendation
- **Right-size it.** Four build agents + a lead is the ceiling, not the floor. A
  single focused implementation session could also do it — but given how much
  independent review caught this session, I'd keep the **Verify agent** even in
  the smallest version. It's the cheapest insurance we have.
- **The spec is the project.** Get §6 decided and the maths frozen, and the build
  is routine. Skip the coverage-suggester (phase-2 idea) and Kelly staking for
  now — land the EV+variance read first, then see if you even want more.
- **Frame the UI honestly** (from the last finding): "am I covering this race
  well," not "have I made this race safe." No single race is tick-steady.

## 6. Decisions I need from you before Phase 1
1. **What to display** — is the recommended set in §2.6 right? Do you want
   percent, dollars, or both leading? Std shown or hidden?
2. **Candidate stake** — when previewing C before you've set a stake, do we
   assume the promo's max stake, or wait for you to type one?
3. **Consistency metric** — is "chance the race profits + P&L range" the number
   you want, or would you rather see something else (e.g., worst-case, or a
   0–100 "coverage" score)?
4. **Scope for v1** — EV + variance read only, and hold the coverage-suggester
   for later? (My recommendation: yes.)
