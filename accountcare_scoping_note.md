# AccountCare — account-health scoping & feasibility note

**Status:** EXPLORATORY / informal — **not** a formal BetHub session. No code
touched, no money path involved, nothing committed to build.
**Date:** 2026-07-23 (Thu), Adelaide.
**Author:** Claude (exploratory session with Tim), outside the S-numbered sequence.
**Purpose:** Assess feasibility and cost/benefit of three operator ideas for
account-health work, and leave a clean pickup for when this folds into a formal
session.

> **How to pick this up in a formal session.** This note is the entry point. It
> maps three operator ideas onto the already-named **AccountCare** satellite and
> the vocabularies DR-022 reserved. A formal session commissioning AccountCare
> cycle-1 should start here, then read the anchors in §2. Nothing here is a build
> commission — it is scoping. Operator sign-off gates any build.

---

## 1. The three ideas (operator's words, condensed)

1. **Longevity strategy.** Don't eke $10 EV/week forever — prefer accounts that
   survive months while extracting a lot. i.e. how to keep books from flagging
   you for as long as possible. Operator flagged reviewing law/literature on
   optimal account-health strategy.
2. **The "gold standard" tool.** An agent per AdsPower profile that monitors
   *all* traffic — TAB/bookie hits, general browsing, bets placed via BetHub —
   and nudges: "not enough general browsing, go read news/YouTube," "you're
   hitting Sportsbet a lot, looks suspect," "you've laid a lot of promo bets
   with this book — ease off with a couple of mug-punter bets." Ideally AdsPower
   exposes traffic so the per-profile picture is complete.
3. **Fresh-account onboarding.** A clean account is about to be activated under a
   new holder, **Mads** (email aged with Gumtree/ABC/eBay traffic, single fresh
   mobile-data IP). Good chance to *start the account-health dataset*. Open
   questions: stagger signups vs all-at-once, and the "bleed-in" ramp before
   taking EV bets.

---

## 2. The key finding: all three are AccountCare, and AccountCare is already reserved in governance

These three ideas are not new territory to invent from scratch. They map exactly
onto a satellite the project has already named and a set of data vocabularies
governance has already reserved but deliberately left unlocked. **The three ideas
together are, in effect, AccountCare research cycle-1** — the work that locks
those vocabularies.

**Anchors (canonical, read these first in a formal session):**

- **`vision.md` — the constellation.** AccountCare is a named **planned
  satellite**: *"Behavioural account-conditioning lifecycle — keeping
  book-at-accounts healthy across betting patterns, withdrawal cadence, account
  age, and bookmaker-side signals."* BetHub core carries only *"primitive
  account-health visibility … with sophisticated treatment living in AccountCare."*
  RouteHub (network isolation) is the satellite ahead of it; AccountCare is next
  after RouteHub in the stated build order.

- **DR-022 (via `w11_accounts_brief.md` §1.2–§1.3) — the reserved vocabularies.**
  DR-022 already names **tier** and **phase** as `accounts_at_book` properties —
  *"tier and phase are tracked, and conditioning happens."* W11 shipped
  **identity-only** and deferred them because the vocabularies aren't locked:
  - **tier** = limiting-state values (clean / restricted / closed / …)
  - **phase** = lifecycle stages (onboarding / conditioning / mature / …)
  - **state-transition rules** = what moves an account-at-book between values,
    and *who or what writes the transition*.
  Adding these is a *small additive migration* — the schema module already
  provisions the `_add_column_if_missing` pattern for exactly this
  (`store/schema/accounts.py`). **The three unlocked things in W11 §1.3 are the
  precise output target of an AccountCare research cycle.**

- **DR-029 §3.3 — account isolation deferred, not dismissed.** Account-isolation
  formalisation is out of scope for DR-029 as *"an entire project in itself,"*
  and infra↔account linkage (MiFi/SIM/AdsPower profile → account-at-book) is
  named as *"a future concern … decided in a separate DR or amendment."* So the
  door is explicitly left open; this note is early input to that DR.

