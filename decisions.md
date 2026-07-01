# Decisions

Every architectural decision, numbered, append-only.

**Format:** `DR-NNN: One-line summary. Why: reason. Tradeoff: what we gave up. Date: YYYY-MM-DD.`

Past decisions are not edited. To reverse a decision, add a new entry that supersedes it.

---

## DR-001: Rebuild BetHub from the ground up rather than continuing to extend v2

**Why:** v2 has reached the point where the cost of changing it exceeds the cost of building it. Sessions take longer (close-out at 20 min), bug fixes touch many surfaces (today's BW Cash UX touched 6 files), reconciliation is broken (§A27 \~$4,800 ledger gap), and the planned v3 features (profile switching, liquidity analytics, soft book scanning) cannot be cleanly added on top of v2's coupling.

**Tradeoff:** Significant up-front planning and rebuild effort (estimated 4–6 weeks of build sessions) before any new features ship. v2 keeps running daily during the rebuild to preserve income.

**Date:** 2026-04-25

---

## DR-002: v3 separates into three layers (operational, execution, accounting) with strict boundaries

**Why:** v2 mixes all three concerns in every page — a UX change to a promo cap field touches the schema. In v3, each layer has one job and a defined interface to the others. This means future changes only touch one layer; new features (profile switching, liquidity analytics) become new tools that talk to the system through the interface, not bolted-on features.

- Operational layer = daily/weekly cadence (profile switching, AccountCare, promo allocation)
- Execution layer = per-bet cadence (logging, hedging, EV, live odds)
- Accounting layer = background (ledger, reports)

**Tradeoff:** More upfront design effort. Some short-term inefficiency where the same data crosses layer boundaries instead of being shared in memory.

**Date:** 2026-04-25

---

## DR-003: v3 governance is six files, no anomaly log, no patch log, no separate conventions doc

**Why:** v2's governance grew reactively into a 1500-line context_index.md plus 90+ session handoffs plus STATUS, system_snapshot, and [CLAUDE.md](http://CLAUDE.md). Closing a session takes 20 minutes of doc maintenance, and session open requires reading 4–5 files. The fix is to constrain governance to its actual jobs: prevent re-litigating settled work, keep the system honest, and let Claude load context efficiently.

The six files are: README, vision, architecture, decisions, work_in_progress, and sessions/. Diagrams live as separate picture files in `diagrams/`. Anomalies become decisions ("we accept X because Y"). Conventions become decisions ("we always do X"). Patches are tracked in git history and one-line session summaries.

**Tradeoff:** Less historical detail captured. Older sessions are summarised, not transcribed. If we need to reconstruct a specific past patch we may need to consult git history.

**Date:** 2026-04-25

---

## DR-004: Session open requires reading only `work_in_progress.md`; Claude loads other files only when scope demands

**Why:** v2's session open required reading 4–5 files (system_snapshot, [CLAUDE.md](http://CLAUDE.md) priorities, latest handoff, §A) before any work could start. This burned 20% of context every session. v3 puts current state in one short file (`work_in_progress.md`), and Claude pulls in `decisions.md`, `architecture.md`, or specific diagrams only when the session's scope makes them relevant.

**Tradeoff:** Operator gives up upfront orientation for less reading. Claude becomes more responsible for asking clarifying questions in-session if it needs context it has not loaded.

**Date:** 2026-04-25

---

## DR-005: Architectural diagrams live as separate picture files in `diagrams/`, referenced from `architecture.md`

**Why:** Diagrams take significant vertical space in markdown documents and make [architecture.md](http://architecture.md) visually heavy. Separating them keeps the architecture doc skimmable, lets diagrams open at full size, and lets either operator or Claude pull a specific diagram into a chat session by referencing its filename.

**Tradeoff:** When you want both architecture text and the matching diagram, you open two things instead of one.

**Date:** 2026-04-25

---

## DR-006: Operations log is a first-class part of the architecture from day one

**Why:** Measuring what works for hygiene, promo allocation, and account longevity requires accumulated data. Without an append-only log of every operational action (hygiene round, promo taken, restriction event, profile switch, deposit, withdrawal), these questions cannot be answered later. The cost to add it day one is small; the cost to retrofit it after a year of operation is large.

**Tradeoff:** Adds one storage concern to the architecture from the start. Disciplined logging required from the operator.

**Date:** 2026-04-25

---

## DR-007: Vocabulary lock — definitions for "concern", "decision", "principle", and "metric"

**Why:** Session 2 surfaced a drift problem: terms used in Session 1 (specifically "functional concern") were being silently redefined in Session 2, leading to attempts to renumber and restructure prior work. The fix is to lock definitions in writing so they cannot drift. If a case arises that does not fit, a new term is added explicitly via a new decision record — not by silently mutating an existing one.

**Definitions:**

- **Concern** — a piece of functionality the system either does or should do. Phrased as a capability ("hedging on Betfair", "promo allocation"). Concerns get triaged into v3-day-one / v4 / killed. Concerns are the unit of scope.

- **Decision** — an architectural or governance choice that constrains how concerns get built. Phrased as a stance ("v3 separates into three layers", "session open reads only one file"). Decisions live in this file, are numbered, and are append-only.

- **Principle** — a rule that governs a class of decisions across the system. Phrased as a heuristic ("show only what Betfair native cannot", "single source of truth per number"). Principles are written as decisions and referenced when relevant decisions invoke them.

- **Metric** — a measurable quantity used to evaluate whether the system is working. Phrased as a number with a target ("operator tax in minutes per week", "reconciliation gap in dollars"). Metrics live in `vision.md` under success criteria, not in the concern list.

**How this resolves Session 2's friction:**

Items in the Session 1 concern list that turn out to be principles or metrics are not removed from the list — they are triaged with the outcome "lift to [decisions.md](http://decisions.md) as a principle" or "lift to [vision.md](http://vision.md) as a metric". The list of 15 stays the list of 15. The triage names where each one actually belongs.

**Tradeoff:** Slight rigidity. If a future concern genuinely does not fit any of these four categories, a new term must be defined explicitly with a new DR rather than fudged into an existing one.

**Date:** 2026-04-25

---

## DR-008: Principle — "Show only what Betfair native cannot; otherwise open in Betfair"

**Status:** Principle (per DR-007). Governs all execution-layer decisions involving Betfair data or interaction.

**Why:** Betfair's own UI is mature, fast, and authoritative for everything it does well — order books, market depth, live price ladders, account history, settled markets. Reproducing those surfaces inside our system is expensive to build, expensive to maintain, always slightly behind Betfair, and adds nothing the operator does not already get by opening Betfair directly. The only views worth building inside our system are the ones Betfair cannot or does not show: cross-account context, our own promotional EV alongside Betfair prices, fair-price indicators that combine our data with theirs, hedge planning that knows about our exposure on the back side.

**How this applies:**

When designing any execution-layer feature that involves Betfair, the test is: *does this view combine our data with Betfair data in a way Betfair cannot show natively?* If yes, build it. If no, the system links to Betfair and the operator opens it there.

**Concrete consequences for v3:**

- Hedge placement UI shows our back stake, our liability, our promo context, and a fair-price indicator (geometric midpoint, liquidity-weighted) alongside the Betfair price. That is information Betfair does not have, so we build it.
- We do not build a market depth ladder, a price history chart, or a settled-market browser. Those are Betfair's job. Our system links to the relevant Betfair page.
- We do not mirror Betfair account state in our UI. We pull balance via API for reconciliation; we do not display a Betfair "wallet view".

**Tradeoff:** Operator does some context-switching between our system and Betfair native. We accept this — the alternative is rebuilding Betfair's UI badly and maintaining it forever.

**Date:** 2026-04-25

---

## DR-009: Triage of the 15 concerns from Session 1

**Why:** Session 1 named 15 functional concerns (8 things v2 does today, 6 gaps that force manual work, 1 meta-concern). Session 2 triaged them against the four jobs from `vision.md`, with v3-day-one reserved for concerns serving Job 1 (run the operation) or Job 2 (capture data accurately). Concerns serving only Job 3 (surface decisions) or Job 4 (measure what works) default to v4 unless there is a specific reason to bring them forward.

This decision locks the triage outcome. Future sessions do not re-litigate whether a concern is in scope; they implement what is in scope and defer the rest.

**v3 day one (11 concerns):**

 1. **Bet logging** — execution layer. The spine; everything else hangs off accurate bet records.
 2. **Hedging on Betfair** — execution layer. Half of how promotional EV is realised.
 3. **Promo engine** — split: EV calculations in execution layer, FB ledger and settlement in accounting layer.
 4. **Account ledger** — accounting layer. Reconciliation backbone; v2's \~$4,800 ledger gap is the case study for why this needs a clean rebuild.
 5. **AccountCare** — operational layer. Job 1 directly; conditioning protocols and cluster awareness are how accounts stay alive.
 6. **Monitoring & alerts (minimal)** — operational layer. Action queue and DISC warnings only. The "Daily Intelligence Layer" surface from v2's roadmap is v4.
 7. **Live odds & race data** — execution layer. Required to log bets and price hedges in real time. VPS scraper infrastructure carries over largely intact.
 8. **Profile & network switching** — operational layer. Job 1's binding constraint per `vision.md`; the highest-value gap in v2.
 9. **Promo allocation (slot tracking + logging only)** — operational layer. Day-one scope: per-account slot accounting plus complete logging of every allocation decision. Allocation *logic* (aggressive vs conservative throttle, EV × longevity decision) is v4. Operator continues to allocate in their head day one — but every decision is logged for future analysis.
10. **Flexible Betfair hedging** — execution layer. Limit orders at custom prices plus fair-price indicator (geometric midpoint, liquidity-weighted). Real money lost today on suboptimal hedge prices, so it earns day one. 13a. **Soft book scanning (unified lookup over already-scraped books)** — execution layer. Cheap to build because the data already exists from VPS scrapers (Entain, PointsBet, Unibet, PlayUp, Sportsbet via Racing API, TABtouch, plus TAB API when registered). Surfaces "best soft price right now" alongside Betfair odds at bet-logging time.
11. **Operations log** — accounting layer. Per DR-006, append-only journal of every operational action.

**v4 (3 concerns / partial concerns):**

7. **Reporting & analytics surface** — accounting layer when built. Critical caveat: the *data capture* for analytics is v3 day one. Schemas, log fields, granularity, and what gets recorded for every bet, cycle, promo, hygiene action, and allocation decision must be designed in from day one. The analytics *surface* (charts, reports, queries) is built when there is accumulated v3 data to analyse. Wrong schemas on day one means a year of data that cannot be used. This will drive an explicit data inventory step during accounting layer design. 10b. **Promo allocation logic** — operational layer when built. The throttle (aggressive vs conservative), the EV × longevity decision, the per-book longevity model. Built once a year of v3 operations log data exists to inform it. 13b. **New scrapers for currently-blocked books** — execution layer when built. BetRight, Betr, PalmerBet, Dabble (Cloudflare-blocked, need headless browser solutions). Defer until live betting under v3 reveals which one is highest-value to crack first.

**Lifted out of the concern list (2 concerns):**

12. **Smart Betfair view** — lifted to DR-008 as a principle. Triage outcome: not a feature to build, a rule to apply when designing execution-layer features that touch Betfair.
13. **Operator tax** — lifted to `vision.md` as a success metric. Triage outcome: not a feature to build, a measurable target the system is judged against. Already named in `vision.md`; a numeric target gets added during success criteria design.

**Tradeoff:** v4 list is non-trivial. The operator runs day one without analytics surfaces, without sophisticated allocation logic, and without coverage of Cloudflare-blocked books. This is acceptable because (a) the operator already runs without these in v2 and earns income, (b) the v3 day-one set fixes the things actively costing money or capping income (profile switching, hedge prices, ledger reconciliation), and (c) v4 features get built on better foundations and informed by real v3 data.

**Date:** 2026-04-25

---

## DR-010: Two-mode session model — bursts and persona sessions

**Why:** Session 2 surfaced that the operator runs in two distinct modes with nearly opposite UI requirements. A single "session" concept would have served one mode badly and the other not at all.

**Mode 1: Burst.** An unplanned span of opportunistic operating time, triggered by available promos. Can last 20 minutes (a casual Tuesday afternoon) or 6+ hours (a Saturday spring carnival day) — duration is not a defining characteristic. Within a burst, the operator switches rapidly between personas/accounts/books to take time-sensitive promos before race jumps. A bet during a burst belongs to a momentary persona context (which persona was active at the keystroke) and to the current race window.

**Mode 2: Persona session.** An explicit, planned span of time spent operating as a single persona for non-time-critical work — conditioning bets, browser activity, account upkeep. Profile/MiFi/AdsPower stay locked to one persona for the duration. Switching mid-session would defeat the conditioning purpose.

**Terminology lock (per DR-007 vocabulary discipline):**

- **Burst** — opportunistic, multi-persona, time-driven by external race windows. Stays live until the operator explicitly ends it. Inactivity within a burst is normal and is not auto-ended.
- **Race window** — a sub-unit within a burst representing a specific race the operator is currently working. Multiple race windows occur within one burst.
- **Persona session** — single-persona, planned, ended explicitly. No race-window concept.

The two modes cannot run simultaneously. Moving between them is one explicit action and is friction-free.

**Hierarchy:**

```
Burst
  └── Race window
        └── Bet

Persona session
  └── Bet (no race window)
```

A bet always belongs to exactly one of {burst+race window, persona session}. The accounting layer's bet schema will have nullable foreign keys to both; exactly one is populated.

**Why this matters for measurement:** burst-mode and persona-session-mode answer different analytical questions later. Bursts answer "EV per minute," "promos missed per race," "burst duration vs error rate." Persona sessions answer "hours of conditioning per account per month," "conditioning vs restriction outcomes." Forcing them into one concept would have blurred both.

**Tradeoff:** Two session types means two code paths in the session controller and two sets of UI affordances. Acceptable cost for analytical clarity and matching operator reality.

**Date:** 2026-04-25

---

## DR-011: Promo Planner is v3 day-one in the operational layer

**Status:** Scope addition beyond DR-009's original triage. Explicitly noted: DR-009 listed "promo allocation (slot tracking + logging)" as concern 10's day-one scope; DR-011 expands that to include a structured Promo Planner. This is recognised as a scope expansion and the v3 day-one count moves from 11 to 12 items.

**Why:** A multi-hour burst across many books and races is a scheduling problem the operator cannot solve in real time without support. With \~30 accounts across multiple personas and multiple books each potentially running promos on multiple races, the combinatorial space exceeds what can be routed optimally by mental tracking alone. The result without a planner is missed promos — high-EV opportunities that the operator simply did not get to before the race jumped. This is unmeasured EV loss in v2 and is exactly the kind of thing v3 should fix.

**What the planner does:**

- **Promo board** — operator-populated list of today's available promos. Each entry: book, race, promo type, expected EV. Operator enters as they spot promos throughout the day (or pre-race-day for big meetings). Entry must be fast — a few seconds per promo, not a multi-field form.
- **Race window scheduler** — given the promo board and your account/persona inventory, derives "for race X, these personas can take these promos on these books" automatically. The operator does not assign personas to promos manually — it is computed from account holdings and cluster state from AccountCare.
- **Action surfacing** — when a race window opens, the action queue surfaces the planned promos for that race, ordered by EV, with the persona/account context pre-loaded so executing is one keystroke.
- **Outcome resolution** — at race jump (or window close), each planned promo resolves automatically to taken (a bet was logged against it) or missed (no bet was logged). No manual reason entry.

**Manual input minimised to one thing:** entering promos to the board as the operator spots them. Everything else (persona assignment, scheduling, outcome resolution) is computed or automatic.

**Why no skip-reason capture:** considered and rejected. Marginal analytical value of "why skipped" over "skipped" does not justify the mid-burst manual cost. If skip patterns matter later, they are inferred from the data already captured.

**Tradeoff:** Adds a new component to the operational layer and a corresponding UI surface. Operator must adopt the discipline of entering promos as they spot them — but this is largely formalising work the operator is already doing mentally.

**Date:** 2026-04-25

---

## DR-012: Keyboard-first interaction model for the execution-layer hot path

**Status:** Principle (per DR-007). Governs UI design for any operator action that occurs inside a burst.

**Why:** The most-used interactions in v3 — switching personas mid-burst, logging bets, opening hedge modals, navigating between race windows — happen under time pressure during burst mode. Mouse-driven UI introduces friction measured in seconds-per-action; over a 6-hour burst with hundreds of actions, that friction compounds into missed promos. Keyboard shortcuts driven by a programmable keyboard (operator has a Keychron Q6 Max, QMK/VIA-capable) collapse multi-step actions into single keystrokes.

**Hot-path actions that must be keyboard-driven:**

- Switch to next persona within current race window
- Log bet (opens logger pre-populated with current persona / account / race / time)
- Open hedge modal for last-logged bet
- Mark current planned promo as taken / move to next planned promo
- Switch race window
- Start burst / end burst

**Cold-path actions stay mouse/UI-driven:**

- Configuring AccountCare protocols
- Adjusting hygiene budgets
- Reviewing reports
- Settings, account onboarding, etc.

**Implementation note (not a decision, just a planning marker):** keyboard shortcut configuration on the Q6 Max will be specified during execution-layer design and the operator will be hand-held through QMK/VIA configuration at build time. The system itself listens for the keystrokes (browser-level or app-level depending on technology choice in build strategy) — the keyboard just sends them.

**Tradeoff:** Operator must learn a small set of shortcuts. Acceptable: the shortcuts replace actions the operator already performs constantly, just slower.

**Date:** 2026-04-25

---

## DR-013: Hygiene engine structure — persona profile, bookmaker rules, account state

**Why:** The operational layer's hygiene budget engine needs to produce weekly plans that drive both betting activity (per-account, per-bookmaker) and browsing/lifestyle activity (per-persona). v2 has tier-aware phase logic but does not output concrete plans, and has no persona-level conditioning concept at all. v3 makes both explicit, structured around three data sources combined by a single engine.

**The three data sources:**

- **Persona profile** — one record per persona (Tim, Kate, Sarie, etc.). Defines who the persona *is*: name, age, location, interests, news preferences, hobbies, plausible betting topics, plausible browsing patterns. Largely stable; updated occasionally. Day-one schema kept minimal — roughly 5–10 fields per persona, biased toward free-text tags rather than rigid categorisation. Expands only if proven useful in v3.

- **Bookmaker hygiene rules** — one record per bookmaker. Defines what the bookmaker requires for account longevity at each tier: target weekly turnover, preferred odds bands, frequency expectations, restriction triggers known from operator experience. Bookmaker-specific knowledge, not persona-specific. Populating this table is a substantial knowledge-capture task tracked separately in `work_in_progress.md`.

- **Account state** — the join row. Per (persona × bookmaker) combination: current tier, current phase, last-bet date, week-to-date turnover, current restrictions, cluster membership. Updated from operations log and accounting layer in real time.

**What the engine produces:**

A weekly plan per persona, with two sections:

1. **Per-account betting actions** — derived from bookmaker rules + account state, flavoured by persona profile. Output format: "PointsBet-Sarie needs 2 bets in 1.8–3.5 band, \~$180 total turnover, by Friday. Plausible events given Sarie's profile: AFL, NRL, harness." The engine outputs the *constraint and the flavour*, not the specific bet. The operator chooses the actual bet within those parameters.

2. **Per-persona browsing actions** — derived from persona profile alone. Output format: "Sarie's recommended browsing this week: ABC news 5 min, BOM check, one cooking-related search. Total \~10 min." Surfaced to the action queue when the operator is in a persona session for Sarie.

**Browsing actions are suggestions, not mandates.** The system does not require the operator to mark them done. If marked done, operations log captures the completion timestamp; this gives v4 the data to ask "do accounts in personas with high browsing-task completion condition better than personas with low completion?" If skipped, no friction.

**Persona profile as connective tissue:** the same profile that drives browsing actions also flavours the betting actions. If Sarie's profile says "casual punter, follows AFL, lives in Adelaide," the engine biases her betting recommendations toward AFL events at modest stakes — not because the bookmaker rules require it but because that is what Sarie would plausibly bet on. The operator retains final say over each bet; the profile only shapes the suggestions.

**Tradeoff:** Three data sources is more upfront modelling than v2 has, and the bookmaker rules table requires a separate knowledge-capture task before the engine can produce useful output. Acceptable because the alternative (per-account-only with no persona concept) cannot produce coherent conditioning across the full set of accounts a persona holds, and would block any future analytical question that asks "does conditioning work."

**Date:** 2026-04-25

---

## DR-014: Soft-book price context in the burst-mode action queue

**Why:** Inside a burst, the operator needs to see soft-book pricing alongside planned promo actions without context-switching to bookmaker websites. The data already exists in v2's scraper infrastructure (concern 13a per DR-009); the question is how the operational layer surfaces it during decision-making. Two surfacing options were considered — top scraped price always vs only when a promo is on a scraped book — and both have value. Layering them is the answer.

**The rule:**

The action queue's burst view shows two pieces of soft-book context per planned action, layered:

1. **Always-on: best scraped price.** For every race window and every planned promo, the system displays the best price currently available across scraped soft books (Entain, PointsBet, Unibet, PlayUp, Sportsbet via Racing API, TABtouch, plus TAB API when registered). Acts as a price reference point regardless of promo status. Cheap to compute given the scraping infrastructure already exists.

2. **Conditional: promo-on-soft-book highlight.** When one of the scraped books is currently running a promo on the race in question and that book also has a competitive price, the system surfaces this prominently — a visual prompt that says "this scraped book has both an active promo and a strong price right now." Higher EV signal than either alone.

Both signals appear in the same UI surface but with different visual weight. The conditional highlight is a layer on top of the always-on display, not a replacement for it.

**Layer ownership:**

- **Execution layer** owns the data, the comparison logic, and the promo-on-book detection. It is the source of truth for "what is the best soft price right now and is there a promo on it."
- **Operational layer** consumes that information through a defined interface and renders it in the action queue UI alongside planned-promo, persona, and AccountCare context.

This is a concrete instance of the layer boundary defined in DR-002. The operational layer never queries scrapers directly; it asks the execution layer for current pricing context.

**Deferred to execution-layer design:**

- How the price comparison is computed (refresh cadence, staleness handling, fallback when scrapers fail)
- Which books are in the comparison set on day one
- How promo-on-book status is detected (operator-flagged in the Promo Planner vs auto-detected from scraped data)

**Tradeoff:** Adds a permanent execution-layer dependency to the burst-mode action queue UI. If scrapers are down, the always-on context degrades gracefully (shows "no scraped data available"). The planned-promo action queue still works; only the soft-price overlay disappears.

**Date:** 2026-04-25

---

## DR-015: Three-tier AccountCare alert severity (red / amber / yellow)

**Why:** AccountCare flags need to surface during bursts without blocking the operator's flow. A binary "alert / no alert" cannot distinguish "this account is about to be permanently banned" from "this account's weekly turnover is slightly below target." The operator needs to see the severity at a glance and decide whether to act now or finish the current race window first.

**Three categories — definitions locked, thresholds deferred:**

- **Red — interrupt-worthy.** Account is at imminent risk of permanent loss or regulatory consequence. Examples (illustrative, not exhaustive): impending ban based on activity pattern, missed cooling-off period that triggers cluster-wide flag, regulatory issue requiring action. Surfaces visually impossible-to-miss in the action queue even mid-race-window. Does not block flow (per operator's explicit direction — nothing blocks). Operator chooses whether to act now or finish current race window.

- **Amber — visible but secondary.** Meaningful operational concern that affects the next bet decision on the affected account. Examples: account is one bet away from a tier downgrade, three consecutive losses on a cluster-watched book, conditioning gap that affects the planned bet. Surfaces on the persona/account row when that account is lined up for action. Does not interrupt other persona/account decisions.

- **Yellow — informational.** A flag worth knowing about over the day but not affecting any specific upcoming decision. Examples: persona's overall weekly turnover trailing target, account inactive for N days, scheduled hygiene round overdue. Surfaces in the action queue's secondary panel, not in the primary in-flow display.

**What is locked:** the three categories, their interrupt/visibility behaviour in the action queue, and the principle that nothing blocks operator flow.

**What is deferred:** the specific thresholds and rules that determine which category any given AccountCare condition falls into. These are operational knowledge filled in when the AccountCare data model is designed in detail. Tracked as a known follow-up; not blocking the architecture decision.

**Tradeoff:** Three categories means the AccountCare data model must include a severity classification per condition type, and that classification must be maintained as the operator learns which conditions are truly critical vs noise. Acceptable: the alternative (binary alerts) produces either constant interruption or missed critical events, both of which are worse.

**Date:** 2026-04-25

---

## DR-016: Hedge trigger model — two profiles, persist-after-jump universal, stake recalculation at fire time

**Why:** Hedge triggers have asymmetric downside between free bets and cash bets. An unmatched free bet hedge has small downside (the back side runs as a free position); an unmatched cash hedge has large downside (real money runs unhedged). A single trigger model cannot serve both. Two profiles are needed, with thresholds calibrated to the asymmetry.

**Universal trigger properties (apply to all hedges):**

- **Persist-after-jump is on by default.** All lays placed by the system carry the persist-after-jump flag. There is no scenario where a hedge benefits from being cancelled at suspension; making it default removes a category of error. Override is possible but buried — not in the standard hedge UI.
- **Stake recalculation at trigger fire.** When a trigger fires at a price different from the original target, the lay stake is recalculated from the actual fill price using stored back-side parameters (back stake, back odds, promo type, desired hedge outcome). This keeps both legs balanced regardless of price drift. Universal — applies to both profiles.
- **Trigger time fallback at scheduled jump (T=0), not earlier.** Empirical observation: races do not jump early. A "minus N seconds" trigger only ever fires too soon. Trigger at T=0 if no other condition has fired; firming detection handles the period between scheduled and actual jump.

**Free bet profile (relaxed):**

- Primary trigger: "fire when conversion ≥ X%" (operator-set per hedge)
- Firming-based fallback threshold: high — wait for strong signals before firing
- T=0 fallback: fire at any available price if not yet matched
- Persistent order behaviour means in-running matching is acceptable; some unmatched free bets are tolerable

**Cash profile (strict):**

- Primary trigger: "fire when lay price ≤ X" (operator-set per hedge)
- Firming-based fallback threshold: low — fire on weaker signals to reduce unhedged risk
- T=0 fallback: mandatory fire at any available price
- Reasoning: unhedged cash carries directional risk much larger than the cost of accepting a slightly worse hedge price

**Threshold calibration is liquidity-relative, not absolute:**

Firming detection uses matched-volume rate-of-change as a percentage of total market volume, or as a multiple of rolling-average rate over the prior N minutes. A Wednesday country race ($50K total matched) and a Melbourne Cup race ($50M total matched) cannot share absolute thresholds. The exact formula is calibrated against captured liquidity data (per DR-020); structure is locked here, parameters are tuning work during build.

**Trigger outcome tracking (data capture, no UI day-one):**

For every trigger fired, the operations log captures: profile, target price set, time trigger fired, time match occurred (or unmatched), final fill price, pre-jump vs in-running classification. For every hedge that does not fully match by settlement, outcome is classified: matched at target, matched at degraded price, matched in-running, ran unhedged. This data is captured day-one with no analytical surface; v4 builds the surface to refine threshold calibration based on accumulated evidence.

**Tradeoff:** Two profiles plus threshold calibration is more complex than a single trigger model. Acceptable because the asymmetric downside between free bet and cash hedges cannot be served by one model without compromising both.

**Date:** 2026-04-26

---

## DR-017: Bet records fully editable, hedge modal as combined back+lay capture surface, inline validation warnings

**Why:** Bursts are frantic and errors are inevitable. v2's design treats edits as exceptional events requiring SQL patches and operator-Claude back-and-forth, which means errors compound until manually fixed (often 24-48 hours later). v3 must treat edits as routine and provide proactive validation to catch errors at log time rather than after.

This decision combines three related concerns into one architectural stance: edit semantics, the bet capture surface for promotional bets, and inline validation.

**Bet records are fully editable indefinitely:**

- Inline editing in the bet history view — click any field, change it, save. No special "edit mode."
- Multi-bet edits in a single after-burst cleanup session
- Every edit creates an operations log entry capturing what changed, when. Audit trail is automatic.
- No special permissions or warnings on edits — they are routine, not exceptional
- Reconciliation tolerance: edits affecting FB ledger or account balance are handled cleanly by the accounting layer without errors. This is a structural requirement on the accounting layer (depends on DR-019).

The 30-second undo concept previously considered is dropped. Errors are not noticed in 30 seconds — they are noticed during after-burst review hours later. Permanent inline editability fits how the operator actually works.

**Burst Review is a first-class workflow:**

After a burst (or any time), a Burst Review view shows all bets logged during the burst, ordered by time, with quick-edit on every field. Includes a "sanity check" pass that flags potential errors (multiple bets to same account in short window, stake outliers, etc.) for operator review.

**Hedge modal is a combined back+lay capture surface for promotional bets:**

For promotional bets that will be hedged on Betfair, the hedge modal becomes the primary capture surface. Two-path design:

- **Promotional + hedged path (most common in bursts):** open hedge modal → confirm/adjust auto-populated back-side info (race, runner, book, persona, stake, odds, promo type, all pre-populated from planned promo where possible) → set lay parameters and triggers → commit. The bet log entry is created automatically from the hedge modal data; no separate "log soft-book bet" step.

- **Ad-hoc or non-hedged path:** open bet logger directly → confirm/adjust auto-populated context → commit. No hedge modal involvement.

This solves the validation gap: previously the system did not see the back-side bet until after the hedge was already placed, making stake validation impossible. With back-side parameters captured in the hedge modal, the system can compute expected lay stake and validate the operator-entered lay stake before placing.

**Inline validation warnings (warnings, not blocks — per DR-015 nothing-blocks principle):**

Fired at log time when conditions are met:

- **Negative balance projection** — if logging this bet would take the account negative, warn (could be intentional in credit-extended scenarios but flagged)
- **Account-promo mismatch** — if the planned promo is on book X and operator selected book Y, warn
- **Persona-account mismatch** — if active persona is X and operator selected an account belonging to Y, warn
- **Unusual stake size** — if stake is &gt;2x typical for this account, confirm
- **Duplicate bet detection** — if a near-identical bet was logged in the last 60 seconds, warn
- **Hedge stake mismatch** — if entered lay stake differs from computed expected stake by &gt;5% given back-side parameters, warn

The Burst Review surfaces any warnings that were confirmed-through during the burst for retrospective recheck.

**Tradeoff:** Combined hedge-modal capture adds slight friction (operator confirms back-side parameters before placing lay) compared to v2's "just enter the lay." Acceptable: the friction is the same fields the operator would enter into the bet logger anyway, just front-loaded; and the validation it enables prevents a class of errors that have cost real money in v2.

**Date:** 2026-04-26

---

## DR-018: Execution layer scraper architecture supports incremental scraper addition

**Status:** Architectural principle, not a feature.

**Why:** Soft-book scraping coverage is a known gap. v3 day-one carries over v2's existing scrapers (Entain, PointsBet, Unibet, PlayUp, TABtouch, Sportsbet via Racing API). The high-value gaps named by the operator — Star Sports, BlueBet platform (HotBet, SwiftBet), and other Cloudflare-blocked books — remain unsourced day-one. These are deferred to v4 (concern 13b per DR-009) because building them is non-trivial (requires headless browser solutions, more maintenance overhead). However, the v3 architecture must not block their later addition.

**The principle:**

The execution layer's Live Odds Aggregator defines a clean per-book interface — a contract that says "given a race identifier, return prices for all runners with timestamps and source metadata." Each scraper implements this interface independently. Adding a new scraper is one new module conforming to the interface; the aggregator picks it up without code changes elsewhere.

**What this means concretely:**

- No bookmaker-specific logic in the aggregator itself
- No assumption that scrapers share storage, scheduling, or transport
- New scrapers can be HTTP-based (current pattern), headless-browser-based (Playwright/Puppeteer for Cloudflare-blocked books), API-based (TAB Studio when registered), or anything else — all conform to the same output contract
- Removing or pausing a scraper is a configuration change, not a code change

**Tradeoff:** Slightly more architectural discipline at build time (scrapers cannot take shortcuts that bypass the interface). Acceptable because the alternative — bookmaker-specific code paths in the aggregator — produces the same coupling problem v2 has elsewhere.

**Date:** 2026-04-26

---

## DR-019: Derived state computed on read, not stored

**Why:** v2's accounting layer stores computed state in multiple places (turnover totals, FB ledger projections, AccountCare phase calculations, balance views). When a bet is edited, every stored derivation must be recomputed and updated, often via separate code paths that can fall out of sync. This is the root cause of v2's "edit a bet, fix five downstream things via SQL patches" problem and the \~$4,800 ledger reconciliation gap.

v3 inverts this: bets and operations log entries are the source of truth. Everything else is computed on read.

**The architectural stance:**

- **Source of truth (stored):** bets, operations log entries, account metadata, FB ledger transactions, persona profiles, bookmaker hygiene rules, AccountCare flag definitions
- **Derived (computed on read, not stored):** turnover by account/persona/period, weekly hygiene plans, account health scores, balance views, FB inventory, EV totals, all analytical aggregates

When the UI shows "Kate's PointsBet weekly turnover," that number is computed from bet records at display time. When a bet is edited, all derived views show the correct number on their next read. There is no cascade of updates because there is no stored derivation to update.

**Performance tradeoff:**

Computing derivations on every read uses more CPU than reading pre-computed values. For the operator's scale (single user, \~30 accounts, hundreds of bets per week, \~tens of thousands of bets per year), SQLite handles this trivially even with naive queries. No pre-computation is needed for performance.

If a specific query becomes slow at scale (unlikely within v3's lifespan), it can be cached in-memory at the read layer with explicit invalidation on relevant writes — but this is an optimisation, not the default. Default is always "compute fresh from source-of-truth data."

**Why this works with the operations log (DR-006):**

The operations log is also event-sourced — it stores events, not state. State is computed by replaying the log. The accounting layer becomes uniformly event-sourced: bets and operations log are events; everything you see is a query over those events. Edits are clean because events are the truth and edits modify events directly.

**Tradeoff:** Less familiar pattern for some developers. Forces architectural discipline — no temptation to "just store this aggregate for speed." Acceptable: the discipline is what makes edits safe and reconciliation clean.

**Date:** 2026-04-26

**Amendment 2026-05-12 (Session 124):** The "compute on read" principle stays load-bearing for **aggregates** (balances, turnover totals, FB inventory, cash flow summary views, operation net flow) and for **cross-entity derivations** (hygiene status per account, outcome-vs-warning analysis). But the principle is **refined for per-entity mutable state**: state that belongs to a single entity — per-bet lifecycle state (`match_status`, `settlement_state`, `dead_heat_count`, `removed_runner_count`, `unexpected_state_count`, `last_read_market_state`, `last_reconciled_at`, `reconciliation_attempts` per architecture.md §A.3) — is stored as mutable columns on the entity row rather than computed by event-chain replay. Transitions are not historical; the previous value is overwritten when a transition fires. This is acceptable per the operator's personal-operation scale and the absence of external audit obligation. Reliability rests on worker correctness (substantial test coverage behind W6 / W6.5), Betfair's `market_settlement` API returning truthful results, and operator catches via Burst Review (§C.1) within normal review windows. See DR-027 Session 124 amendment for the full architectural rationale.

The earlier framing — "bets and operations log entries are the source of truth; everything else is computed on read" — survives as the default. Per-entity mutable state is the named exception, captured here as the materialised-view-on-entity-row pattern. Source of truth for aggregate computations is now (per architecture.md §A.9): bet records (`bets` + `bet_legs` per DR-032) plus events in the three per-domain event log tables (`cash_flow_events`, `promo_events`, `ops_events` per architecture.md §A.2 / DR-027 Session 124 amendment).

This amendment closes Finding #5 from the Session 123 pre-W14 codebase review (DR-019 derived-state-on-read partially divergent — divergence is acknowledged as a deliberate materialised-view-on-entity-row pattern, not a defect).

---

## DR-020: Standalone Betfair liquidity capture, cadence-stepped, runs on VPS

**Why:** Hedge trigger calibration (per DR-016) requires liquidity data — specifically, matched-volume curves through pre-jump and into in-running. This data is not historically available at the granularity needed; it must be captured forward from now. Capture cannot wait for v3 build because every day of missing data is irreplaceable. Capture is also independent of v2 (which is left untouched per operator direction) and v3 (which is in design, not yet built). It runs as a standalone process.

The capture also serves Job 4 broadly: late-market runner movement, in-running price action, and total-matched patterns are all analytical assets v4 will consume.

**Scope:**

Australian thoroughbred, harness, and greyhound racing. Other markets can be added later if proven useful.

**Cadence:**

Time before scheduled jumpPoll interval&gt; 1 hourevery 5 min10 min – 1 hourevery 1 min5–10 minevery 30 sec2–5 minevery 10 sec1–2 minevery 1 sec&lt; 1 minevery 0.5 secSuspension/jumppauseIn-running (market re-opened)every 1 secSettlementstop

High resolution where the data is interesting, sparse where it isn't. In-running capture continues through settlement to enable analysis of post-jump matching behaviour (relevant to free bet persistent-order outcomes).

**Captured per poll:**

For each runner in each in-scope market:

- Best back price + size available
- Best lay price + size available
- Top 3 back prices + sizes (market depth)
- Top 3 lay prices + sizes (market depth)
- Total matched on the market
- Timestamp

**Storage and infrastructure:**

- Runs on existing Hostinger VPS (where v2's scrapers already run)
- Standalone Python process, separate from v2's processes
- Standalone SQLite database, separate from v2's data
- Uses operator's existing Betfair API credentials
- No integration with v2 or v3 application code
- Append-only writes; no in-place updates

**Estimated volume:** \~20 KB per race captured at full cadence. At 50 races/day, \~1 MB/day, \~365 MB/year. Trivial.

**Build timing:** Built as a separate Claude Code session, intended for 2026-04-27. Spec captured in `work_in_progress.md` with full requirements so the build session has clear scope.

**Tradeoff:** Adds a small ongoing process to maintain. Acceptable because the data is irreplaceable and cheap to capture.

**Date:** 2026-04-26

**Amendment 2026-04-28 (Session 11):** The standalone Betfair liquidity capture build originally targeted by this DR is **superseded for AU racing** by `capture.db` — the existing UK VPS racing-data capture system at `/home/racing/racing-data-capture/data/capture.db`. capture.db captures Betfair time-series snapshots for AU thoroughbred / harness / greyhound markets with 3-level depth on both back and lay, total matched, last_match_time, and snapshot batch tracking, on a tiered cadence (5 min standard → 60s intensive in the 5 min pre-jump window → 60s in-running → 2 min settlement checks). This implementation predates v3 and has been running successfully serving Strategy 1, BetHub v2, the Racing EV model, and AFL Edge.

Per DR-027, v3 reads at-log-time market snapshots from capture.db via `vps_client` rather than running its own capture process. Per the DR-026 amendment (also dated 2026-04-28), the snapshot fields and capture principle are unchanged — only the source path is updated. Per DR-029, the architecture is periodic-only (no on-demand fresh-now pattern); analytical bracketing via surrounding-interval snapshots in capture.db provides stronger market-context visibility than a single fresh snapshot would.

**Sports markets (AFL, NRL, etc.) are NOT covered by capture.db and remain genuinely uncaptured today.** The DR-020 capture principle (cheap to capture now, expensive to reconstruct retrospectively) still applies to sports markets and is the first item in the upcoming DR-029 data review. Day-one v3 sports bets will log with `bf_snapshot_unavailable = true` until the sports capture extension lands per DR-029.

**For DR-014 (soft-book price context in burst-mode action queue):** existing VPS bookmaker scrape cadence (5 min standard / 90–120s intensive, 5 min pre-jump) may or may not be sufficient for DR-014's hot-path use case. Cadence verification is parked as a build-time question per DR-029's data review. Architectural shape (capture.db is the source) is unchanged regardless of cadence outcome.

---

## DR-021: Session logging and date discipline

**Why:** Sessions can span overnight or multi-day periods. Without explicit logging, Claude has no reliable way to know how much time has passed between user messages, and date stamps written into governance docs can drift (e.g. a decision dated for the day the session opened, even when the actual write happens 12+ hours later). v2's governance suffered from inconsistent and stale date stamps, making the audit trail unreliable. v3's rebuild governance must not repeat this.

**Three disciplines locked:**

**1. System date verified at every governance write.**

Before writing any date stamp into any governance document, Claude runs `date "+%Y-%m-%d %H:%M %Z"` via bash and uses the actual returned date. No date stamps written from memory or from session-open context. The cost is one bash call per write; the benefit is an auditable trail that does not drift.

**2. Per-session log file maintained throughout each session.**

Each session has a single `session_log.md` file in the rebuild folder root. The file is opened at session start, appended to on every Claude response, and archived at session close.

Format per session:

```
# Session N log

**Opened:** YYYY-MM-DD HH:MM TZ

## Activity

- HH:MM — \[5-15 word description of response\]
- HH:MM — \[...\]
- HH:MM — \[...\]

**Closed:** YYYY-MM-DD HH:MM TZ **Summary:** \[1-2 sentence summary of what got done\]
```

Each appended entry is a one-line bash append — minimal latency, durable against unexpected session interruption. Descriptions are deliberately short — enough to scan the log later and recall the conversation shape, not enough to become noise.

**3. Session logs are archived, not deleted.**

At session close, the active `session_log.md` is moved to `sessions/SESSION_NN.md` (where NN is zero-padded session number) and the active file is removed. The next session opens with a clean active log file. Archive is preserved for future analytical use (how long did sessions run, how much got done per session, when did each conversation happen) and for cross-session date-anchoring. Folder convention follows the existing `sessions/SESSION_01.md` from Session 1.

**Session-open read protocol (kept minimal to reduce friction):**

- **Always read:** `work_in_progress.md` (per DR-005), most recent archived session log (one file, to establish "when did we last talk")
- **Architecture/design sessions add:** `decisions.md` in full
- **Never read by default:** [vision.md](http://vision.md) (only if explicitly relevant), older session logs, archive folders

The protocol scales: simple build sessions or follow-ups read two files; architecture sessions read three. No session opens by reading more than three governance files unless something specific demands it.

**Session-close protocol:**

```

1. Verify system date via bash
2. Append `Closed:` timestamp and summary to active session log
3. Update `work_in_progress.md` with current session's outcomes and next session's scope (using verified date)
4. Move active `session_log.md` to `sessions/SESSION_NN.md`
5. Confirm next session's opening prompt is current
**Mid-session awareness:**

Within a session, Claude can read the active session log to check elapsed time between current and prior user message. If a meaningful gap is detected (e.g. &gt;4 hours, or any gap crossing local midnight), Claude briefly acknowledges and re-anchors before responding to substantive content. Not surfaced for short gaps — only when it changes the right move.

**Tradeoff:** Adds one bash call per response (date check + log append) and one new file per session. Latency is small (\~1s per response). Acceptable: the durability and cross-session date-anchoring value far exceeds the cost, and v2's governance proved that informal date-handling produces compounding errors.

**Date:** 2026-04-26
```

```
```

```


---

## DR-022: Vocabulary correction — `account` is a person, `book` is a bookmaker, `account-at-book` is the registration

**Status:** Vocabulary lock. Supersedes the use of "persona" in DR-010, DR-013, and any earlier reference. Per DR-021's discipline, prior DRs are not edited; this DR records the corrected reading.

**Why:** Session 3 surfaced that the term "persona" had been used inconsistently with how the operator actually thinks about the operation. The operator's mental model is: real people (Tim, Kate, Sarie, friends) hold registrations at bookmakers. The person is the unit of identity; the bookmaker is the unit of platform; the registration is the unit at which money sits and promos are received. Continuing to call the person a "persona" obscured this and threatened to produce schema with the wrong noun on the wrong table.

**Locked vocabulary (Session 3 onward):**

- **Account** — a real person whose identity is used for registrations. Tim, Kate, Sarie, friends. Has its own balance sheet (money owed to them as fees, money transferred to them awaiting deposit). Owns one or more registrations across bookmakers.
- **Book** (or **bookmaker**) — the betting company. Sportsbet, PointsBet, Ladbrokes, Neds, etc. Reference data with attributes including ownership cluster and platform.
- **Account-at-book** — the specific registration of one account at one book. The unit at which money sits, promos are received, tier and phase are tracked, and conditioning happens. One account never holds two registrations at the same book.

**Reading prior DRs:** Where DR-010, DR-013, or any earlier DR uses "persona," read "account." Where they refer to "(persona × bookmaker)" or similar, read "account-at-book." The semantic intent of those decisions is preserved; only the noun is corrected.

**Tradeoff:** Brief cost in cross-referencing — anyone reading DR-010 or DR-013 must mentally substitute. Acceptable because silent rewriting of prior DRs would violate DR-021's no-silent-restructuring discipline, and the alternative (carrying inconsistent vocabulary into the schema) would compound through every downstream artefact.

**Date:** 2026-04-26

---

## DR-023: Principle — operator focuses on betting decisions and hedge intent; the system handles all administrative work

**Status:** Principle (per DR-007). Governs all design decisions about where work sits in the operator-vs-system division of labour.

**Why:** v2 leaks administrative friction into the operator's flow at every stage — manual settlement, manual free-bet creation when an insurance trigger fires, manual reconciliation, manual hedge match-status checking, manual ledger correction, fuzzy bet-to-Betfair matching that the operator has to repair. Every minute spent on this is a minute not spent identifying promos and placing bets. The accumulated weight of this also bleeds attention during bursts, where the operator finds themselves balance-watching and outcome-watching instead of attending to the next decision.

The principle inverts the default. The operator's job is two things: identify and place bets; choose hedge intent. Everything else — settling bets, creating free-bet records when triggers fire, matching backs to lays, computing balances, surfacing reconciliation gaps, classifying hedge outcomes — is the system's job. The operator never enters data the system could have derived; the operator never reconciles a number the system should have computed.

**Concrete consequences:**

- Bet settlement is automated via Betfair-bet-ID linkage at log time (no fuzzy matching, no operator confirmation step).
- Free-bet records are auto-created when an insurance bet settles as a loss within insurance terms.
- Hedge classification is auto-computed from Betfair data where derivable (per DR-025).
- Balance views and reconciliation are computed on read from bet records and the per-domain event log tables (`cash_flow_events`, `promo_events`, `ops_events` per architecture.md §A.2 — see DR-019 Session 124 amendment for the materialised-view-on-entity-row refinement and DR-027 Session 124 amendment for the per-domain event-table spine).
- Late-scratch deductions and similar real-world anomalies are captured as named events, not as unexplained drift the operator must investigate from scratch.

**Boundary cases that remain operator decisions:**

- Whether to take a promo (the betting decision proper).
- Hedge intent — hedge or let-ride, with reason where intent diverges from default.
- Resolving cases the system could not classify automatically (e.g. unhedged-deliberate vs unhedged-oversight in the small minority of bets that need retrospective classification).
- Editing any record where the operator catches an error the system did not detect (per DR-017).

**Tradeoff:** More upfront engineering — auto-settlement and auto-FB-creation are non-trivial to build correctly. Acceptable because the alternative is permanent operator tax that grows with operation scale, and v2 has demonstrated that this tax compounds over time as the operation grows.

**Date:** 2026-04-26

---

## DR-024: Principle — operating-mode and analytical-mode surfaces are separated

**Status:** Principle (per DR-007). Governs UI surface design and refines DR-008 (Smart Betfair view) and DR-012 (keyboard-first hot path).

**Why:** Session 3 surfaced that conflating operating-mode and analytical-mode is a source of friction in both directions. While operating, balance-watching and per-bet outcome-watching dilute attention from the betting decision and introduce emotional noise into what should be a mechanical execution loop. While analysing, mid-bet emotion biases the reading of the numbers. The operator named this directly: "I really need to focus on separating the operational side of things versus the analytical side of things, which should just be its own dedicated session, not seeing how I'm doing bet to bet."

**The principle:**

Operating-mode surfaces (action queue, bet logger, hedge modal, race window views, anything inside a burst or persona session) display only forward-looking, decision-relevant context. Analytical-mode surfaces (reports, reconciliation views, EV-realised-vs-estimated dashboards, anything that answers "how am I doing") are accessed through dedicated entry points that are not embedded in the operational flow.

**What operating-mode surfaces show:**

- Next promo, race window, account-at-book context for the bet about to be placed
- EV of the specific decision in front of the operator
- Hedge target and fair-price indicator at the moment of hedge placement
- AccountCare alerts at their tiered severity (per DR-015)
- Soft-book price context (per DR-014)

**What operating-mode surfaces do not show:**

- Running portfolio balance
- Today's realised P&L
- This week's EV total
- Per-bet settlement results as they come in during a burst
- Reconciliation gap status
- Anything answering "how am I doing"

**What analytical-mode surfaces show:** all of the above and more, accessed deliberately through their own entry point.

**Behavioural reinforcement:**

The operator has explicitly asked to be reminded of this principle when drifting back into balance-watching during bursts. Future sessions should reinforce this when the topic surfaces.

**Tradeoff:** The operator may want a quick "how am I doing today" glance during a burst and find that path deliberately absent. Acceptable: the operator's own assessment is that the temptation to look is itself the friction, and removing the surface from the operating flow protects attention. The analytical surface is one click away when the operator chooses to enter it.

**Date:** 2026-04-26

---

## DR-025: Hedge classification model — five terminal states plus one transient, auto-classified where derivable, settlement+24h auto-resolve for the ambiguous case

**Why:** Session 3 surfaced that hedge intent and hedge outcome cannot be cleanly captured by a single binary (hedged / not hedged). Three operationally distinct states exist: hedged-as-intended, deliberately-not-hedged (operator chose to let the bet ride for EV reasons), and intended-but-failed-to-match (operator wanted to hedge, the lay didn't fill). Each has different downstream consequences — partial or failed matches leave residual exposure the operator should know about; deliberately-not-hedged is a clean state; hedged-as-intended is the default working case.

A naive classification would force the operator to set hedge intent at log time, but this conflicts with DR-023 (operator focuses on betting decisions, system handles admin) and adds friction to the most time-pressured part of the operation. The model below auto-classifies where derivable from Betfair data and isolates operator input to the small ambiguous slice.

**The five terminal states plus one transient:**

| State | Meaning | How it gets set |
|---|---|---|
| `hedged` | Betfair lay linked, fully matched | Auto, from Betfair data |
| `hedge_partial` | Betfair lay linked, partial match — residual exposure exists | Auto, from Betfair data |
| `hedge_failed` | Betfair order placed, no match at all — full exposure | Auto, from Betfair data |
| `unhedged_deliberate` | No Betfair order; operator chose not to hedge | Operator (Burst Review) or auto-resolve |
| `unhedged_oversight` | No Betfair order; operator retrospectively flagged as a mistake | Operator only — no auto-path |
| `unhedged_unclassified` | Transient — no Betfair order, awaiting classification or auto-resolve | Default state on log when no Betfair order exists |

**Auto-classification flow:**

1. At log time, the system never asks the operator about hedge intent. The bet is logged. If a Betfair order is placed against it (now or later), the link is captured.
2. If the bet is settled and a linked Betfair lay is fully matched → `hedged`.
3. If the bet is settled and a linked Betfair lay is partially matched → `hedge_partial`.
4. If the bet is settled and a linked Betfair order exists but no match → `hedge_failed`.
5. If the bet has no linked Betfair order at all → `unhedged_unclassified` until classified or auto-resolved.

**Auto-resolve rule for the ambiguous case:**

24 hours after the bet settles (not 24 hours after log), `unhedged_unclassified` auto-resolves to `unhedged_deliberate`. The settlement-anchored timer accommodates multi-day sport settlement and late-protest result reversals. The Burst Review surfaces unclassified bets at two stages: "unclassified — pending settlement" (informational, no pressure) and "unclassified — ready to classify" (after settlement, prompts retrospective classification).

`unhedged_oversight` has no auto-path. It is only ever set by the operator retrospectively saying "I meant to hedge that and forgot." The asymmetry is deliberate: the system biases toward the empirical common case (deliberate let-ride), and only records oversights when the operator actively confirms them.

**Operations log captures the path to terminal state:**

Every classification event goes into the operations log with the path indicator: operator-classified vs auto-resolved. v4 analytics can distinguish operator-confirmed deliberate states from auto-resolved deliberate states and weight them differently if needed.

**Configurability:**

The 24-hour-after-settlement window is a setting, not a hard-coded value. Default 24 hours, adjustable.

**Tradeoff:** Six states is more complex than two. Acceptable because the additional states answer real analytical and operational questions (residual-exposure surfacing, hedge-skip vs hedge-failure distinction, retrospective oversight tracking) that a binary cannot. The complexity is borne by the system, not by the operator at log time.

**Date:** 2026-04-26

**Amendment 2026-05-22 (Session 139):** Revisit per the standing "revisit DR-025 before W15 brief drafting" flag. Outcome: the six-state model is confirmed as-is — no change to the states, the auto-classification flow, or the settlement+24h auto-resolve rule.

*States confirmed.* All six states retained. `unhedged_oversight` (operator meant to hedge and forgot) is rare but real, especially in busy bursts; kept because it is operator-set-only (no auto-path) and is a label that never feeds the balance maths, so retaining it carries no calculation or data-capture risk. No new state is added for the "lay placed only to convert a free bet" pattern: a hedge is a hedge regardless of what it covers, and the cash-vs-free-bet distinction is derived from the bet the lay is placed against (which already records cash vs free bet per `is_free_bet`), with the shared `cycle_id` linkage carrying the upstream journey.

*Lay recording shape (mirrors v2).* A Betfair lay is recorded as its own bet record (`book_or_exchange='betfair'`, a `LegRole.HEDGE` leg), sitting in the same operation as the bet it covers via the shared `cycle_id`, and traceable to upstream linked operations. Purpose (turnover hedge vs free-bet hedge) is derived from the linked bet, not stored as a separate state. This mirrors v2, where a lay is a `bets` row with `side='lay'` linked to its back bet through the shared `operation_id`.

*Lay substrate for balance correctness (the load-bearing decision).* The W12 Location 1 balance derivation mishandled the Betfair lay side of a hedge (handled it on a back-bet basis) because the bet row carries nothing distinguishing a lay from a back and no commission. Two stored fields close the gap, mirroring v2's `bets` table: (1) a side tag (`LAY` / `BACK`, the existing `BetSideTag` domain enum, currently defined but not persisted) on the Betfair bet record, and (2) a commission rate. Liability is not stored — it is derived on read from matched price, matched stake, and side per DR-019 (derive-on-read), exactly as v2 derives it from odds + stake. The lay maths already defined in the v3 domain model (`domain/bets` — Construction A/B, `HedgeSoftBookStakeKind`) is unchanged; the substrate simply supplies the two inputs the read side was missing.

*Commission sourcing.* The commission rate is Betfair's per-market base rate (`marketBaseRate`), captured and snapshotted at hedge-entry time, with an 8% fallback when the lookup is unavailable — not a static venue/track lookup table. This replicates v2's current method (`_get_commission_for_market` in `src/services/betfair_sync.py`, which reads `description.marketBaseRate` per market and divides by 100) and the lesson behind it: v2's prior table-based venue/race-type lookup drifted and silently misclassified some markets (NSW/ACT thoroughbred and NRL at the wrong rate); reading Betfair's authoritative per-market rate is the single source of truth and is why rates come out track-accurate (per-track variation — e.g. lower-rate Queensland courses — is simply Betfair's per-market rate, not a value v3 maintains). Consistent with Betfair-owns-market-facts (DR-026 / architecture.md §A.10). Account-level discount tier (`discountAllowed`) is out of scope per the v2 precedent — Betfair applies any account discount on settlement; the stated MBR is what is stored.

*Separation — balance vs classification.* Balance correctness depends only on the two-field substrate (side + commission); it does not depend on the hedge-classification state machine. The two were coupled in the pre-revisit framing (S138 routed the lay-side gap to "the DR-025 revisit decides the lay substrate"); this revisit establishes they are separable — the lay-balance fix needs neither the `hedge_state` column nor the auto-classification flow.

*Sequencing.* (a) W12.1 — lay-balance fix: adds the side + commission substrate and a lay branch to the read-side balance derivation (`_bet_cash_return` / `_read_bet_rows_for_account_at_book`); standalone surgical Code brief, may precede W15. The Betfair-rate capture itself rides with the hedge-entry surface (racing screens, W17+); W12.1 adds the fields and the read-side maths in the read-first shape W12 was built in. (b) W15 — the operations log ships the `hedge_state_classification` audit-event shape only. (c) Post-W15 — the `hedge_state` column on the `bets` row, the auto-classification flow, and the W8 burst-review operator surface (including visibility of unclassified bets during the settlement+24h window) land with the racing / burst-review screens.

*Cross-references.* architecture.md §A.5 (Location 1 at-book balance), §A.6 (hedge-state deferred block), §A.3 (bets row / `bet_legs`), §A.10 (Betfair canonical source); DR-019 (derive-on-read, S124 amendment); DR-032 (bet-record shape); v2 `betfair_sync._get_commission_for_market` (per-market MBR sourcing). Closes the before-W15 DR-025 revisit flag.
```


---

## DR-026: Principle — market-context snapshot captured on every bet at log time

**Status:** Principle (per DR-007). Governs the bet record schema in the accounting layer and the data interface between the execution layer's odds aggregator / liquidity capture and the accounting layer's bet-logging surface.

**Why:** Round 5 of Session 4 surfaced that several distinct analytical questions all reduce to the same data requirement: a point-in-time snapshot of Betfair market state at the moment a back bet is logged. Q6 (hedge-skip outcomes vs counterfactual hedge return), Q7 (optimum hedge timing, drift between log time and jump), and the operator-raised broader probe ("should we hedge at all given Betfair commission drag?") all need the same data — what the Betfair market looked like at the moment of bet placement.

The operator's stance, locked here as the principle: capture is structurally on-by-default for every bet, not gated by which analytical questions are currently in scope. *"Having point-in-time data on every single bet will not only allow us to answer analytical questions now, but also keeps all sorts of doors open in the future for other analysis we may not have yet thought of."* The cost is small (three fields, no manual input); the cost of *not* doing it is unrecoverable — a year from now the question cannot be answered retrospectively because the moment is gone.

**What gets captured at log time:**

For every bet recorded — promotional or non-promotional, hedged or unhedged, cash or free bet — the bet record includes a market-context snapshot:

- **Best Betfair lay price + size available** on the bet's runner at the moment of log
- **Best Betfair back price + size available** on the bet's runner at the moment of log
- **Total matched on the market** at the moment of log
- **Snapshot timestamp** (the bet log timestamp; both share the same instant)

The snapshot is sourced from the standalone Betfair liquidity capture per DR-020, which runs on the VPS and writes to its own SQLite. The accounting layer reads the most recent capture-poll for that market at log time and stores the snapshot inline on the bet record. If the most recent capture is more than N seconds stale (parameter to be set during build, target ≤5 seconds for pre-jump windows), the bet record flags the snapshot as stale rather than storing misleading data.

**Why captured inline on the bet, not derived later:**

The liquidity-capture database is append-only and time-indexed; in principle the snapshot could be looked up at read time by joining bet log timestamp to capture polls. Two reasons not to:

1. The liquidity capture is a separate process on a separate database. A failed or paused capture process means missing snapshots if derived at read time. Inline storage means the snapshot is durable against later capture-side issues.
2. Per DR-019, derived state on read is the default *for state computed from events in the same event log*. A market-context snapshot from an external time-series database is not derived state in that sense — it is captured external context, properly stored where the bet record lives.

This is a deliberate, narrow exception to DR-019's "compute on read" principle, justified by the cross-system durability requirement.

**What this principle does *not* require:**

- No additional manual input from the operator at log time. The snapshot is sourced automatically from the liquidity capture.
- No surfacing in operating-mode UI per DR-024. The data is captured for analytical use; it is not displayed during a burst.
- No real-time computation of "what the hedge would have returned" or similar derived counterfactuals. Those are analytical-mode queries against the captured data, built when needed.

**Reconciliation against future-captured data:**

The standalone Betfair liquidity capture also continues capturing the same market through to settlement. Later analysis can reconcile the at-log-time snapshot against the full price-and-volume curve from log time through to jump and through to settlement, enabling the timing-optimum analysis (Q7) and counterfactual return analysis (Q6 broadened, "lay everything?" probe).

**Tradeoff:** Three additional fields on every bet record and one read against the liquidity-capture database at log time. The read adds small latency to bet logging (target sub-100ms; if the local cached snapshot is fresh, sub-10ms). Acceptable: the data is irreplaceable retrospectively, the manual cost is zero, and the principle preserves analytical optionality at trivial structural cost.

**Date:** 2026-04-26


**Amendment 2026-04-28 (Session 11):** The at-log-time market-context snapshot for AU racing bets is sourced from `capture.db` via `vps_client`, not from a standalone capture process. The fields captured on the bet record are unchanged (best Betfair lay price + size, best back price + size, total matched, snapshot timestamp, stale flag). The cross-system-durability justification for inline storage (rather than read-time derivation per DR-019) survives intact — the snapshot is captured external context, properly stored on the bet record, durable against later capture-side issues including VPS reachability changes and `capture.db` schema evolution.

Per DR-029, the architecture is **periodic-only with analytical bracketing**: VPS returns the most-recent-stored snapshot from `capture.db` (typically 0–60s old in pre-jump windows; longer outside). v3 marks `stale_flag = true` above a tunable threshold (e.g. 90s) and `bf_snapshot_unavailable = true` above a larger threshold (e.g. 5 min) or when VPS is unreachable. Analytical queries can later bracket the bet's true market state by reading the surrounding-interval snapshots from capture.db, giving stronger market-context visibility than a single fresh snapshot would. **No on-demand fresh-now pattern** is introduced unless cadence verification in the data review proves insufficient.

Late scratchings are handled via a separate flag: v3 reads scratching state from `capture.db` alongside the snapshot at bet-log time; if a scratching occurred between snapshot timestamp and bet-log time, v3 flags this on the bet record.

For sports-market bets (AFL, NRL, and any non-racing market type), at-log-time snapshots are not available day-one per DR-029. v3 logs the bet with `bf_snapshot_unavailable = true` and surfaces the gap in Burst Review.

The integration is implemented in a single module (`vps_client` or its named successor) per DR-027. The data API contract is load-bearing; per DR-028, no second integration point is permitted.

DR-026's architectural stance (capture cheap, capture inline on the bet, capture durable across system boundaries) is unchanged. Only the source path is updated. The principle is what locks; the source path is implementation.

**Open question for Session 14 multi-agent review:** Whether DR-026's inline-storage principle should be further revised to drop bet-record snapshot storage entirely, with all race-side context (the snapshot, field-size captures from Slice 6, scratching events, etc.) resolved via `vps_client` from capture.db at read time. This was raised in Session 11 after the periodic-only architecture was locked, and is reserved for Session 14's multi-agent governance review as part of the data-layer-first sequencing assessment. The simplification, if adopted, would: (1) shrink the `bet_placed` payload by removing inline snapshot fields; (2) remove `field_size_at_bet_placement` and `field_size_at_settlement` from the Slice 6 amendment; (3) clean DR-028 forbidden pattern 1 by removing its single narrow exception. Until reviewed, DR-026's current form (inline snapshot storage on bet records, with periodic-only architecture per this amendment) and Slice 6's current form remain in force.

**Amendment 2026-05-12 (Session 124):** DR-026's at-log-time market-context snapshot scope is **bounded to the fields already defined** in DR-026 plus the Session 11 amendment: best back price + size, best lay price + size, total matched, snapshot timestamp, stale flag, `bf_snapshot_unavailable`, `bf_snapshot_aligned_to_placement`, `late_scratch_between_snapshot_and_log`. **No additional market-context snapshot fields are added to the `bets` row.**

Deeper market context — back / lay depth beyond first price, time-series snapshots around placement, in-running price curve, total-matched trajectory — lives in `capture.db` (the analytical line per DR-027). Analytical queries that need this deeper context cross-reference at analysis time, joining bet records to `capture.db` snapshots by `betfair_market_id` + `bet_placed_at` timestamp. The bracketing model from DR-029 (read both the T-x snapshot and the T-x+cadence snapshot from capture.db at analysis time) gives stronger market-context visibility than additional inline fields would.

This amendment closes Finding #3 from the Session 123 pre-W14 codebase review (market-context snapshot fields absent on `bets` beyond DR-026 scope — confirmed as intentional bound, not a gap).

**Carry-forward dependency:** §2.4 Fix 4 cadence design must verify that `capture.db` capture cadence is tight enough to bracket near-jump placements. The operator typically places close to jump; the cross-reference relies on capture timestamps tightly framing the bet's `placed_at`. If Fix 4 surfaces that cadence isn't sufficient for analytical reliability, this amendment's resolution is revisited.

---

## DR-027: Two-database architecture — v3 bet-data and capture.db race-data are separately owned, joined by reference

**Why:** Session 11 surfaced that the existing UK VPS racing-data capture system (`capture.db`, ~30k AU thoroughbred / harness / greyhound races, Betfair time-series snapshots, bookmaker time-series snapshots, BSP historical, calibration summaries) is the canonical source for race-side data and already serves Strategy 1, BetHub v2, the Racing EV model, and AFL Edge. v3 was about to design a `race` entity and duplicate this capture. Duplicating it would have produced two race-data sources drifting from each other — a v2-shaped failure mode at slow cadence.

The architectural fact locked here: **race-side data and bet-side data are owned by different systems, in different databases, joined at read time by stable identifier.** This is the DR-019 "compute on read" discipline extended across a database boundary.

**Locked stance:**

- v3's accounting-layer database (`bethub.db` or whatever the rebuild names it) owns **bet-data**: all entities and events from Slices 1–6 (account, book, ownership_cluster, platform, account_at_book, promo_template, promo, account_arrangement, the single event log carrying bet_placed / bet_correction / bet_settled / hedge_state_classification / cascade events / FB credit and deployment events / friend_payment_made / etc., plus operations log entries).
- `capture.db` (UK VPS, separate infrastructure, separate process) owns **race-data**: races, runners, finish positions, Betfair time-series snapshots, bookmaker time-series snapshots, BSP historical, batch summaries, daily calibration summaries.
- **No fact is owned by both.** No row exists in both databases. No table is written to by both systems.
- v3 references race-data by stable identifier — Betfair `market_id`, the natural key `(race_date, venue_normalised, race_number)`, or `capture.db`'s `race_id`. v3 reads race-side context on demand via the existing read-only data API on the VPS (`racing-api.service`, `127.0.0.1:8400` over SSH tunnel). v3 never writes to `capture.db`. v3 never stores a copy of race-data locally.
- The integration is implemented in a single module (`vps_client` or its v3 equivalent). All v3 access to `capture.db` flows through this one module.

**What this means concretely:**

- When a bet is logged in v3, the bet event payload carries `event_id` (the Betfair market_id) and `bf_market_id` (the same identifier scoped to its source) plus the DR-026 market snapshot. Race classification, distance, surface, finish position, BSP — none of these live on the bet record. They live in `capture.db` and are read on demand when a query needs them.
- When the operator opens a Burst Review and wants to filter bets by race class or distance, v3 resolves each bet's race identifier through `vps_client` and returns the joined view. The join happens at query time in Python, not in SQL.
- When `capture.db` gets a race-data correction (a Racing API metadata update overnight, a finish-position revision after a stewards' inquiry), v3's next read sees the corrected value automatically. No sync, no cascade, no drift.

**Tradeoffs:**

- v3 is dependent on the VPS being reachable for any read that needs race-side context. Mitigations: the existing liveness-check infrastructure already monitors VPS health; bet-logging-time reads degrade gracefully via the `bf_snapshot_unavailable` flag pattern (DR-026 amendment) when the VPS is unreachable; analytical-mode queries can tolerate brief unavailability.
- The data API contract becomes load-bearing for v3. If `capture.db`'s schema evolves and the API doesn't, v3 silently gets stale shape. Discipline against this is in DR-028.
- Cross-DB joins in SQL are not possible. Joins happen in Python at the integration boundary. For v3's scale (single user, tens of thousands of bets per year, hundreds of operator queries per day), this is structurally fine.

**Why this is the right pattern, not a v2-style mess:**

v2's coupling problems were caused by stored derived state going out of sync, mixed ownership of the same data within one database, and no clear boundaries. The pattern here is the opposite: strict ownership per fact, no stored derivations of cross-DB data, single integration boundary. The failure modes are *different* from v2's failure modes — contract drift across the boundary rather than ledger drift within the database. DR-028 codifies the discipline that prevents the contract-drift failure mode from compounding.

**Date:** 2026-04-28

**Amendment 2026-05-12 (Session 124):** DR-027's top-level architectural fact — race-data in `capture.db`, bet-data in v3's operational store, joined by Betfair-side reference via the single `vps_client` integration boundary — is unchanged by this amendment. The cross-database boundary is unaffected.

What this amendment names is the bet-data side's internal shape, which has diverged from the original "everything is events / single append-only event log" framing of v3's accounting layer:

- **Bet records are mutable, not event chains.** The shipped `bets` table (per DR-032) plus `bet_legs` table holds per-bet state — including post-write-mutable columns (`match_status`, `settlement_state`, `dead_heat_count`, `removed_runner_count`, `unexpected_state_count`, `last_read_market_state`, `last_reconciled_at`, `reconciliation_attempts`) updated in place by the W6 / W6.5 / W8 workers. Settlement is not a `bet_settled` event that gets superseded; it is a column on the `bets` row that mutates. Transitions are not historical. See architecture.md §A.3 / §A.6 / §A.9 for the column-level detail.
- **Events live in three per-domain tables, not one unified log.** The original DR-027 framing — "the single event log carrying `bet_placed` / `bet_correction` / `bet_settled` / `hedge_state_classification` / cascade events / FB credit and deployment events / `friend_payment_made` / etc., plus operations log entries" — is superseded. Shipped reality has zero rows in any unified event-log table. Cash flow events live in `cash_flow_events` (W14 ships); promo lifecycle events live in `promo_events` (W13 ships); ops events live in `ops_events` (W15 ships).

**Why this asymmetry — bet records mutable, events append-only:**

The audit-trail concern that originally motivated the unified event-log spine (everything is replayable from immutable events) was load-bearing for systems with external audit obligations. v3 is a personal gambling assistant with no audit obligation (no accountant, no ATO, no regulatory body reviewing settlement history). The reliability question collapses from "can we defend any historical settlement to an external auditor" to "does the operator catch misclassifications before they compound." The shipped pattern's reliability rests on three things:

1. **Worker logic is correct** — substantial settlement-test coverage behind W6 / W6.5.
2. **Betfair's `market_settlement` API returns truthful results** — decades of operational track record.
3. **Misclassifications get caught operationally before they compound** — W8 burst-review queue (per architecture.md §C.1) gives the surface to fix them within the normal review window.

If a future audit need surfaces (operator takes on a partner, incorporates, regulatory shift), a transitions log can be added as a forward-only operation — pre-change history is lost but post-change history is captured. The Session 123 pre-W14 codebase review surfaced this asymmetry (Findings #1 and #2); the final routing was "document the asymmetry, leave shipped as built". This amendment is that documentation.

**What this amendment does NOT change:**

- The cross-database boundary (DR-027 §1) is unchanged. `capture.db` still owns race-data; bet-data lives separately in v3's operational store; single integration via `vps_client`.
- DR-028's forbidden patterns continue to apply — no race-data caching in v3, no denormalisation, no second integration point.
- DR-026's at-log-time market-context snapshot pattern is unchanged (snapshot fields per the Session 11 amendment plus bounded per the Session 124 amendment).
- DR-019's "compute on read" principle continues to apply to aggregates and cross-entity derivations (per the DR-019 Session 124 amendment — refined for the materialised-view-on-entity-row pattern).
- DR-032's canonical-reference-layer schema commitment (Betfair identifiers as canonical join keys, two-table shape) is reinforced by this amendment, not replaced.

**Cross-references:** architecture.md §A.2 (the new spine — mutable bets row + per-domain event log tables), §A.3 (bets row schema), §A.6 (settlement state on bets row), §A.7 (cascades against mutable settlement state), §A.9 (derivation rules), §C.1 (Burst Review surface for provisional resolution). DR-019 Session 124 amendment (compute-on-read refined for materialised-view-on-entity-row). DR-026 Session 124 amendment (snapshot scope bounded; deeper context via capture.db cross-reference).

---

## DR-028: Integration boundary discipline — no caching, no denormalisation, no second integration point

**Why:** DR-027 is only safe if its discipline holds. Discipline that lives only in the heads of session participants is unstable across years of build sessions, model upgrades, fresh-start sessions, and operator-Claude conversations where shortcuts feel locally reasonable. The protection against discipline rot is structural: name the forbidden patterns, make them visible, require a deliberate DR-write to bend them. This DR is the structure.

**Forbidden patterns:**

1. **No race-data caching in v3.** v3 does not store any race-data fact (race classification, distance, surface, finish position, BSP, runner detail, Betfair time-series snapshot, bookmaker time-series snapshot) in its own database. Reads happen on demand through the integration module. The DR-026 at-log-time market snapshot is the **single, narrow exception** explicitly justified in DR-026 itself by cross-system-durability concerns; no other captures may be added to that exception without a new DR. (See also DR-026's open question for Session 14 multi-agent review on whether even this single exception should be removed.)

2. **No race-data denormalisation onto v3 entities.** v3's `bet`, `bet_settled`, or any other v3 entity does not carry denormalised race fields. The Slice 6 fields `field_size_at_settlement` and `field_size_at_bet_placement` are *not* denormalisations — they are point-in-time captures of race state at specific bet-context moments, captured per the DR-026-extended cheap-capture principle. They survive on the bet record because they are bet-context facts, not race-context facts. If a future schema change proposes adding a v3-side field that duplicates a `capture.db` field, that is a denormalisation and is forbidden under this DR.

3. **No second integration point.** v3 talks to `capture.db` through exactly one module (`vps_client` or its named successor). No raw SQLite reads from `capture.db` in any other v3 module. No second HTTP client. No bypass. Schema drift, contract changes, and integration failures surface in one file, not scattered.

4. **No reflexive extension to additional external data sources.** Adding any third data source (a second VPS service, a third-party API, a new database) is a new architectural decision requiring its own DR. The pattern from DR-027 does not give standing permission to "and we'll add this too." Each new cross-system integration is a deliberate, named, documented architectural step.

**How the discipline is reinforced operationally:**

Four lean structural protections, each fires only when relevant — they do not blow out routine session-orientation reading:

1. **Orientation citation at session open.** When Claude reads `decisions.md` during session orientation and reaches DR-027 / DR-028, Claude names them explicitly in the orientation summary as a check that they have been registered for the session. Fires every session.

2. **By-number citation when invoked.** When any in-session proposal touches the cross-DB boundary, Claude cites DR-028 by number and names which forbidden pattern applies before proposing implementation. Fires only when cross-DB topics arise.

3. **Mid-session re-read trigger.** If a cross-DB topic surfaces mid-session (after orientation reading is past), Claude re-reads DR-028 explicitly before responding. Fires only when relevant.

4. **Log discipline-rot watch.** Sessions where DR-028 is invoked, deferred, or even almost-bent get a log entry. Pattern-tracking across sessions becomes possible. Fires only when DR-028 actively participates in a session.

**Additional structural protection:**

- **Multi-agent governance review for high-stakes cross-DB decisions.** High-reversal-cost or high-blind-spot decisions involving the cross-DB boundary are candidates for the multi-agent governance review pattern documented in `governance.md`. The multi-agent review is a structural protection against Claude's anchoring on the v3 frame — distinct from these in-session protections.

- **Reversal as new DR.** A reversal of any forbidden pattern is itself a new DR. The bending becomes visible deliberately, never via session-by-session erosion.

**What this DR does *not* prohibit:**

- Reading from `capture.db` via the data API for any analytical or operational need. The whole point is that reads are cheap and unlimited.
- Storing references (Betfair market_id, race_id, natural-key tuples) on v3 entities. References are not denormalisation.
- Storing bet-context facts that happen to be informed by race state at a specific moment (the Slice 6 field_size captures, DR-026 market snapshots). Bet-context capture is owned by v3.
- Future changes to `capture.db`'s schema or the data API contract. Those are owned by the racing-data project, not v3, and v3's integration module absorbs the change in one place.

**Tradeoff:** Adds a discipline overhead — every cross-DB-related design decision passes through this DR. Acceptable: the alternative is the slow-cadence v2-shaped failure that the operator explicitly named as the meta-risk for this whole architecture.

**Date:** 2026-04-28

---

## DR-029: Data layer is reviewed and brought to v3 fit-for-purpose before v3 build begins

**Why:** Session 11 surfaced two distinct risks for v3's cross-DB architecture: (1) discipline rot at build time, where the path of least resistance under bet-logging pressure could be to add an ad-hoc capture or denormalisation in v3 in violation of DR-028; (2) v3 building against a moving data-API contract while `capture.db` is itself being extended for v3's needs (sports markets, NZ, cadence tuning), producing integration bugs that compound. Both risks are eliminated by sequencing data-layer-first.

The operator also surfaced (Session 11) that the deep scoping work across Slices 1–6 has produced the truest sense of v3's data requirements yet — making this the right moment to review the data layer against those requirements, before build.

**Locked stance:**

The execution-layer (v3) build does not start until the data layer (`capture.db` + data API) has been reviewed against v3's scoped requirements and any required extensions are complete and stable.

**What "fit for purpose" means concretely:**

The data review produces a written audit covering at minimum:

- **Race-data coverage confirmed fit for purpose for v3's scoped needs.** All fields needed by v3 are captured at sufficient cadence with sufficient quality. Includes verification of race classification fields (race_class, distance_metres, race_group, track_type, track_condition_raw), finish position and margin capture, runner-level metadata, BSP / closing Betfair coverage. **Race results coverage is confirmed canonical for v3 auto-settlement** — v3's `bet_settled` settlement logic reads VPS race results via `vps_client` and resolves bet outcomes against them, inheriting Strategy 1 / BetHub v2's existing auto-settlement confidence pattern. NZ thoroughbred / harness / greyhound coverage is re-asked in the data review (operator decision: include if Racing API supports, exclude if not).

- **Sports market data layer added.** Betfair sports markets (AFL, NRL at minimum; other sports per scope) captured to support DR-026 at-log-time snapshots for sports bets in v3. Soft-book sports market coverage is a separate scope question to be decided in the data review.

- **At-bet-placement-time API pattern: periodic-only with analytical bracketing.** v3 calls VPS data API on bet log; VPS returns the most-recent-stored snapshot from `capture.db` with its timestamp and a freshness indication. v3 stores this inline on the bet record per DR-026. **No on-demand fresh-now snapshot pattern is added to the VPS** — the periodic capture (5 min standard, 60s pre-jump intensive, 60s in-running) is sufficient given the analytical model below.

  *Analytical justification (the bracketing model):* the bet record carries the snapshot at T-x with timestamp; analytical queries can read both the T-x snapshot and the T-x+cadence snapshot from `capture.db` at analysis time, observing the market movement *across* the bet timestamp. The bet's true market state at T is bracketed by the surrounding interval data. Cadence determines the tightness of the bracket; for typical pre-jump cadence (60s), the bracket is tight enough that timing-optimum, counterfactual-return, and promo-EV-calibration analyses are well-supported. This is a stronger analytical position than a single fresh on-demand snapshot, because the surrounding-interval data tells us about market movement *around* the bet, not just at a single point.

  *Freshness handling:* v3 marks `stale_flag = true` if the snapshot is older than a threshold (e.g. 90s) and `bf_snapshot_unavailable = true` if the snapshot is older than a larger threshold (e.g. 5 min) or the VPS is unreachable. Thresholds are tunable in v3 config.

  *Late-scratching handling:* v3 reads scratching state from `capture.db` alongside the snapshot at bet-log time; if a scratching occurred between snapshot timestamp and bet-log time, v3 flags this on the bet record. This handles the edge case without requiring an on-demand snapshot pattern.

  *Cadence verification as data-review item:* the data review verifies empirically that pre-jump cadence is tight enough for v3's actual bet-log timing distribution. Resolution paths in priority order if insufficient: (a) extend the pre-jump intensive window; (b) tune the standard-cadence interval; (c) accept the staleness with operator-visible indicator. On-demand snapshot is not introduced unless (a)/(b)/(c) prove insufficient.

  *VPS-unreachable handling:* per DR-026 amendment, v3 logs the bet with `bf_snapshot_unavailable = true`, surfaces in Burst Review.

- **Settlement model simplification (no confidence hierarchy).** The v3-with-VPS architecture removes the need for an algorithmic confidence hierarchy on bet settlement. Two sources, different facts: **VPS race result is canonical for "what happened in the race"** (auto-settlement reads from here); **book settlement (operator-recorded on `bet_settled`) is canonical for "what the operator's cash outcome was"**. Divergences between the two — voids per book rules, dead-heat handling differences, stewards' inquiry resolutions, late book corrections — are surfaced as **reconciliation signals in burst review or session reconciliation reports**, not algorithmically ranked. If divergence frequency turns out to warrant building structure around it, that is a future BetHub update, not a v3 day-one concern.

- **External analytics environmental scan (cheap-capture / expensive-to-reconstruct fields).** The data review explicitly conducts an external environmental scan to identify data fields v3 should capture now to preserve future analytical optionality, even though v3 is not building analytics in this phase. Scope:

  *Source-by-source field inventory.* What does Betfair API expose beyond what we currently capture? What does The Racing API expose beyond what we currently use? Are there other accessible sources (official racing body data, free historical archives, sectional times feeds, league data feeds for AFL/NRL, fitzRoy R package data, AFLTables, NRL-equivalent sources) that we don't currently consume? For each, what's the field list, what's the access cost, what's already in capture.db, what's not.

  *Analytics literature reconciliation.* Survey of racing AND sports analytics work — published research, public-domain models, betting-syndicate disclosures, Kaggle competitions, blog posts from quant-betting practitioners. What features do they use? What does the literature suggest matters predictively?

  *Cross-reference into capture decisions.* For each field the literature suggests is valuable, three buckets: (1) available + currently captured → no action; (2) available + not currently captured + cheap → capture in the data review; (3) available + not currently captured + expensive, *or* not available → parked for future consideration with a written rationale.

  *Cost test (the cheap-capture filter):* a candidate field is in-scope for capture only if capture cost is below threshold (e.g. "no new external API calls beyond what's already authorised; only fields already passing through existing API responses or trivially extractable from existing scrapers"). Expensive captures are parked, not adopted.

  *Multi-domain coverage.* Racing AND sports are treated as parallel work-streams with the same methodology. The existing AFL Edge work and racing-ev-model design notes feed in directly — the scan absorbs prior thinking rather than redoing it.

  *Time-box.* The scan is time-boxed to **two sessions of work** (covering racing + sports). If two sessions isn't enough for both, the operator decides whether to extend the box or split (racing scan first, sports scan second). The scan never opens-end. Whatever doesn't make the cut by the time-box closes is parked.

  *Capture-only constraint.* This is capture decisions only — **no analytics design happens here**. The analytics layer remains deferred and out of scope. Captured fields preserve future optionality; designing what to do with them is a later phase. The principle is the DR-026 cheap-capture principle applied at the race-data and sports-data layers: capture cheaply now, preserve analytical optionality for questions we haven't asked yet.

- **Data API contract versioned and documented.** v3's `vps_client` interface is specified against the locked contract. Schema-drift discipline (DR-028 forbidden pattern 3) is now operationally meaningful because there is a documented contract to drift from.

**Scope limits:**

This DR covers data-layer work scoped to v3's needs as locked across Slices 1–6 plus the cross-DB integration governance (DR-027 / DR-028 / DR-026 amendment). It does **not** cover:

- **Analytics layer formalisation.** Deferred. Out of scope for this phase. Cheap-capture fields per the data review are captured; analytics queries against them are not designed here.
- **Account-isolation layer formalisation.** Deferred (TP-Link MiFi + AdsPower + SOCKS5 remains operator-managed manual workflow). Out of scope.
- **Cloudflare-blocked book scraping** (Sportsbet non-racing, BetRight, Betr, PalmerBet, Dabble). Deferred — operator judgment that this is "an entire project in itself" and not a v3 prerequisite. Out of scope.
- **Any other umbrella-architecture work** beyond the v3 ↔ data layer integration.

These deferred scopes are intentional and operator-confirmed. They do not block v3 build. If they become binding during v3 operating life, they enter the work backlog as their own scoped pieces.

**Sequencing inside the data review (high-level, to be refined in Session 12+):**

1. Reconciliation contract write-up across Slices 1–6, including explicit v3 data-requirements statement (Session 12).
2. Build strategy decision — strangler-fig vs clean break + slice strategy (Session 13). Has data-layer implications because it determines whether v3's `vps_client` builds on top of `bethub-v2/vps_client.py` or designs from scratch.
3. First multi-agent governance review — assesses data-layer-first sequencing decision and v3 data requirements doc (Session 14). Decision-under-review document drafted collaboratively (operator + Claude) mid-Session-12 or Session-13.
4. Data review scoping — structured audit template covering the items above, checklist per data type, sub-questions per checklist item (Session 15).
5. Pre-execution governance review — operator go/no-go on data review scope before any execution begins.
6. Data review execution — extensions built, tested, documented, contract versioned. Per-extension governance check before each significant change. External analytics scan time-boxed to two sessions of work within this phase.
7. Final data layer lock review — confirms API contract is locked, `vps_client` interface is specified, data layer is fit-for-purpose. This is the gate.
8. v3 build begins.

**Tradeoffs:**

- **Cost:** v3 build is deferred by the duration of the data review and extensions. Measured in sessions, possibly several weeks. Operator accepts this cost as structural insurance against v2-shaped failure modes; explicitly prefers slow-and-solid over fast-and-fragile ("time spent now is time saved later, likely with dividends").
- **Risk:** Some v3 data requirements may only become visible during v3 build, not surfaced in the review. Mitigation: review is scoped to what's understood from Slices 1–6, not "perfect data layer." Gaps surfacing during build are bounded by DR-028 (extensions go through the integration module, no in-place caching, no second integration point), so build-time discoveries don't compound into v2-shaped messes.

**Date:** 2026-04-28

**Amendment 2026-06-25 (Session 191):** Two clauses in this DR's "what fit for purpose means concretely" list are **superseded by DR-033 (Data-source roles, 2026-06-22)** and must not be read as current:

- "**Race results coverage is confirmed canonical for v3 auto-settlement** — v3's `bet_settled` settlement logic reads VPS race results via `vps_client` …" (in the race-data-coverage bullet); and
- "**VPS race result is canonical for 'what happened in the race'** (auto-settlement reads from here)" (in the settlement-model-simplification bullet).

Both reflect the pre-Session-174 design assumption that v3 auto-settlement would read finishing positions from the VPS / Racing-API analytical line. DR-033 overturned this: **live settlement is Betfair-only** — `settlement.py` resolves win/lose purely off the bet's Betfair market + selection and reads no finishing position or other analytical data (confirmed S174). **Place / ordinal settlement (Safety Net 2nd–4th) stays a manual operator flag**; auto-settling it is deferred, not declined, gated on (a) free bets being layable in-tool and (b) a DR-027/028 boundary call on whether the operational engine may read the analytical source for a placing. The Racing-API finishing-order data captured into `capture.db` is **analytical-line only** (enrichment / future analytics), never in the live settlement path. The race-data-coverage *capture* requirement in this DR still holds — what is superseded is only the claim that settlement reads it.

**Cross-references:** DR-033 (the controlling role split); `data_sources.md` (Part 2 role table; Part 3 deferred auto-settle); DR-027 / DR-028 (the operational/analytical boundary this keeps clean); Session 174 (finish-position pipeline diagnosis); Session 191 (governance-hygiene flag).


---

## DR-030: V3 repo layout and module-boundary discipline

**Status:** Architectural decision. Locked Session 79 as part of pre-build scoping for v3 build proper.

**Why:** v3 build proper is unblocked post-DR-029 close (Session 78). Before any code is written, the repo layout and the import-graph rules need to be locked architecturally so they don't drift across the build sessions. v2's structural debt traces partly to absent import-graph discipline — over 18 months of v2 development, every module came to import every other module, and refactoring became expensive. v3 starts fresh with clean module boundaries and codified import rules from day 0.

This DR captures both halves of the same architectural decision: (a) the top-level folder layout, and (b) the directed-graph import rules that prevent the layout from rotting back into spaghetti as the codebase grows.

**Locked stance — top-level layout:**

```
bethub-v3/
├── clients/              # External integration boundary modules
│   ├── vps_client/       # Read interface against capture.db
│   └── betfair_client/   # Operational interface vs Betfair
├── store/                # v3 operational store
│   ├── schema/           # SQL DDL, migrations
│   └── repositories/     # Read/write data access layer
├── domain/               # Pure business logic
│   ├── bets/             # Bet entry, validation
│   ├── settlement/       # Settlement worker
│   └── pricing/          # Live pricing cache
├── workflows/            # Operator-facing workflows
│   ├── bet_entry/        # Write surfaces
│   └── burst_review/     # Burst Review workflow
├── ui/                   # Frontend
├── ops/                  # Cron, scripts, deploy
├── contracts/            # Locked contract files (relocated from dr029/)
└── tests/                # Test harness
```

**Locked stance — import-graph rules (strict directed graph, arrows go down only):**

```
ui/, ops/        →  workflows/, domain/, store/, clients/
workflows/       →  domain/, store/, clients/
domain/          →  (nothing — pure)
store/           →  (nothing — pure data access)
clients/         →  contracts/
contracts/       →  (nothing — leaf)
tests/           →  anything (test harness sees the whole tree)
```

**Reasoning per layout band:**

- **`clients/` as the boundary layer.** `vps_client` and `betfair_client` are the two locked v1.0 contracts (per DR-029 close-out); they sit at the integration edge and nothing else in the codebase imports past them to reach external systems. This is DR-028 (the cross-database integration boundary discipline) made structural at the folder level — the one-file boundary lives at the folder boundary too.

- **`store/` separate from `domain/`.** The operational store (schema + repositories) is data-access; domain logic (bets, settlement, pricing) is business rules. v2's structural debt traces partly to mixing these — repository methods grew domain logic over time. v3 keeps them separate from day 0.

- **`domain/` is pure.** No DB access, no external API calls. Takes inputs, returns outputs. Tested in isolation. This is where regression test coverage (DR-029 close-out debt 1 — "no test coverage") lands first because it's the cheapest place to test.

- **`workflows/` as the orchestration layer.** Bet entry isn't a domain concept — it's a workflow that calls clients, calls domain logic, calls the store. Burst review is similar. Keeping workflows separate from domain prevents the domain layer from accumulating orchestration concerns.

- **`ui/`, `ops/`, `contracts/`, `tests/` self-explanatory.** UI and ops sit at the top — both can reach all the way down if needed but cannot orchestrate each other. Contracts are leaf (the locked v1.0 contract files). Tests see the whole tree.

**The two rules that hurt the most to enforce but pay back biggest:**

1. **`domain/` imports nothing.** Tempting violation: a domain function "just needs to read one row from the store to check something." The right answer is the workflow reads the row and passes it in. Painful in the moment, free downstream. v2's hardest-to-test code is the code that mixed domain logic with DB calls — v3 forbids that mix structurally.

2. **`workflows/` cannot import `workflows/`.** Workflows don't call other workflows — they share `domain/` helpers if there's reusable logic, but they don't chain. v2 has workflow-calls-workflow chains that became impossible to reason about. v3 forbids it.

**Enforcement:**

A lint rule via `import-linter` (per DR-031) runs on every commit and fails the build if an import crosses the wrong boundary. This is DR-029 close-out debt 1 substrate (test coverage) but applied to architecture rather than behaviour — the import-graph rules are the first regression-protected surface in v3.

**Layouts considered and rejected:**

- *Flat layout (everything at root).* Doesn't scale past ~5 modules; v3 is ~20+ from day 1.
- *Domain-driven design with bounded contexts as folders (e.g. `racing/`, `sports/`, `accounts/`).* Tempting but premature — the bounded contexts aren't clear yet, and forcing them creates artificial boundaries that get refactored later.
- *MVC layout (controllers/views/models).* v2 is partly this. Doesn't fit v3's data-flow shape; the operational/analytical line distinction (Cat 4 of `standing_instructions.md`) cuts orthogonally to MVC.

**Scope:**

Applies to the v3 build proper repo only. Pre-build artefacts (governance docs in the rebuild folder, dr029 substrate) remain in their current locations until v3 build proper is operational. Contract files (`vps_client_contract.md`, `betfair_client_contract.md`) relocate from `dr029/2_7_api_contract_versioning/` to v3's `contracts/` folder as part of v3 build proper administrative cleanup (relocation completed Session 125 — files now at `bethub-v3/contracts/`).

**Tradeoff:** More upfront architectural discipline before any v3 code is written. Acceptable: the alternative is v2-shaped import sprawl that becomes expensive to refactor 12 months in. The discipline is the protection.

**Date:** 2026-05-04

**Amendment 2026-05-12 (Session 124):** Two clarifications to the locked top-level layout per Findings #12 and #14 from the S123 pre-W14 codebase review.

**Clarification 1 — `workflows/bet_entry/v1/` is the canonical home for `pricing.py` and `settlement.py` (Finding #12).**

The original DR-030 layout placed `pricing/` and `settlement/` as sub-folders under `domain/`. The shipped reality is that `domain/pricing/` and `domain/settlement/` are empty, and the pricing + settlement logic lives in `workflows/bet_entry/v1/`. This amendment locks the inversion as deliberate, not a gap.

Reasoning: pricing and settlement are workflow concerns (they involve orchestration across the integration boundary — reading from `betfair_client` / `vps_client`, writing to `store/`), not pure-domain concerns (which take inputs and return outputs with no I/O). Placing them in `workflows/bet_entry/v1/` reflects the actual data-flow shape. The `domain/bets/` folder retains its pure-type role (bet record dataclasses, validation helpers, no I/O).

Forward-compatible: `pricing.py` and `settlement.py` can be promoted to top-level `workflows/pricing/v1/` and `workflows/settlement/v1/` if and when they grow beyond bet-entry context.

**Clarification 2 — `domain/accounts/` added to the locked layout (Finding #14).**

The shipped repo includes a `domain/accounts/` folder (account types, account-at-book validation helpers) that was not in DR-030's original layout listing. The folder fits the layout's existing structure (pure-type, no I/O) and is added to the locked layout as:

```
domain/
├── bets/         # Bet entry, validation
├── accounts/     # Account, account-at-book types and validation     ← added
├── settlement/   # (Empty in shipped reality — see Clarification 1)
└── pricing/      # (Empty in shipped reality — see Clarification 1)
```

Import-graph rules (DR-030's strict directed graph) apply to `domain/accounts/` unchanged — pure domain, imports nothing.

These two clarifications close the DR-030 §Scope tracking pointer that named the contract-file relocation as the only outstanding administrative cleanup; that relocation also lands at S125 (see DR-030 §Scope — relocation now complete).

---

## DR-031: V3 tech stack — Python 3.12+ / FastAPI / SQLite WAL / SQLAlchemy Core / Alembic / React + TypeScript + Vite

**Status:** Architectural decision. Locked Session 79 as part of pre-build scoping for v3 build proper.

**Why:** v3 build proper needs a locked tech stack before any code is written. v2's stack (Python + Flask + SQLite + React) works at the operator's scale, the operator has muscle memory at the Python + SQLite level (per the standing instruction to query `bethub.db` via `Desktop Commander:start_process` with Python), and the VPS-side `racing-data-capture` is also Python. Locking the stack now prevents drift across build sessions and prevents accidental tech-decisions made under pressure mid-build.

The stack carries v2's choices forward where they work and upgrades where v2's choice is straining or where a fresh start enables a cleaner pattern.

**Locked stack:**

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.12+ | Latest stable, mature type hints, ecosystem coverage for every shape v3 needs |
| Web framework | FastAPI | Replaces v2's Flask. Async-native, OpenAPI auto-generation, type-checked routes prevent ad-hoc-validation drift v2 accumulated |
| Database | SQLite (WAL mode) | Same as v2. Single-operator scale doesn't need Postgres. WAL mode gives concurrent read while write is in progress — load-bearing for live pricing |
| ORM / query layer | SQLAlchemy Core (not ORM) | Composable SQL without ORM domain-leak risk. Repositories write Core queries; no ORM session leaking into domain logic |
| Migrations | Alembic | Standard SQLAlchemy companion. Substrate for DR-029 close-out debt 2 (no migration framework) — landing this from day 0 closes the debt before it accumulates |
| Frontend | React + TypeScript + Vite | Same React lineage as v2. TypeScript catches type errors at compile time. Vite for fast dev builds |
| Streaming | `betfairlightweight` | Mature Python library for Betfair Streaming API. v2 uses it; v3 carries forward |
| Testing | `pytest` + `pytest-asyncio` | Standard Python testing. Substrate for DR-029 close-out debt 1 (no test coverage) |
| Lint/format | `ruff` | Replaces flake8/black/isort. Modern, fast, single-tool |
| Import enforcement | `import-linter` | Enforces DR-030 import-graph rules on every commit |

**Three calls worth flagging explicitly:**

1. **FastAPI over Flask.** Small upgrade, real benefit. v2's Flask works but its routes accumulate ad-hoc validation; FastAPI's type-checked routes prevent that pattern. Operationally invisible to the operator (operator doesn't write framework code); deliberate fresh-start upgrade.

2. **SQLAlchemy Core over ORM.** v2 uses raw SQL strings in places. SQLAlchemy Core is the middle ground — composable queries without the ORM's tendency to leak object models into domain logic. Software-discipline call.

3. **Alembic from day 0.** Closes DR-029 close-out debt 2 (no migration framework) before it accumulates. Small upfront cost, large downstream benefit. Material decision.

**Choices considered and rejected:**

- *Postgres instead of SQLite.* Adds operational overhead (a running database service rather than a file). Single-operator scale doesn't justify it. Reconsider only if v3 ever runs on a remote VPS rather than locally, or if concurrent multi-machine access becomes a requirement.
- *Keep Flask.* No technical benefit to keeping Flask given the fresh start. FastAPI's type-checked routes are a free upgrade.
- *Pure SQLAlchemy ORM.* Domain-leak risk doesn't justify the boilerplate savings.
- *Alternative test framework (unittest, nose).* `pytest` is the Python ecosystem standard; no reason to deviate.

**Scope:**

Applies to the v3 build proper repo only. v2 keeps its own stack. VPS-side `racing-data-capture` keeps its own stack — v3 reads from `capture.db` via the locked `vps_client` v1.0 contract per DR-027/DR-028, the VPS-side stack is not v3's concern.

**Tradeoff:** Some upgrades (FastAPI, SQLAlchemy Core, Alembic) carry small learning costs for any future contributor reading v3's code with v2's stack in mind. Acceptable: the upgrades are deliberate, named here, and each has a clear reason. v3 is a fresh start — carrying v2's choices forward where they work and upgrading where they don't is the right balance.

**Date:** 2026-05-04

**Amendment 2026-05-08 (Session 107):** W7 (the web layer skeleton, shipped Session 106→107 between sessions) was the first session to install specific versions of every frontend library named in the locked stack above. The exact versions Code shipped are recorded here as the substrate baseline — knowing exactly what v3 was built against is governance hygiene, and if something breaks after a future library upgrade, having the baseline pinned lets us diagnose whether the upgrade caused it.

**Backend versions:** Python 3.12.7, FastAPI 0.136.1, pydantic 2.13.3, pydantic-settings 2.14.0 (added W7).

**Frontend versions:** React 19.2.5, React DOM 19.2.5, Vite 8.0.10, TypeScript 6.0.2, React Router 6.30.3, TanStack Query 5.100.9, openapi-typescript 7.13.0 (dev dependency).

**Going forward:** version bumps to any library named here need a fresh decision (a new amendment to DR-031 or a separate DR), not a silent upgrade between sessions. Patch bumps (e.g. React 19.2.5 → 19.2.6) are routine bug-fix releases and don't need a formal amendment; minor bumps (e.g. React 19.2 → 19.3) and major bumps (e.g. React 19 → 20, Vite 8 → 9) do.


---

## DR-032: Betfair as canonical reference layer for all bet records — bet-record / bet-leg schema, immutable logging-time snapshots, no fuzzy-matching at logging time

**Why:** The Session 42 architectural extension surfaced an operator-driven principle: every bet record in v3 — whether placed on Betfair directly or on a soft book and logged manually — should carry Betfair-side identifiers as the canonical join key. The principle eliminates fuzzy-matching between bet records and the analytical layer at read time and gives the project one consistent reference scheme across operational and analytical lines.

The principle was referenced consistently across ~10 sessions (Sessions 42, 69, 72, 73, 76, 78, the §2.8 brief, the §2.10 brief, project_context.md, standing_instructions.md) but never landed as a numbered decision record or a real architecture heading. References cited `architecture.md §D12` as if a section by that name existed; it didn't. Session 90 closes that governance gap by writing both the architecture sub-section (§A.10, the principle) and this decision record (the locked schema commitment).

DR-032 specifies the schema commitment that makes the §A.10 principle concrete: the bet-record / bet-leg shape, ownership of fields between them, the operator entry paths that inherit Betfair identifiers without fuzzy-matching, and the boundary against Racing API ↔ Betfair joins (which sit in the analytical layer and not at logging time).

**Locked stance:**

**(1) Bet records carry Betfair-side identifiers as the canonical join key.** Every bet record in v3 — Betfair-direct bets, soft-book bets, all four racing strategies, sports bets, single-leg bets, multi-leg same-game multis — carries `betfair_market_id` plus `betfair_selection_id` (or an array of those pairs for multi-leg bets) as the canonical join key into Betfair-sourced data. Fuzzy-matching between bet records and the analytical layer is eliminated by construction.

**(2) Two-table shape: bet record + bet legs.** A bet has one row in the `bets` table (bet record) and N rows in the `bet_legs` table (one per leg, all sharing the bet's `bet_id`).

The bet-record row owns *bet-as-a-whole* properties — fields that exist once per bet regardless of leg count:

- Stake (one stake per bet, regardless of how many legs)
- Soft-book combined price (the SGM combined price the bookmaker quoted, or the single-leg price for non-multi bets)
- Account, book-at-account
- Free-bet flag and promo metadata
- Strategy tag, timestamp, settlement outcome, cash returned

The bet-leg rows own *per-leg* properties — fields that genuinely exist once per leg:

- `bet_id` (foreign key to bets table)
- `leg_number` (ordering — 1, 2, 3, etc.)
- `betfair_market_id`, `betfair_selection_id` (the canonical join keys, different per leg)
- Set B denormalised display fields per leg: `betfair_event_name`, `betfair_market_name`, `betfair_selection_name`, `betfair_event_venue`, `betfair_event_sport`, `betfair_event_start_time` (immutable logging-time snapshots, captured per leg)
- Optionally: the leg's individual Betfair-implied probability at logging time (for SGM correlation analytics)

Single-selection bets are bet records with exactly one leg row. SGMs are bet records with N leg rows. The schema is uniform across both shapes.

**(3) Stake and combined price live exclusively on the bet record. Never on legs.** A three-leg SGM has $50 staked once, not $50 × 3. The legs table has no `stake` column and no `combined_price` column — there is nothing for a query to double-count. This is a structural idempotence rule enforced by the schema, not by convention.

Reporting and P&L queries always read against the bet record, never against legs. "Total staked this week" sums `bets.stake`; the legs table doesn't enter that query. "P&L by strategy" reads `bets.stake` and `bets.cash_returned` grouped by `bets.strategy_tag`; no leg involvement, no double-counting risk.

The legs table is read for one purpose: leg-level analytics — SGM correlation analysis, per-leg join-out for Betfair price history, leg-by-leg settlement audit. These queries are explicitly leg-level by design.

**(4) Set B denormalised display fields are immutable logging-time snapshots.** The Betfair-side display fields captured on each leg row (event name, market name, selection name, venue, sport, start time) are frozen at the moment the bet is logged. They do not refresh if the Betfair-side data changes later. If Betfair corrects a runner name from "Riff Raff" to "Riff-Raff" the day after the bet is logged, the bet leg's denormalised field stays as logged. Anything reading authoritative current Betfair-side data joins out via the identifiers; the denormalised fields are historical fact, not live mirror. This sits cleanly under DR-028 (the no-caching rule): logging-time snapshots are not cache because they don't refresh.

**(5) No resolution logic at logging time. Identifiers inherit from the entry path.** Soft-book bets are logged from one of two screens — racing or sports. Both screens are Betfair-driven; the runner row (racing) or selection row (sports) is already a Betfair `(market_id, selection_id)`-keyed entity. Clicking "log soft-book bet" on a row passes the Betfair identifiers (plus Set B display fields) into the bet-log modal as inherited context. The operator types account, book-at-account, and confirms. The bet record and its leg(s) are written with Betfair identifiers attached. There is no matching, no fuzzy lookup, no resolution step — the identifiers are present from the click onwards.

**(6) Hard rule: soft-book bets must have a Betfair market available at logging time.** There is no fallback path for races or markets where Betfair has no coverage. If Betfair has no market for a race or fixture, that bet cannot be logged via v3's normal write path. This is a deliberate scope decision — the rule keeps every bet in the system joinable. Edge cases (Australian non-metropolitan harness pre-Betfair-market-open, low-tier greyhound, some pre-pre-post Saturday metro before markets open) fall outside scope for the foreseeable future.

**(7) Racing API ↔ Betfair joins are not at logging time.** The Racing API is analytical-line only. Bet records carry only Betfair identifiers. When v3 needs Racing-API-sourced context for a bet (form, trainer history, track condition for thoroughbred bets), the join goes through `capture.db`'s internal Racing-API ↔ Betfair resolution layer:

bet record (Betfair `market_id`) → resolution table (in `capture.db`) → Racing API record

The fuzzy match between Racing API and Betfair is owned by capture.db's analytical layer — addressed by code reading both sources post-hoc, producing a resolution table with confidence flags. Low-confidence matches are surfaced for operator review. Unresolvable cases stay flagged. This matching layer can be improved over time without touching bet records.

Racing API covers thoroughbreds only; harness and greyhound bets join only to Betfair-sourced analytics (no Racing API enrichment is available for them, which is a known limitation, not a defect).

**(8) Multi-leg correlation analytics fall out for free.** Each bet leg captures the Betfair-implied probability at logging time. Multiplying the leg probabilities (under independence assumption) gives an "if uncorrelated" combined probability. The bet record's soft-book combined price gives the bookmaker's "with correlation" combined probability. The ratio is the bookmaker's implied correlation. This signal is the EV foundation for Strategy 3 (Correlated Friction); the schema captures it natively without bolt-on later.

**Choices considered and rejected:**

- *Set A (minimal — just market + selection IDs, no denormalised display fields).* Rejected because operator UX would require a Betfair join on every bet-record read just to display what the bet was about. Set B's logging-time snapshots are cheap to capture and make bet records self-readable.
- *Set C (full Betfair envelope — every market metadata field captured at logging time).* Rejected as over-broad. Most of the heavy metadata (commission rate, market type, country code, race code) is already in capture.db's analytical layer; duplicating it on every bet record violates DR-028's no-denormalisation discipline without adding operational value.
- *Single-table bet schema (no legs table; SGMs as serialised JSON or denormalised columns).* Rejected because it makes correlation analytics structurally harder, breaks query uniformity between single-leg and multi-leg bets, and creates the double-counting risk that the two-table schema eliminates structurally.
- *Single-selection-only v1, SGMs deferred to a later DR.* Considered but rejected. The two-table shape supports both natively at the same cost; deferring SGMs would later require a schema migration when Strategy 3 work begins. Better to lock the right shape now.
- *Rules-based Racing API ↔ Betfair matching at logging time.* Rejected. Fix 5's experience (venue harmonisation, ~784 cleanly-resolvable cases out of 1,332 in the v2 data) demonstrates that rules will always lag the data. Capture-then-match-later defers the matching to where the most context is available.
- *Resolution logic in the bet-entry workflow (fuzzy-match against Betfair markets at log time).* Rejected. Reintroduces fuzzy-matching at logging time, which is exactly what the canonical-source principle eliminates. The racing-screen and sports-screen entry paths already inherit Betfair identifiers cleanly; no resolution step is needed.

**What this means concretely:**

- The `bets` table schema includes `bet_id`, `account_id`, `account_at_book_id`, `stake`, `soft_book_combined_price`, `is_free_bet`, `promo_id` (nullable), `strategy_tag`, `created_at`, settlement fields, etc. **No Betfair identifiers on this table.**
- The `bet_legs` table schema includes `bet_id` (FK), `leg_number`, `betfair_market_id`, `betfair_selection_id`, denormalised Set B display fields, `betfair_implied_probability_at_log_time` (nullable). **No stake or combined-price fields.**
- A single-selection bet writes one `bets` row plus one `bet_legs` row. An N-leg SGM writes one `bets` row plus N `bet_legs` rows.
- Bet-entry from racing screen: operator clicks runner row → modal opens with Betfair `market_id`, `selection_id`, and Set B display fields pre-populated → operator enters account, book-at-account, soft-book price (single-leg) → confirms → bet record + one leg row written.
- Bet-entry from sports screen: same shape, with the row being a sports market selection rather than a racing runner. SGM bet-entry is a multi-leg variant of the same flow — operator selects multiple legs from the sports screen, modal opens with N legs pre-populated, operator enters the SGM combined price quoted by the bookmaker → confirms → bet record + N leg rows written.
- When v3 reads "what was this bet about" for display, it reads the bet record plus its leg(s) — the denormalised display fields render directly without a Betfair round-trip.
- When v3 reads "what's the current Betfair price for this leg," it joins from the leg's `betfair_market_id` + `betfair_selection_id` to live `betfair_client` data or to capture.db's analytical store.
- When v3 reads "what's the form profile for this thoroughbred bet," it joins from the leg's `betfair_market_id` to capture.db's resolution table to the Racing API record. The resolution layer handles the fuzziness.

**Tradeoffs:**

- Two-table schema is one extra join compared to a flat bet record. At v3's scale (single user, tens of thousands of bets per year), the cost is structurally trivial — SQLite handles the join in microseconds. The schema clarity and idempotence guarantees are worth far more than the join cost.
- Logging-time snapshots (Set B fields) duplicate display data that lives canonically on Betfair. The duplication is bounded — the snapshots are immutable, never refreshed, never reconciled, and live only on the bet leg. Cost is one-time capture at logging time; benefit is bet records remain readable years later without round-tripping to Betfair (which may have aged-out the market entirely).
- The hard rule (soft-book bets must have a Betfair market) rules out edge cases. Acceptable scope decision; the alternative (carrying a fallback path with no canonical identifiers) breaks the join discipline that DR-032 exists to enforce.
- Racing API context for non-thoroughbred bets is unavailable. Acceptable; Racing API is thoroughbred-only by source, and harness / greyhound analytics through Betfair-sourced data is sufficient for v3's foreseeable use cases.
- The `bet_legs.betfair_implied_probability_at_log_time` field is captured per leg even when correlation analytics aren't being used. Cheap-to-capture, expensive-to-reconstruct (the field requires Betfair pricing at logging time, which is gone by the time analytical work starts). Following the principle from §2.8: cheap-to-capture / expensive-to-reconstruct fields earn day-one capture even if their consumer is downstream.

**Why this is the right pattern:**

The decision puts the canonical-reference discipline at the schema level rather than at the application level. The schema cannot represent a bet without Betfair identifiers (the `bet_legs` table requires them). The schema cannot double-count stake (the `stake` column lives only on `bets`). The schema cannot accumulate Racing API identifiers on bet records (there are no columns for them). The architectural principle is enforced by structure, not by code review or developer discipline. This is the same pattern DR-027 / DR-028 use for the cross-DB boundary — make the right thing structurally easy and the wrong thing structurally impossible.

The decision also defers the harder problem (Racing API ↔ Betfair identity reconciliation) to where it belongs (capture.db's analytical layer, code-driven, post-hoc, with operator review for low-confidence matches). The bet-record write path stays clean; the analytical layer carries the resolution complexity.

**Scope:**

Applies to all bet records in v3 — Betfair-direct, soft-book, racing, sports, single-leg, multi-leg, all four racing strategies. Does not apply to v2 bet records (v2 retains its own schema; no migration). Does not apply to capture.db's analytical-layer records (capture.db keeps its existing identifier scheme; the canonical-source rule is about bet records, not about analytical data).

Implementation lands during W4 (the Betfair hedge-entry workflow), W4.1 (the soft-book entry path), and W6 (the operational store schema). W7 (UI) lands the racing-screen and sports-screen entry paths against the schema. The math review at `dr029/w4_bet_entry/hedge_staking_math.md` is the substrate for W4 brief drafting; DR-032 is the schema substrate for W4 / W4.1 / W6.

**Cross-references:**

- `architecture.md` §A.10 (canonical source identifiers — the architectural principle DR-032 implements).
- `architecture.md` §A.8 (cross-DB integration boundary — the discipline DR-032 sits under).
- DR-027 (two-database architecture — bet records own operational state; capture.db owns analytical).
- DR-028 (integration boundary discipline — no caching, no denormalisation, no second integration point; logging-time snapshots are exempt because they're immutable historical fact).
- DR-026 (at-log-time market snapshot pattern — Set B's denormalised display fields follow this principle at the per-leg level).
- DR-022 (account / book / account-at-book vocabulary — used in bet record fields).
- DR-019 (derived state on read — bet records store events, not derived state; settlement outcomes derive from bet_settled events plus capture.db / Betfair joins).
- `dr029/2_8_bet_schema/2_8_bet_schema.md` (the bet-schema reframing brief — DR-032 makes the §10.2 load-bearing contract concrete and closes the §10.3 carry-forward "architecture.md §D12 sub-section update").
- Session 42 (the original surfacing of the architectural extension flag).

**Date:** 2026-05-06

**Amendment (Session 180): the promo link is the single-level catalogue serial, not a per-instance row.**

The "what this means concretely" clause above named a nullable `promo_id` on `bets` as the promo link, pointing (per the `promo` domain docstring) at the per-instance `promo` row. That instance link was documented but never built (Session 179 review). Sessions 178–179 locked a single-level promo model; this amendment makes it concrete:

- The bet's promo link is `bets.promo_template_id` (nullable TEXT, soft reference) — it points at the kind-catalogue serial (`promo_template.promo_template_id`), not the per-instance `promo` row (which carries book + run-window). The catalogue row holds the promo's structured terms (refund positions, free-bet-vs-cash, return %, cap); the bet stores only the serial.
- Rationale: book is already on the bet (`bet_legs` identifiers + `account_at_book_id`), and promos mature at the event, so there is no per-bet run-window to model.
- The promo/adjusted EV at log time persists alongside as `bets.promo_ev_at_log` (nullable REAL).
- This reinforces, does not replace, the canonical-reference schema commitment above: legs still carry Betfair identifiers as the canonical join key; the promo serial is an additional single-DB operational reference (the v3 operational store), not a cross-DB or analytical join.

Built in Build 1 (promo-attach foundation), per `interface_triage/promo_attach_build1_brief.md`. Does not change the two-table shape, leg ownership, or the no-fuzzy-matching discipline.

**Amendment date:** 2026-06-23

---

## DR-033: Data-source roles — Betfair is operational, The Racing API is analytical/enrichment

**Why:** Across 174 sessions the project has repeatedly re-derived which of its two live data sources — Betfair (free, real-time, operational) and The Racing API (paid, periodic, enrichment) — does which job, because the two overlap in capability and the decision lived only in scattered session memory. Session 174 surfaced the confusion directly: diagnosing why finishing positions stopped landing raised the questions of which source should settle, which should enrich, and how sports fit. This DR locks the role split so it is re-encountered at session open rather than re-decided from memory. Capability detail (what each source *can* do) lives in `data_sources.md`; this DR locks what each is *used for*.

**Locked stance:**

**(1) Betfair is the operational source.** Live pricing, bet placement, win/lose settlement, and bet/event identity all run off Betfair. Confirmed S174: v3 `settlement.py` settles purely off the bet's Betfair market + selection (WINNER→won, LOSER→lost) and reads no analytical data, no finishing position.

**(2) The Racing API is the analytical / enrichment source, racing only.** It supplies finishing positions, margins, form, pedigree, career stats, and a BSP cross-reference across all races, feeding the (not-yet-built) analytical layer. It is never in the live settlement path.

**(3) Place / ordinal settlement (Safety Net 2nd–4th) stays manual.** The operator flags the trigger. Automating it would require the operational settlement engine to read an analytical source for a placing — which crosses the DR-027/028 boundary — and depends on free bets being layable in the tool, which does not yet exist. Deferred, not declined.

**(4) Sports settlement = Betfair; sports enrichment = a future separate subscription.** Betfair settles sports win/lose exactly as it does racing. The Racing API carries no sports, so equivalent sports enrichment depth, if wanted later, is a future separate data subscription — not owed before sports lands.

**The rule underneath:** Betfair settles and operates; the Racing API enriches and feeds analytics. Where both *could* do a job (the Racing API could settle a place refund; Betfair holds BSP and price history), the job still goes to one owner by this rule. Overlap is capability, not shared duty.

**Scope / what this is not:** A usage-role decision, not a schema or boundary change. It sits on top of DR-027/028 (the two-database boundary) and DR-032 (Betfair as canonical reference for bet records) without altering them. The analytical layer's own design stays deferred to its future project; this DR only fixes which source feeds it.

**Deferred (named so they don't drift):** auto-settling Safety Net place refunds (depends on in-tool free-bet laying + a DR-027/028 boundary call); a sports-enrichment subscription; the analytics spec itself.

**Cross-references:**
- `data_sources.md` (capability detail + the role table this DR locks).
- DR-027 / DR-028 (two-database architecture + integration boundary — the operational/analytical line this role split keeps clean).
- DR-032 (Betfair as canonical reference for bet records; Racing API analytical-line only, thoroughbred coverage).
- DR-029 (data-layer fit-for-purpose — the results-coverage assumption this session re-examined).
- `external_api_resources.md` (where each API's specs/URLs live).
- Session 174 (the finish-position pipeline diagnosis that surfaced the role confusion).

**Date:** 2026-06-22


---

## DR-034: Canonical race identity — the Betfair WIN market is the spine; capture-store fragments resolve by completeness, not row id

**Why:** Brief 1.1 surfaced that 87% of market-bearing capture rows
share their `betfair_win_market_id` with ≥1 other row, because the
capture store's natural key `(race_date, venue_normalised,
race_number)` fragments one physical race into many rows (both
components drift across the two ingest paths). BetHub had no defined
cross-source race identity, so "which physical race is this" had no
deterministic answer, and the shipped by-market route's "first by id"
tie-break returns an empty discovery shell in the dominant case. This
DR locks the identity model so every future data consumer keys races
the same way.

**Locked stance:**

1. **The Betfair WIN market id is the canonical identity of a physical
   race** wherever a Betfair market exists — the one field invariant
   across all fragments of a race; consistent with DR-032. Runner
   identity is `(WIN market_id, selection_id)`; the Betfair `event_id`
   parents a race's WIN + PLACE markets.
2. **The capture store's `races.id` is not a race identity** — it is a
   per-fragment row id and must never be used as one (the trap "first
   by id" fell into).
3. **Races with no Betfair market take a second-class, analytical-only
   identity:** `(scheduled_start→Adelaide-local date, canonical venue,
   race number)`. The operational/earning path never relies on it
   (DR-032 §6 requires a Betfair market at logging time; DR-033 settles
   off Betfair).
4. **Fragment-collision resolves by completeness, not row id.** Among
   capture rows sharing a WIN market id, the authoritative fragment is
   the most-complete one (resolved status → most runners → results
   present → most recent), superseding the Brief 1.1 `ORDER BY id`
   tie-break. Target end-state: collapse fragments under the market id
   at read time and enforce identity at write time (remediation,
   specified in §C/§D + roadmap, not executed by this DR). **The
   placings-recovery backfill lands Racing-API finishing positions on
   natural-key fragments via the subscription path, so its results are
   a primary producer of the cross-sibling data this read-time collapse
   must union — and are only fully spine-reachable once that collapse
   runs (S206 backfill review).**
5. **Per-source native keys map onto the spine** as in §B.3. The
   Racing-API race id is not currently persisted (the subscription path
   collapses it into the natural key); recording it is a named
   remediation item.

**Scope / what this is not:** A definition, not a build. This DR fixes
how races are identified and reconciled; it does **not** change any
schema, ingest path, or the live earning path, and commissions no code.
Schema/ingest remediation is specified separately (§C/§D + roadmap) and
executed under its own briefs. Bet-safe: analytical/governance only.

**Cross-references:**
- `BETHUB_DATA_REFERENCE.md` §B (the full identity & reconciliation
  model this DR summarises).
- DR-032 (Betfair canonical reference — the spine builds on it).
- DR-033 (source roles — keeps the no-market identity analytical;
  the placings backfill is the Racing-API analytical line in practice).
- DR-027 / DR-028 (two-DB boundary — identity by reference, no
  caching).
- `vps_endpoint_enrichment_report.md` §4 (the duplication anatomy,
  market `1.259530858`).
- `race_date_semantics_report.md` (the fragmentation mechanism).
- `placings_landing_fix_report.md` (S198 — the RC-2 write-side guard
  applies this DR's principle at runner level: match on horse identity,
  never the bare saddlecloth number).
- `recovery_run_report.md` (S201 — the nightly backfill landing
  positions on natural-key fragments; deficit-floor caveat per S206
  review).
- Brief 2 (`vps_client_api_rewrite_brief.md`, re-locks against this
  identity).

**Date:** 2026-06-30 (Session 206 — locked from the §B draft after the
backfill cross-check).
