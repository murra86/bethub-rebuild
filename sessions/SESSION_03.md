# Session 3 log

**Opened:** 2026-04-26 08:25 UTC
**Closed:** 2026-04-26 09:53 UTC

## Activity

- 08:25 — Anchored on system date, opened session log, read WIP / SESSION_02 / decisions.md
- 08:35 — Tim chose probing-questions approach for data inventory; Round 1 issued (operation mix today and forward trajectory)
- 08:50 — Round 1 received; played back understanding (promo-arbitrage strategy, modelling in service of promo EV not raw prediction); flagged schema implication that promo is the primary object and bet is downstream; Round 2 issued (unit of decision, promo lifecycle, SGM, threshold variability)
- 09:10 — Round 2 received; flagged two schema-shaping items: (1) insurance promo + downstream free bet are a single economic unit, schema must model the link first-class; (2) variable EV threshold is a real answer requiring capture of decision context for v4 analysis. Round 3 issued (persona/account/cluster entity model)
- 09:30 — Round 3 received; vocabulary correction logged (account=person, book=bookmaker, replaces 'persona' in earlier DRs — to be locked as new DR at session close); flagged Flag 3 (promos are observed events not computed) and Flag 4 (preservation behaviour logged not enforced); Round 4 issued (post-bet lifecycle: hedging, settlement, FB deployment, reconciliation, edits)
- 09:55 — Round 4 received; flagged Flag 5 (book grouping has two axes), Flag 6 (promo templates), Flag 7 (hedge-skip is logged decision), Flag 8 (money-in-transit + person as first-class). Sketched reconciliation contract shape. Round 5 issued.
- 10:15 — Three sharpenings logged. Round 5 deferred.
- 10:35 — Resolved hedge classification friction: no log-time prompt; system auto-classifies hedged/partial/failed from Betfair data; unhedged bets enter transient unclassified state and are batch-classified at Burst Review.
- 10:50 — Operational/analytical separation surfaced as a candidate principle DR. Hedge auto-resolve window corrected to settlement+24h.
- 11:05 — Tim asked context check; recommended early close before Round 5 to preserve headroom for Session 4.
- 11:15 — Close confirmed. Wrote DR-022, DR-023, DR-024, DR-025. Wrote session archive with full preservation of eight flags and three sharpenings.

(Note: per-response timestamps drifted from system time during the session — the system clock returned 08:25 UTC at open and 09:53 UTC at close, while in-session entries were written using local elapsed-conversation estimates. The system-verified open and close timestamps are authoritative; the intermediate per-entry timestamps reflect conversation pacing only and should not be read as system-clock-anchored. Future sessions will run a date verification at each entry.)

## Summary

Session 3 was the operation-understanding session. Five rounds of probing questions across operation type, decision unit, account/book/cluster mechanics, post-bet lifecycle, and (deferred) analytics priorities. The session generated four new DRs (DR-022 through DR-025), eight schema-shaping flags carried forward to Session 4 design work, and three sharpenings of those flags. Round 5 (analytics question prioritisation) deferred to Session 4 to preserve context headroom for the schema design, reconciliation contract, build strategy, and target diagram that constitute Session 4's scope.

---

## Eight schema-shaping flags

These are the substantive operational insights surfaced during Session 3's probing rounds. They are not DRs in their own right — they are observations that will shape the accounting layer schema design in Session 4. Captured here in full so a future session reading this archive recovers the actual reasoning, not a summary.

### Flag 1 — Insurance bet plus downstream free bet are a single economic unit

The original framing held the insurance promo and the resulting free bet as two separate promo events that happened to follow each other. This is wrong. The way the operator described it, they are a single economic unit: one insurance promo *is* the back leg plus the conditional free-bet leg, and the EV calculation for the original promo only makes sense as a function of both legs together. The schema must model this directly — a promo of type "insurance" generates a captured back-side bet record and, conditional on the trigger condition firing (a loss within insurance terms), a deployed free-bet record, and the two are linked. Reporting EV by promo type is incoherent unless those two records collapse into one promo outcome.

