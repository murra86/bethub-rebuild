# Session 116 — Source documents

**Written:** 2026-05-11 (post-close recovery from Session 116).
**Reason:** Session 116 close-out missed the Cat 2 "Persist drafted-but-not-assembled artefact content to scratch" rule. The operator's refreshed top-level view document — provided in Session 116 chat as the strategic anchor for the `vision.md` update queued for Session 117 — was summarised in `SESSION_116.md` but the document text itself was not persisted. Session 117 surfaced the gap on opening; recovery is this file plus a close-out note appended to `SESSION_116.md`.

**Session 117 use:** this file is the source-of-truth for the operator's refreshed top-level view of BetHub. Integrate into `vision.md` per the two locked refinements from Session 116:

- (a) BetHub surfaces inputs, doesn't recommend. Drop original Job 3 "Surface decisions in real time" framing. Add Betfair price-movement indicators as a named feature for racing pages.
- (b) Binding-constraint statement included with sharper why: fingerprint-contamination risk from manual-switching errors (AdsPower / Wi-Fi / desktop-browser slip-ups), not just time-overhead.

Promo-scheduler does not enter `vision.md` — stays standalone, not in constellation.

**Operator note (Session 116):** "Satellite sections are placeholders that will be expanded as each tool becomes the active build." Applies to RouteHub / AccountCare / Analytics / edge-generators / price-capture VPS — keep their entries lean in `vision.md`; full treatment lands when each tool moves to active build.

---

## Operator's refreshed top-level view (provided at Session 116 open)

# BetHub Vision

## What BetHub is

BetHub is the operational hub for a multi-persona, multi-
strategy promotional betting operation. It is the single
surface from which the operator views edges, places and
records bets, monitors accounting flows, and watches the
operation run end-to-end.

## The operation BetHub serves

The operation runs multiple personas — internally called
accounts — each holding bookmaker accounts (book-at-
accounts) at many bookmakers. The number of active book-at-
accounts at any given time is high enough that coordinating
across them manually is impractical; the volume of bets,
settlements, and reconciliations exceeds what an operator
can track reliably without tooling.

The operation executes four distinct betting strategies
(Safety Net, Price Booster, SGM Correlated Friction,
Synthetic Each-Way) against a constantly shifting
promotional landscape. Every bet entered into BetHub
belongs to one of these strategies; every bet exits as
either a settled outcome, a void, or a promotional credit.
The operation's value comes from the cumulative edge across
thousands of small positions — which means the operation's
accuracy is the operation.

## Why BetHub exists

BetHub v2 went live in early March 2026 and proved the
operation could run on a custom platform. It also proved
that without architectural discipline, the platform itself
becomes the bottleneck. v2's pain points — manual
reconciliation, undetected data drift, opaque promo cycles,
accumulated bugs that compromised analytical confidence —
define what v3 must not repeat.

BetHub v3 exists to be the tool the operator can have full
faith in: accurate without manual investigation, self-
surfacing on anomalies, and structured so that promotional
cycles and bet histories are queryable at the level
analytics actually need.

## What BetHub does

- Surfaces live odds and Betfair market state
- Captures bets — manually or via integration — with
  strategy and cycle tagging
- Settles automatically where data permits; flags where it
  doesn't
- Reconciles book-at-account positions against internal
  records
- Surfaces anomalies, drifts, and inconsistencies as they
  emerge, not at quarter-end
- Exposes accounting flows and inter-account movement
- Provides primitive account-health and primitive analytics
  visibility — enough that the operator can sense the state
  of both areas at a glance, with sophisticated treatment
  living in AccountCare and Analytics
- Provides the data foundation for downstream analytics

## Non-negotiables

These are the qualities BetHub must hold across every
release. Drift on any of them is a regression regardless of
what else has been added.

- **Trust without manual reconciliation.** If the operator
  has to spot-check the tool to know it's right, the tool
  has failed.
- **Anomalies surface as they occur.** Bugs in data or
  logic are caught at the cycle they happen in, not
  discovered months later when analytics produce nonsense.
- **Promotion cycles are visible end-to-end.** A single
  insurance cycle, from qualifying bet to bonus credit to
  bonus turnover to final P&L, is one queryable thing —
  not five disconnected rows.
- **Strategy-tagged from the moment of entry.** Every bet
  knows which of the four strategies it belongs to.
  Untagged bets are a data defect, not an option.
- **Adelaide local time is the operator's clock.** Timestamp
  anchoring is operator-facing, not server-facing.

## The constellation

BetHub is the operational hub. It does not need to be the
only tool, and it should not try to be. The long-term
vision is a constellation of tools that interoperate
cleanly, each owning a distinct domain. Build priority
runs roughly in the order below.

**Top priority (current).**

- **BetHub (core).** Operational hub. Bets, odds,
  settlement, reconciliation, accounting, anomaly
  surfacing. Carries primitive account-care and primitive
  analytics inside it so the tool can stand alone even
  before the satellites exist.

**Next, after BetHub v3 ships.**

- **RouteHub (planned).** Pairs each book-at-account with
  its correct network identity (router and SIM) and
  AdsPower profile, removing the manual switching that
  makes mistakes statistically inevitable over a long
  enough timeline. Envisaged as a Raspberry Pi hub
  controlling the routers and SIMs, with the operator's
  laptop staying on home Wi-Fi only. High operational-risk
  payoff, which is why it lands first in this tier.

**Following.**

- **AccountCare (planned).** Behavioural account-
  conditioning lifecycle — keeping book-at-accounts
  healthy across betting patterns, withdrawal cadence,
  account age, and bookmaker-side signals.
- **Analytics (planned).** True-edge measurement, strategy
  P&L, promotion-cycle ROI, the ability to strip
  promotional EV from results to see model-pure
  performance.

**Further out.**

- **Edge generators.** Racing EV Model, AFL Edge, SGM
  Correlated Friction model. These produce edges; BetHub
  consumes them. Significant work expected before they're
  ready to integrate as proper satellites.
- **Price capture VPS.** Scraper infrastructure feeding
  odds data to BetHub. Currently exists in working form
  but not formally integrated.

The boundary between BetHub and its satellites is
interface-level: BetHub does not generate edges, does not
own network isolation, does not run account-conditioning
behaviour, and does not perform deep analytical modelling.
It is the operational surface they feed and the historical
ledger they draw from.

## What BetHub is not

- Not an edge generator. Models live elsewhere.
- Not a network/device isolation tool. That is RouteHub.
- Not a deep account-conditioning workflow tool. That is
  AccountCare.
- Not a deep analytics platform. That is Analytics.
  BetHub's job is to make the data analytically usable,
  not to host the analysis.
- Not a multi-user platform. Single operator; multiple
  personas managed within.

## The test of scope

If every satellite tool disappeared tomorrow — no RouteHub,
no AccountCare, no Analytics, no Racing EV model, no
scraper VPS — the operator could still run the operation
from BetHub alone with accurate historical records,
sufficient operational visibility, and enough analytical
surface to keep making informed decisions. The satellites
add leverage; BetHub holds the operation.