- **`work_in_progress.md` item 18 (Session 50) — onboarding pre-work already
  thought through.** Directly covers idea #3's foundations: pre-warming AdsPower
  profiles + aged email accounts, and the compounding value of (a) email age,
  (b) profile cookie/local-storage maturity, (c) SIM/IP usage history. **Carries
  the key warning for staggering:** profile browsing patterns must *differ*
  between profiles (sites, times of day, cadence) or *"statistical clustering at
  the books' fraud-vendor side links them despite individual fingerprint
  cleanness."* Estimated ~2–3 h setup + ~30 min/week warming per profile.

- **`browse-baseline/build_spec_v3.md` — idea #2's behavioural capture layer,
  already designed.** A passive Manifest-V3 browser extension + Flask/SQLite
  receiver that records browsing behaviour (dwell, scroll, click, typing cadence,
  mouse paths, session shape, site-category transitions). Explicitly names its
  own **Layer 3a = conformance scoring / guidance** and **Layer 3b = automated
  persona browsing**, feeding a *"BetHub AccountCare"* consumer via versioned
  persona artefacts. **This is the "gold standard" tool's behaviour half, spec'd
  in April.** ⚠️ **Status: spec only — not built.** The directory contains just
  the spec; no `server/`, `extension/`, or `data/`.

- **`router-sim/` — idea #2's traffic-capture chokepoint, already live.** The
  Pi 5 gateway runs **one `3proxy` SOCKS5 instance per SIM**, and one SIM is
  permanently dedicated to one account (a "four pillars" discipline). **This is
  the unlock for idea #2:** every AdsPower profile's traffic already egresses
  through a dedicated, per-account proxy lane. See §4.2.

- **Account schema (`bethub-v3/store/schema/accounts.py`).** `accounts` (real
  people — Tim, Kate, Sarie, and soon Mads), `books` (with an
  **`ownership_cluster`** TEXT field), `accounts_at_book` (the health unit).
  `ownership_cluster` matters for account health: limiting commonly propagates
  across a parent company's books, so a per-book tier is not enough — cluster is
  a first-class health dimension.

- **`project_context.md` — strategies already carry account-health profiles.**
  Each of the four racing strategies is framed by its account-health profile:
  Strategy 3 (price-uplift/bonus) has the *"best account-health profile … the
  bet shape looks like ordinary punting"*; Strategy 4 (value/synthetic each-way)
  is *"god-tier for account health because the bet shape is statistically
  indistinguishable from sharp punting."* So bet-shape-as-camouflage is already a
  live operating concept, not a new one.

- **`decisions.md` — AccountCare already has locked decisions.** Three matter for
  these ideas:
  - **DR-009:** AccountCare is v3 operational-layer scope; *"conditioning
    protocols and cluster awareness are how accounts stay alive."* Promo-allocation
    as an *"EV × longevity decision"* / *"per-book longevity model"* is deferred
    to v4.
  - **DR-015: three-tier AccountCare alert severity is LOCKED** (red = imminent
    ban/regulatory; amber = affects the next bet decision; yellow = informational),
    with interrupt/visibility behaviour fixed and only the *thresholds* deferred
    to the data-model work. **This is the severity spine idea #2's nudges already
    have to fit.**
  - **Health scores are derived / computed-on-read, not stored** (single-source-of-
    truth rule). A hard constraint on how idea #2 is designed.
  - **Bookmaker hygiene rules** are a decided table shape — per bookmaker: target
    weekly turnover, preferred odds bands, frequency expectations, restriction
    triggers — with populating it named as *"a substantial knowledge-capture
    task."* **This is the decided home for idea #1's policy output.**

- **`architecture.md` — AccountCare warning plumbing already exists in the event
  schema.** `promo_events` (W13) carries `accountcare_warning_raised` /
  `accountcare_warning_cleared`; there's a `warning_catalogue` reference table;
  bets snapshot `active_warnings_at_log` (JSON) *"for outcome-vs-warning
  analysis"*; and an *"AccountCare action queue"* is named as a post-day-one
  operator workflow. So idea #2's nudge engine has more scaffolding to plug into
  than a greenfield build.

- **`operator_workflow_map.md` — current cover behaviour is already documented.**
  Under "Account-health behaviours": spreading runners across accounts, and
  *"cover browsing — an article, some site activity — after a bet."* This is the
  manual practice idea #2 would systematise/monitor.