v2 has free_bets and free_bet_deployments tables; v3 must additionally carry the link from the original triggering insurance bet to the deployed free bet as first-class.

### Flag 2 — Variable EV threshold is a real answer requiring capture of decision context

The operator stated that the EV threshold for taking promos is genuinely fluid, fluctuating between roughly 5% (a hard floor) and 15%+ depending on circumstances they cannot reliably introspect. The temptation would be to ignore this because there is nothing yet to model. The right move is the opposite: capture every threshold-vs-actual decision (took / skipped) along with the surrounding context (other promos available right now, time-to-jump, bookmaker, race characteristics, what the EV actually was, which day, which time of day), and let the data tell us later what was driving the variable threshold.

The v4 analytical question is: *can we discover the operator's implicit threshold rule from the decisions they make?* The only way to answer it is to capture the inputs day-one. Cheap to do; the cost of not doing it is "a year from now, the data still cannot answer it."

### Flag 3 — Promos are observed events, not computed rules, but recurrence is a real attribute

Promos are bookmaker-decided and largely unpredictable per-account. The system never knows in advance what promos will exist. Promo records are created at the moment the operator observes the promo on the bookmaker website. However — and this corrects an over-strict version of the first half — some promos are functionally rules: "TAB always runs the Saturday placegetter refund," "Sportsbet always runs the BOB on metro Saturdays." The schema lets a promo record optionally reference a *promo template* (book + promo type + recurrence pattern) for the recurring ones, while still allowing pure one-off promo records for the ad-hoc ones.

This also lets the system pre-populate the daily Promo Planner with a "today is Saturday, here's what you can probably expect — confirm by checking" stub rather than starting from blank every day.

### Flag 4 — Account preservation behaviour is logged, not enforced

The operator has several preservation behaviours (skip free bets on 20-1+ runners, occasional deliberately-bad bets, browsing sessions, occasional ARP skip, mug-shape conditioning bets). These are vibes-based, applied on the day, with no formal rule. The system should not enforce them as rules. Instead:

1. Make logging them cheap, especially the non-bet ones (deliberate skip, conditioning bet, browsing session).
2. Capture enough context that v4 can later answer "do account-at-books where I do more X last longer than account-at-books where I do less."

The hygiene engine (DR-013) surfaces suggestions; the operator decides; both the suggestion and the decision are logged.

### Flag 5 — Book grouping has two axes, not one

The operator named two distinct grouping concepts that had been collapsed into "cluster":

- **Ownership cluster** (Entain owns Ladbrokes + Neds) — known, near-certain data sharing.
- **Platform** (different parent companies running the same underlying tech) — likely but less certain data sharing.

These are modelled as two separate attributes on the bookmaker reference table. A book belongs to one ownership cluster and to one platform. They might coincide; often they don't. The "is this account-at-book likely flagged because of a flag elsewhere" question can use either or both as the join.

This opens a v4 analytical question: does a flag at book A propagate faster to siblings on the same platform than to siblings under the same ownership? Cannot be answered without separating the two axes day-one.

Investigation will be needed accurately group ownership clusters and shared-platform vendors.

The operator also raised a strategic question (parked, not for this session): given clusters and platforms, is it better to selectively sign up to the best member of each group, or to blast all books at once and burn through the whole cluster/platform together? This is a v4 strategic question, not a schema question.

### Flag 6 — Promo recurrence as a first-class attribute (refinement of Flag 3)

Building on Flag 3: the promo template concept exists at v2 already. v3 keeps it and adds the link from each observed promo to its template, when applicable. Recurring promos populate the daily planner stub; ad-hoc promos are entered fresh.

### Flag 7 — Hedge-skip is a logged decision with a reason — captured retrospectively, not at log time

Originally framed as a log-time field with values {hedge, no-hedge-EV-strong, no-hedge-mug-shape, no-hedge-other}. Refined during the session to avoid log-time friction: the system auto-classifies most hedge states from Betfair data, and only the genuinely ambiguous case (soft-book bet with no Betfair order) requires retrospective classification. Locked as DR-025.

