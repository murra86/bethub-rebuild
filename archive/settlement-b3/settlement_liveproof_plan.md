# Settlement worker — live-proving plan

**Drafted:** Session 220, 2026-07-02 17:25 ACST (DR-021 Adelaide anchor).
**Author:** Chat (governance / operator-facing checklist).
**Status of the worker today:** built, wired, triaged clean — but **OFF by default and never run against real Betfair**. In plain terms: the auto-settlement code exists and passed its bench tests, but it has never settled a single real bet with real money. This plan is how you take it from *built* to *proven*.

**What this document is:** the operator's run-book for switching the auto-settlement worker on in the live app, watching it settle real bets, and confirming it behaves correctly — so we can call it **live-proven** and tick off cutover blocker **B2** (the cheapest money-path win on the runway).

**What this document is NOT:** it does not flip any switch, touch any settlement code, or settle anything. Drafting it changed nothing. The flip itself is your action, done between sessions using the checklist below.

**Grounding:** `settlement_worker_build_report.md` (what was built), `settlement_worker_code_goahead.md` (the safety invariants you signed off), `settlement_worker_build_brief.md` (the spec). Cutover context: `cutover_readiness_map.md` (B2).

---

## 1. Plain-English: what the worker does

Right now, when a real bet settles on Betfair, nothing in v3 automatically pays it out or marks it lost — settlement is manual. The auto-settlement worker changes that: once switched on, it wakes up **every 60 seconds**, looks at your pending bets, reads how each one actually settled on Betfair, and marks them **won / lost / void** without you touching them.