- **`bethub-analytical/race-price-pressure/cycle3_tab_leadlag/` — a fresh (S250)
  law/literature strand already exists.** An operator-commissioned research cycle
  that already did a real law/forum/academic sweep bearing on account health (see
  §3.1). This is the operator's flagged "review law/literature" already partly
  done — idea #1 extends it, it doesn't start from zero.

**Consequence for framing:** a formal session shouldn't treat these as three
disconnected experiments. They are one thing — **AccountCare cycle-1** — with a
shared output (locked tier/phase/transition vocabularies + a starter dataset) and
a shared bottleneck (§5: no ground-truth data yet).

---

## 3. Feasibility & value — one section per idea

Scoring is coarse (Low/Med/High) and deliberately conservative. "Value" is
cost/benefit to the operation, not raw upside.

### 3.1 Idea #1 — Longevity strategy (the policy layer)

**What it actually is:** not a build — a *research + policy* deliverable. It's
the account-health **objective function** and the playbook the other two ideas
serve. Everything in idea #2 (what to nudge) and idea #3 (how to onboard) is
downstream of decisions made here.

**Feasibility: HIGH** (it's research/writing, no engineering dependency), and
**partly already done.** The S250 `cycle3_tab_leadlag/` research already ran a
real law/forum/academic sweep with findings that bear directly on longevity:
- **The crucial reframe — the win channel is MBL-protected.** Australian
  minimum-bet-limit law (Racing NSW/VIC; ~$2,000 metro / $1,000 country win
  protection) means books largely *cannot* refuse a win bet at advertised odds.
  So *what flagging actually costs is **promo eligibility** — the operation's
  lifeblood — not the win itself.* This reshapes idea #1's objective function:
  longevity is about **protecting promo access**, and camouflage exists to keep
  the promo tap open. A formal session should make this the top-line framing.
- **A real exposure to name:** the "bowler / betting on behalf of others"
  integrity carve-out is a genuine multi-account-operation risk flagged in that
  research — worth an explicit line in the policy.
- Camouflage is already elevated there to a **"first-class model constraint"**
  (round stakes, timing jitter — not always the last bet before the fluc, spread
  across books/accounts), and practitioner evidence is cited (e.g. value/arb
  accounts gubbed fast; restricted accounts far likelier to be in profit).

What remains gatherable and not yet done: bookmaker T&Cs / closure clauses per
book, public writing on bookmaker fraud/risk vendors (IP reputation, device
fingerprinting, bet-pattern profiling, withdrawal-cadence flags), and a
systematic mug-bet / sport-mix camouflage spec (a named gap — no such spec
exists). The operator explicitly flagged wanting this review; it's a well-trodden
domain and the strand is already open.

**Value: HIGH, foundational.** The operator's own framing is the whole ROI
argument: an account that survives months at high extraction beats one that
yields $10/week until it's limited early. A written, testable longevity policy is
what converts idea #2's nudges from guesses into a rule set, and gives idea #3's
onboarding a target. Without it, #2 and #3 are building instruments with no scale.

**Cost: LOW–MED.** Mostly research + synthesis time. Output is a policy doc:
the tier/phase vocabularies (locking DR-022's reservation), the signals books are
believed to weight, the levers the operator controls (bet mix, stake shape,
timing, withdrawal cadence, mug-bet ratio, sport diversification, session
hygiene), and — critically — **which of those are measurable in BetHub today vs
need new capture.**

**Recommendation:** Do this **first**, as a standalone research doc, before any
build. It is cheap, it unblocks the other two, and it produces the DR-022
vocabulary lock as a side effect. One honest caveat to hold: much of the
"literature" is community lore and vendor-opaque — treat it as **hypotheses to be
validated against the operation's own dataset (§5)**, not settled fact. That
tension is itself the argument for starting the dataset now (idea #3).

### 3.2 Idea #2 — The "gold standard" per-profile monitor + nudge

**What it actually is:** a sensing-and-advice engine per account/profile with
three inputs — (a) **destinations/traffic** (where the profile went), (b)
**behaviour** (how it browsed — the browse-baseline signals), (c) **operational
bets** (what BetHub already knows: strategy tags, promo cycles, book, stake) —
producing nudges against the idea-#1 policy.

**The operator's stated blocker dissolves.** The worry was *"AdsPower would
ideally expose traffic."* It doesn't need to. **Every profile already egresses
through its own dedicated `3proxy` SOCKS5 lane on the Pi, one lane per account
(router-sim).** `3proxy` has native per-connection logging; a lane == an account,
so the proxy is a clean, complete, per-account traffic tap **with no AdsPower
cooperation required.** This is the single most important feasibility finding in
this note. Caveats: SOCKS5h gives destination **host + timestamp + byte counts**,
not page content (TLS) — which is exactly the right altitude for "how much
non-betting browsing vs bookie hits," and is privacy-preserving by construction.

**Feasibility by component:**
| Component | Source | State | Feasibility |
|---|---|---|---|
| Per-profile destination/traffic | `3proxy` lane logs (Pi) | Proxy live; logging not yet turned on/collected | **HIGH** |
| Behavioural signals (dwell, browsing mix) | browse-baseline extension | **Spec only, unbuilt** | **MED** (build exists on paper) |
| Operational bet context | BetHub store (strategy tags, promo cycles, book) | **Live** | **HIGH** |
| Nudge engine (policy → advice) | new | New work, depends on idea #1 | **MED** |
| Per-profile aggregation ("complete picture") | join of the three | new | **MED** |

**More scaffolding exists than "greenfield" implies.** The nudge/warning side is
partly specified already: **DR-015 locks a three-tier severity model**
(red/amber/yellow) that nudges must map onto; `architecture.md` already defines
`accountcare_warning_raised`/`_cleared` events on `promo_events`, a
`warning_catalogue` table, `active_warnings_at_log` snapshots on bets, and an
"AccountCare action queue." So the *output surface* for nudges has a decided shape
— what's missing is the *sensing* (traffic + behaviour inputs) and the *policy*
that decides when to raise which warning. **Design constraint:** health scores are
**derived/computed-on-read, not stored** (single-source-of-truth decision) — the
monitor computes, it doesn't persist a health number.

**Value: HIGH but back-loaded.** This is the tool that operationalises longevity
day-to-day. But its nudges are only as good as idea #1's policy and §5's data —
so its *realised* value trails the other two. It is also the most engineering.

**Cost: MED–HIGH, and multi-component.** Naturally phases:
- **Phase A (cheap, high-signal):** turn on `3proxy` per-lane logging + a small
  collector, and build a per-account traffic summary (bookie-hit share vs general
  browsing, hit frequency by book). This alone answers *"you're hitting Sportsbet
  a lot"* and *"not enough general browsing,"* using infra that already exists.
- **Phase B:** build browse-baseline (the spec is ready) for the behavioural half.
- **Phase C:** the nudge engine + BetHub-side "complete per-profile picture,"
  wiring in operational bet context (mug-bet ratio, promo-lay density per book).

**Recommendation:** Don't build the whole "gold standard" at once. **Phase A is a
strong, low-cost early win** that stands on already-live infra and delivers two of
the three example nudges. Sequence: idea #1 policy → Phase A → reassess. Fold the
"complete picture" ambition into AccountCare proper; don't try to grow it inside
BetHub core (vision keeps AccountCare a satellite).

> ⚠️ **Boundary flag for a formal session.** browse-baseline's own spec sets a
> hard rule: **one-way artefact flow, no cross-DB queries** — `baseline.db` is
> never queried by BetHub; it feeds versioned persona artefacts only. Any
> "gold standard" design must respect that boundary and the vision's rule that
> AccountCare is a satellite, not core. Design the monitor as its own tool that
> *consumes* BetHub's ledger + the proxy logs + baseline artefacts, not as a new
> BetHub-core surface.

### 3.3 Idea #3 — Fresh-account onboarding (Mads) + starting the dataset

**What it actually is:** two things bundled — (a) an **operational playbook** for
bringing Mads online safely (stagger, bleed-in ramp), and (b) the **first
ground-truth entry in the account-health dataset** that §5 says everything else
needs.

**Feasibility: HIGH and available now.** No tooling is required to *start*. WIP
item 18 already reasons through the profile/email/SIM aging and the
anti-clustering discipline. The bleed-in ramp and stagger decision are policy
calls the operator can make and record this week. The dataset can begin as a
simple structured capture (a sheet/markdown log) and be migrated into
AccountCare's tier/phase fields later — the schema reserves them.

**Value: HIGH and time-sensitive.** This is the point that most deserves the
operator's attention: **a fresh account is a one-time, non-recoverable chance to
capture clean onboarding ground-truth** — signup date, exact bleed-in schedule,
first-value-bet date, stake shape, mug-bet ratio, and then *how long the account
survives and what (if anything) triggered limiting.* Every account onboarded
without recording this is a data point lost forever. The operation currently has
**no such dataset** (§5), which is why idea #1's literature stays hypotheses.

**Cost: LOW.** Mostly discipline + a light capture template. The heavier cost
(browse-baseline, the monitor) is *not* on the critical path for starting —
the dataset can begin on paper.

**On the two open questions (initial read; a formal session should decide):**
- **Stagger vs all-at-once:** WIP item 18's clustering warning argues for
  **stagger** — simultaneous signups + identical early browsing across profiles
  is exactly the correlation fraud vendors look for. Staggering also *spreads the
  dataset over time*, which is better for learning. With Mads specifically being a
  single new holder on a single fresh IP, staggering is more about spacing Mads's
  *own book signups across books* than about Mads vs other holders. Lean:
  **stagger book-by-book, don't open six books in a day.**
- **Bleed-in ramp:** the principle (mug/recreational activity before value/promo
  extraction) is sound and standard. The open design question is *shape* — how
  long, what bet mix, what stake sizes, whether value bets phase in gradually or
  step in. This is precisely the thing the dataset should let you *measure* rather
  than guess. Lean: **pick a deliberate, written ramp for Mads, log it exactly,
  treat Mads as experiment #1** — the value is as much in recording the ramp as in
  choosing the "right" one (which no one currently knows for this operation).

**Recommendation:** **Act on the lightweight half now, independent of any build.**
Before Mads takes a first value bet: (1) write the bleed-in ramp and stagger plan;
(2) stand up a minimal capture log (per-account: signup dates by book, ramp
schedule, first-value-bet date, and an open "outcome" column for eventual
limiting events). This is the cheapest, most time-sensitive, highest-leverage
action across all three ideas.

---

## 4. Cross-cutting technical notes

### 4.1 Where account-health state lives (data model)
`accounts_at_book` is the unit. DR-022's **tier** (limiting-state) and **phase**
(lifecycle) land here as additive columns when their vocabularies lock — the
schema module (`store/schema/accounts.py`) already carries the
`_add_column_if_missing` helper for exactly this. `books.ownership_cluster` is a
first-class health dimension (limiting propagates across a parent company's
books), currently a TEXT field, promotable to a reference table later.

### 4.2 The proxy chokepoint (idea #2's foundation)
`router-sim` runs one `3proxy` per SIM, one SIM per account, on the Pi 5 gateway
(operational since 2026-07-07 per project memory). `3proxy` supports per-instance
connection logging. Turning that on per lane + a small collector yields a
per-account destination log **without any AdsPower integration** — dissolving the
operator's stated blocker. SOCKS5h means DNS resolves proxy-side, so destination
hostnames are visible in-log; TLS keeps content private. This is the recommended
Phase-A data source.

### 4.3 The behavioural layer (idea #2's other half)
browse-baseline is fully spec'd (v3, April) and **unbuilt**. It captures Tim-as-Tim
as a *distributional* baseline (not session replay) and is explicitly designed to
feed AccountCare via versioned persona artefacts under a strict one-way boundary.
A formal session pursuing the "gold standard" monitor should treat building
browse-baseline as the Phase-B prerequisite, and respect its no-cross-DB rule.

---

## 5. The real bottleneck: there is no account-health dataset yet

Every one of the three ideas ultimately depends on ground-truth data the
operation does not yet have: *which onboarding/behaviour patterns actually
correlate with account survival vs limiting, for these books, under this
operation.* Idea #1's literature is community lore until validated against it;
idea #2's nudges are heuristics until trained/checked against it; idea #3 is the
first chance to *start* it. This is the through-line and the reason idea #3 is the
most time-sensitive: **onboarding events are the dataset's raw material, and each
un-captured one is gone.**

Practically: the dataset wants, per account-at-book, at least — signup date,
ownership cluster, onboarding ramp actually followed, first-value-bet date,
running bet-mix/mug-ratio, withdrawal cadence, and outcome events (soft/hard
limit, closure, stake-factor cut) with dates. Start it as a log now; migrate into
tier/phase later.

---

## 6. Recommended sequence (for operator decision in a formal session)

1. **Now, no build:** write the bleed-in ramp + stagger plan for Mads; stand up a
   minimal account-health capture log (idea #3 lightweight half). *Time-sensitive
   — before Mads's first value bet.*
2. **Cheap research:** the longevity policy + literature review (idea #1),
   producing a first draft of the **tier/phase vocabularies** (locks DR-022's
   reservation as a by-product). Flag every proposed signal as measurable-today
   vs needs-capture.
3. **Low-cost early win:** turn on `3proxy` per-lane logging + collector +
   per-account traffic summary (idea #2 Phase A) — delivers the "too many bookie
   hits / not enough browsing" nudges on already-live infra.
4. **Then reassess** for browse-baseline build (Phase B) and the full nudge engine
   / complete-picture monitor (Phase C) — i.e. AccountCare proper, after RouteHub,
   per the vision's satellite order.

**Governance reminder:** none of the above is commissioned. AccountCare is a
post-v3, post-RouteHub satellite in the stated order; bringing any of it forward
is an operator call. Steps 1–2 are research/operational and don't touch the v3
build or any money path; step 3 touches Pi/proxy infra, not BetHub core.

---

## 7. Open questions for the operator
- **Priority/timing:** AccountCare sits after RouteHub in `vision.md`. Do we pull
  cycle-1 research (steps 1–2) forward now because Mads is a live onboarding
  opportunity, while leaving the builds in their planned slot?
- **Stagger granularity:** for Mads specifically — stagger which books to sign up
  for and over what spacing? (Initial lean: book-by-book, not all in a day.)
- **Bleed-in shape:** duration, bet mix, stake sizes, and how value bets phase in.
  (Initial lean: pick one deliberately, log it exactly, treat Mads as experiment #1.)
- **Literature scope:** how deep on the law/T&C side vs the community
  advantage-play/fraud-vendor side for idea #1's review?
- **Dataset home:** start as a markdown/sheet log now, or wait and design the
  tier/phase migration first? (Initial lean: log now, migrate later — don't lose
  Mads's onboarding.)

---

## 8. Pickup checklist for the formal session
Read this note, then the anchors in this order (merged from the §2 map):
1. `vision.md` — constellation + the AccountCare/RouteHub boundary.
2. `project_context.md` — the four strategies × their account-health profiles.
3. `decisions.md` — **DR-009** (AccountCare scope; v4 longevity-model deferral),
   **DR-015** (three-tier severity, locked), the derived-not-stored rule, and the
   **bookmaker-hygiene-rules** table (the decided home for idea #1's policy).
4. `w11_accounts_brief.md` §1.2–1.3 — the tier/phase reservation + the three
   things that need locking; `dr029_scope.md` §3.3 — isolation deferred.
5. `operator_workflow_map.md` §"Account-health behaviours" — current manual practice.
6. `bethub-analytical/race-price-pressure/cycle3_tab_leadlag/report.md` +
   `research/strikeability_research.md` — the freshest camouflage/MBL/gubbing
   research (the law/lit strand idea #1 extends).
7. `router-sim/` brief + status — the proxy chokepoint (idea #2 Phase A source).
8. `browse-baseline/build_spec_v3.md` — the behaviour-capture layer (idea #2 Phase B).
9. `architecture.md` — how AccountCare warnings wire into `promo_events` /
   `warning_catalogue` / `active_warnings_at_log`.
10. `work_in_progress.md` item 18 — profile/email/SIM onboarding pre-work.

- Treat the three ideas as **AccountCare cycle-1**, whose concrete output is the
  DR-022 tier/phase/transition vocabulary lock + a starter dataset, with the
  policy landing in the decided bookmaker-hygiene-rules table shape.
- Confirm the §6 sequence with the operator; commission only what they sign off.