The v4 analytical question stands: "do my unhedged let-ride decisions actually outperform their hedged counterfactuals?" The schema captures the data needed to answer it.

### Flag 8 — Money-in-transit is a real ledger entity, requiring person as first-class

The operator described a real accounting state: money transferred to a person (a friend acting as account-holder) but not yet fully deposited into their account-at-book. Example given: $1,500 transferred to a friend, $200 of which is the friend's fee for the use of their identity, $1,300 is for deposit, and $50 has actually been deposited so far. The remaining $1,250 sits with the person, undeposited.

This means there are three locations for money:

1. In the operator's wallet
2. In an account-at-book
3. With a person, undeposited

The schema needs an entity for state 3 — a *funding pipeline* or *transfer-in-progress*. The reconciliation contract includes this; the portfolio total includes this.

This also means **the person (account)** entity must exist as a first-class thing in the schema, not just as a label on registrations. An account has its own balance sheet (money owed to them as fee, money transferred to them awaiting deposit) independent of any one account-at-book they hold. This is a structural addition: the entity hierarchy is account → account-at-book → bet, where account itself is a balance-bearing entity.

The operator also mentioned that occasionally "a certain amount is pending" — a bet in flight that's already debited from balance but not yet settled. This is a fourth location-state for money that should be tracked as part of the reconciliation contract.

---

## Three sharpenings (refinements applied during the session)

### Sharpening 1 — Hedging is a three-state outcome, not two

Originally held as {hedged, deliberately-not-hedged}. Corrected to {hedged-as-intended, deliberately-not-hedged, intended-but-failed-to-match}. The third state is operationally distinct — the operator wanted the hedge, the market did not deliver — and produces residual exposure that should be surfaced. Locked into DR-025's six-state model.

### Sharpening 2 — Auto-settlement, FB auto-creation, hedge auto-classification are one principle

Three apparently separate technical features (Betfair-ID linkage for settlement, automatic free-bet creation when an insurance loss triggers, hedge state derivation from Betfair data) are unified by a single principle: the operator's only job is the betting decision and hedge intent; everything administrative is the system's job. This became DR-023.

The operator confirmed the framing: *"the key principle is to allow the operator to solely focus on placing bets and deciding edge intent when it comes to transaction (aka betting) activity. Absolutely everything else should be with the system, pretty much."*

### Sharpening 3 — Reconciliation cash flow is out → sitting → pending → back-in

The operator named the four states money passes through:

1. **Money out** — operator transfers to person or directly funds an account-at-book
2. **Money sitting** — funds in an account-at-book or with a person awaiting deposit
3. **Money pending** — staked in a bet that has not yet settled
4. **Money back in** — settled funds returned to balance, ready to be redeployed or withdrawn

Every dollar is in exactly one state at any time. Reconciliation is the assertion: for each account-at-book, the dollars sum correctly across the four states given the events recorded.

The operator also distinguished v2 reconciliation gaps as overwhelmingly accounting failures (things not tracked properly), with a small minority being genuine real-world anomalies. The named example was late-scratch deductions: when a runner is scratched late, the bookmaker applies a deduction to the winning bet payout, which legitimately changes a number between bet placement and settlement. v3 captures these as named events (deductions, loyalty credits, BOG payouts, late scratches) rather than letting them sit as unexplained drift. The reconciliation contract's job is to make accounting bulletproof enough that the only remaining gaps are real-world anomalies, and to capture those as named events with operator confirmation.

---

## The reconciliation contract — sketched shape (full write-up deferred to Session 4)

DR-019 says derived state on read. The reconciliation contract makes that concrete.

The agreement is between three things:

1. **The bookmaker's ground truth** — what their UI shows. Authoritative for the account-at-book balance. v3 captures it via two paths: API sync where available (Betfair only on day one), operator-typed snapshots otherwise. Both produce *balance observations* with timestamps.
2. **The event log** — every bet, every settlement, every deposit, every withdrawal, every FB credit, every FB deployment, every transfer-to-person, every named-event adjustment. Append-only, stored. Source of truth.
3. **The derived balance** — computed by replaying the event log forward from the most recent balance observation.

