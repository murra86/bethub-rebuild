# Priority flags — operator, Thu 16 Jul 2026 (S241)

Two features flagged **HIGH priority** by the operator, "ideally before Saturday 18 Jul".
Recorded verbatim intent + honest scheduling assessment. Both need operator walkthrough
before build (normal drafts → walkthrough → fenced brief process).

## 1. Race watcher — advisory targeting

Operator intent: watching a race set with (e.g.) 2nd/3rd insurance promos armed, the tool
should watch ALL signals per runner and surface targets in real time — "this runner you've
priced looks super promising because X and Y".

Two-tier shape agreed in discussion (16 Jul):
- **Tier 1 — deterministic target board (no LLM, no cost):** score/rank every runner with
  typed soft odds across watched races: promo EV band + BF Close direction WITH pool-
  coherence gate (sum of 1/sp_near vs 100% — both failure modes observed live 16 Jul:
  Pinjarra back-heavy all-▼, Kilmore lay-heavy all-▲) + trend/$$ spike + thinness + reason
  chips. Display-only, fenced. ~1 day. **Candidate for Fri 17 pm post-reset IF reset lands
  clean + early and operator approves; otherwise first build next week.**
- **Tier 2 — Claude watcher (paid service — operator decision needed):** periodic snapshot
  → Claude API → prioritized cross-race advice in plain language. ADVISORY-ONLY hard fence
  (never places/logs/settles). Cost ~cents-to-dollars per racing day (small model +
  caching). Post-Saturday discussion.
- Delivery vehicle for the price-pressure research cycle-3 "NOW A-cluster spec".
- Strategy context (operator, 16 Jul): insurance bets are NEVER layed — targeting =
  positive promo EV + expected shortening, to maximise unlayed EV at jump.

## 2. TAB API integration

Operator intent: TAB is the main promo driver right now; embed the TAB API "next on the
list".

Presumed value (to confirm at walkthrough): auto-populate SOFT ODDS for TAB (kills the
biggest manual-entry cost on the race page and makes the watcher's EV column live without
typing), plus whatever promo/meeting data the API exposes.

Assessment: NOT safe to build before Saturday — new external integration (endpoints, auth,
ToS, rate limits, new client under contract governance) landing 2 days before the biggest
bet day contradicts the week's hardening discipline. **Plan: scoping brief by Fri/Sat
(endpoints, auth model, soft-odds mapping, risks), build from Monday 20 Jul with zero
unknowns.**

## 3. Race results retention (flagged 16 Jul eve — minor, future build)

Operator observation: the race page already knows interim results early (the Betfair
prices read carries runner WINNER/LOSER status the moment the market closes). Ask:
retain recently-jumped race cards in a "Results" section for a while so results are easy
to look up in-tool.

Assessment: LOW risk, display-only. The data is already flowing (live read shows
settlement status at close; the capture results read built for the settle door covers
the after-the-fact case incl. margins/SP). Shape: sidebar "recent results" group holding
the last N hours of jumped races, card shows placings. **Operator-scheduled (16 Jul eve): build Fri 17 pm post-reset**, riding with the Tier-1
watcher slot — deliberately NOT built Thursday night (zero soak before the frozen
day + Saturday; race-list sidebar is core Saturday navigation). Friday evening racing =
the live soak.

## Sequencing proposal (for operator confirmation at the reset session)

1. Fri am: close-out + reset (unchanged).
2. Fri pm (if clean): Tier-1 target board build, fenced, display-only.
3. Fri/Sat: TAB API scoping brief delivered for reading.
4. Sat: bet day on the proven tool — no new code.
5. Mon: TAB API build; then Tier-2 watcher decision (API key/cost sign-off) + build.