The catch is the awkward cases — dead-heats, and races where a runner was pulled out late (which reduces the payout under the bookmaker's "Rule 4" deduction). Getting those wrong means **overpaying yourself in the books' eyes**, which is exactly the kind of settlement friction we don't want. So the worker is built to be **cautious**: anything it can't work out cleanly, it **parks** into a manual review queue rather than guessing. It never silently pays a winner in full when there's a reason the payout should be reduced.

That "park, don't overpay" behaviour is the whole safety story. Live-proving is about watching it actually do that against real races.

---

## 2. Preconditions — before you flip anything

Tick all of these first. If any is not true, stop — the worker either won't start or shouldn't yet.

- [ ] **App is running in LIVE mode** (`BETHUB_BETFAIR_MODE=live`), with real Betfair credentials present. This was provisioned back at S189 — but confirm it's still live, not mock. In mock mode the worker refuses to start (by design), so nothing would happen.
- [ ] **You have real pending bets that will settle soon.** There's nothing to prove against an empty book. Ideally a normal Strategy 1 (Safety Net) day with a handful of live bets going through.
- [ ] **Real exposure is deliberately small for the first window.** Treat the first proving run like a test flight — low stakes, bets you're comfortable watching settle by hand as a cross-check.
- [ ] **You're at the machine (or watching the logs) for the first settlements.** This is a supervised proving run, not fire-and-forget.
- [ ] **You know how to flip it back off** (Section 6). Rollback is one switch and it's harmless.

---

## 3. The flip — switching the worker on

The worker is gated on **two** conditions, both of which must be true for it to run: the app must be in live mode (precondition above), **and** the settlement flag must be on. The flag defaults OFF, which is why nothing has run yet.

**The flag:** `BETHUB_SETTLEMENT_WORKER`

**Set it to on** — any of `on`, `true`, or `1` works — in the **launcher environment / app config** (the same place `BETHUB_BETFAIR_MODE` is set). It's read at app startup.

- [ ] Set `BETHUB_SETTLEMENT_WORKER=on` in the live launcher/config.
- [ ] Restart / start the app so it picks up the flag.
- [ ] Confirm at startup that the worker started — you should see it come up in the app logs (the settlement worker announces its bring-up, same as the streaming socket does). If the app started but the worker didn't, check you're actually in live mode.

Once up, the worker runs its **60-second cycle** automatically. Each cycle runs **both passes**: it settles freshly-pending bets, and it re-checks the parked (PROVISIONAL) ones. You don't trigger anything — you watch.

**One reassurance:** if the worker hits an error starting up, it's built to **log the error and let the app carry on** — it can't take the app down. Worst case on start-up trouble is "the worker didn't run," never "the app crashed."

---

## 4. What to watch — the heart of live-proving

This is where proving actually happens. You're watching for three things: clean bets settling correctly, awkward bets parking correctly, and — the subtle one — **no bet silently overpaid**.

### 4a. Clean winners and losers settle themselves
- [ ] A clear-cut winner (no dead-heat, no late scratching) flips to **SETTLED_WON** on its own within a cycle or two of the race settling on Betfair.
- [ ] A clear-cut loser flips to **SETTLED_LOST**.
- [ ] A voided market comes through as **void**.

If clean bets settle correctly and promptly, the core engine works.

### 4b. The verification records — the park decisions (watch these closely)
Every time the worker meets a **winner in a race where a runner was removed**, it writes a **verification record** — a structured line in the app logs — recording exactly what it decided. There are three possible decisions, and you want to eyeball each one against reality:

- **`parked`** — it judged the payout reduction *material* (or found a dead-heat) and pushed the bet into the manual review queue rather than paying it. Confirm the parked bet genuinely deserved a reduction.
- **`fallback_flagged`** — it *couldn't read* the reduction factor for a removed runner, so it parked the bet anyway to be safe. Confirm — this is the "when in doubt, park" safety net firing.
- **`paid_full`** — **this is the one to watch hardest.** Here the worker decided a removed-runner reduction was *too small to matter* (below the 2.5% threshold on a win market) and **paid the winner in full**. This is a *negative* decision — the bet settles silently to SETTLED_WON with no park. If the threshold is wrong, or the market type was misjudged, a genuine over-payment hides exactly here. **So read every `paid_full` record and confirm the full payout was actually correct** — i.e. that the removed runner's reduction really was trivial and Betfair applied nothing.

- [ ] Read **every** verification record during the proving window — especially the `paid_full` ones.
- [ ] For each, confirm the decision matches what actually happened on Betfair.

### 4c. The manual park queue
- [ ] Parked bets show up in the **manual review queue** flagged with the reason **`provisional_dead_heat_or_reduction`**. Confirm they're landing there and that resolving them by hand still works exactly as it did before the worker existed.

### 4d. The money-path invariant — the non-negotiable
- [ ] **Nothing is ever silently overpaid.** Across the whole window: every winner that settled to full winnings was genuinely a clean full-payout case; every case with a real reduction either parked or (for a sub-threshold win-market reduction) is accounted for in a `paid_full` record you've checked. No bet paid more than it should have, unseen.

> **Known narrow exposure to watch for (already flagged in the build):** the worker works out whether a bet is a *win* market or a *place* market from signals on the bet itself, because the settlement feed doesn't state it directly. There's a rare corner — a **place-market winner that carries none of the usual "place" signals** — where a small place-market reduction could be judged immaterial and the bet **paid in full when it shouldn't be**. It's unusual (Betfair normally names place markets "To Be Placed," which the worker catches), and every such case emits a `paid_full` record — but that record is an *after-the-fact audit*, not a park. So during proving, **pay special attention to any `paid_full` record on a place-type bet.** Closing this corner properly is a named follow-up (Section 7), not part of this proving run.

---

## 5. Success criteria — when can we call it live-proven?

Green bench tests are **not** enough (that's the S189 lesson — passing fixture tests only means *built*, never *proven*). To declare the worker **live-proven** and clear blocker B2, all of the following must hold across a defined observation window:

- [ ] The worker ran against **real Betfair** in the live app across a meaningful window — say, **a full race day / at least N real settlements** (pick N with enough clean winners, clean losers, and at least one removed-runner or dead-heat case to actually exercise the park path; if no awkward case turns up naturally, the window isn't done).
- [ ] **Clean winners, losers, and voids settled correctly end-to-end**, on their own.
- [ ] **At least one park decision was observed and confirmed correct** — ideally one of each kind you can get (`parked`, `fallback_flagged`, and a checked `paid_full`).
- [ ] **Every `paid_full` decision in the window was checked and was correct** — no hidden over-payment.
- [ ] **The money-path invariant held** across the whole window — nothing silently overpaid.

Meet all five → the worker is **live-proven**, B2 is cleared, and it can be left on for normal running.

Once proven, the verification log lines can be quietened (they're deliberately lightweight and retirable) — but leave them loud until you're satisfied.

---

## 5b. Confirming the criteria — the review loop with Chat (the mechanism)

You don't judge the five criteria alone. As you bet, we run a **review pass** together — **read-only** — to confirm them against the real data:

- **What we look at:** the worker's **verification records** (the `parked` / `fallback_flagged` / `paid_full` lines in the app logs) and the **settled / parked bet states** in the operational store.
- **How we group it:** by **cycle**, not single bets — the insurance bet, the free bet it triggers, and the conversion as one unit (our standing "one bet whose outcome drives another is one analytical unit" rule) — so we confirm the *whole pathway* settled right, not just isolated legs.
- **What we check:** clean bets settled correctly; each park was deserved; **every `paid_full` was genuinely correct** (against the reduction factor the worker itself recorded); nothing silently overpaid.
- **How we finish:** Chat keeps a running tally against the five criteria across days and tells you honestly when the window is *genuinely* met — including flagging when a path hasn't been exercised yet (e.g. no removed-runner case has occurred), so we never call it proven early.

**The review pull:** a single **read-only** command that gathers a day's settlement decisions + cycles into a review-ready summary, so each pass is fast. It is built and validated on the **first real review pass** — shaped against the actual log + store format once the worker has produced real records, rather than guessed at up front.

**Boundary:** the whole review loop is read-only — Chat reads the logs and the store, and never touches a bet, a settlement, or the flag.

---

## 6. Rollback — if anything looks wrong

Rollback is one switch and it is **harmless**:

- [ ] Set `BETHUB_SETTLEMENT_WORKER=off` (or remove it) in the launcher/config and restart.
- [ ] The worker stops. Settlement returns to **exactly how it works today** — manual resolution of the PROVISIONAL queue. Nothing is left half-done: each pass settles bets one at a time and commits as it goes, so stopping mid-stream just means the next bet waits for you instead of the worker.

No data cleanup needed, no half-settled state to unwind. If in doubt, flip it off and settle by hand — you lose nothing but the automation.

---

## 7. Explicitly out of scope / deferred (do NOT wait on these)

These are **not** part of live-proving and should not hold it up. They're named follow-ups for later:

- **Market-type precision** — the "one more authorised line" that would let the worker read win-vs-place directly from Betfair instead of inferring it, closing the narrow place-market corner in Section 4d. **Decision (S220): explicitly gated — must be done before Strategy 4 / place-market betting enters v3, but NOT needed for Strategy-1 (win-market) proving, since the corner cannot arise on win bets.** A separate, operator-authorised change when that trigger arrives.
- **Threshold calibration** — whether 2.5% is the right materiality cut-off. Leave as-is for proving; revisit only if the real data suggests it.
- **Free-bet-credit automation** — still manual by standing decision. The worker only *detects* uncredited free bets; it doesn't credit them.
- **Auto-re-settlement** — the post-settlement void detector only *flags*; it never re-opens or re-settles a bet. Out of scope.
- **Persisted settlement audit table / a read-only audit endpoint** — the log-line + manual-queue surface is what proving uses; a stored audit list is a later add.

---

## 8. Bet-safety framing (the one-paragraph summary)

Start with **low real exposure**. Switch the worker on, watch the **first real settlements** closely — especially the verification records, and hardest of all the `paid_full` ones. The worker is built to **park anything uncertain rather than overpay**, so the failure mode is "a bet you have to settle by hand," not "money paid out wrong" — with the single narrow place-market exception in Section 4d, which the `paid_full` records surface for you. If anything looks off, flip the flag off and you're back to manual, no harm done. Prove it across a real window, confirm nothing was silently overpaid, and it's done.

---

### One-page checklist (tear-off)

**Before:** live mode on · real pending bets · small exposure · watching · know the off-switch.
**Flip:** `BETHUB_SETTLEMENT_WORKER=on` in the live launcher → restart → confirm worker started.
**Watch:** clean bets self-settle · read every verification record (esp. `paid_full`) · parked bets hit the manual queue · nothing silently overpaid.
**Prove:** a real window with clean wins/losses/voids + ≥1 confirmed park + every `paid_full` checked + invariant held.
**Rollback:** `BETHUB_SETTLEMENT_WORKER=off` → restart → back to manual, harmless.