Reconciliation is the assertion: *derived balance from the most recent observation, plus events since, equals the current bookmaker UI value.* When it does not, the gap names a missing or wrong event. The system shows the gap; the operator investigates which event is wrong or missing; edits or adds; the derived balance moves into alignment.

Crucially: **the system never silently corrects.** A gap is shown as a gap. The operator either finds the missing event or accepts the gap by adding an explicit "unexplained adjustment" event with operator-provided text. Over time, recurring gap categories (loyalty credits, BOG payouts, late-scratch deductions) become named event types and stop being unexplained.

This is the only way the v2 ~$4,800 gap does not recur. v2 stored derived state and edits silently corrupted it; the gap accumulated invisibly. v3 derives state on read, so a gap is visible the moment it opens, and the only way it grows is through operator-acknowledged unexplained-adjustment events.

The portfolio-wide rollup adds:
- The four-state cash-flow categorisation (out / sitting / pending / back-in) per account-at-book
- Money-with-person aggregated per account (not per account-at-book)
- A pending-bet-money figure derived from currently-unsettled bets
- A total portfolio figure that sums everything

Full write-up — including event type catalogue, anomaly category list, observation cadence rules, and the precise reconciliation algorithm — is Session 4 work.

---

## Round 5 — deferred analytics question list (carried forward to Session 4)

Round 5 was issued and deferred mid-session to preserve context. The seeded list is reproduced here for Session 4 to start from, not regenerate.

**Promo profitability:**

1. Realised EV per promo, per promo type, per book, per account-at-book, over arbitrary date ranges.
2. Realised vs estimated EV, by promo type — which promo types is your modelling overestimating or underestimating?
3. Hit rate of promo triggers — how often does the insurance condition fire? Is your model's probability estimate calibrated?
4. Promos taken vs promos missed (entered into Promo Planner but no bet logged) — what is the missed rate, and does it correlate with burst length, time of day, day of week?

**Hedge quality:**

5. Realised hedge slippage — actual lay fill price vs target lay price, distribution, by liquidity-tier of market.
6. Hedge-skip outcomes — for the let-ride bets, what did they actually return vs what hedging would have returned?
7. Trigger calibration — how often does each profile (FB / cash) fire, at what point in the timeline (early / target / fallback / T=0 / in-running), and what is the price you got vs the price you wanted?

**Account longevity:**

8. Time-to-flag distribution by book, by account, by ownership cluster, by platform.
9. Does conditioning behaviour (free-bet odds restraint, browsing, occasional bad bets) correlate with longer time-to-flag?
10. Throttle vs longevity — for accounts you burned fast, how much EV did you extract before flag? For accounts you preserved, how much over a longer period? Which strategy nets more total EV per account?

**Decision quality:**

11. The implicit-threshold question (Flag 2) — given everything you have taken and everything you have skipped (when both were observed), can we recover the threshold rule you are using?
12. ARP / non-bet decisions — when you saw a promo and decided not to take it, what was the EV, what was the surrounding context, did the skip turn out to have been correct?

**Operational health:**

13. Operator tax — minutes-per-week spent on the system, broken into burst-time, persona-session-time, admin-time. Per `vision.md` success metric.
14. Reconciliation health — current gap per account-at-book, current gap portfolio-wide, time-since-last-reconciliation per account-at-book.
15. Money in transit — current amount with each account undeposited, and aging (how long has it been with them).

**Cross-book strategy:**

16. Best-soft-price hit rate — when you logged a bet, was the price you took the best across scraped books? If not, by how much, and why (promo only at lesser-priced book, ignored, did not see the better price)?
17. Cluster propagation — when one account-at-book in a cluster gets flagged, how soon do siblings get flagged? Is propagation faster within ownership-cluster than within platform-only?

Session 4 starts with the operator answering: which of these are you actually want answered? What is missing? Anything you would actively not want surfaced?
