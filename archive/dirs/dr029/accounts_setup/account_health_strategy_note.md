# Account-Health & Extraction Strategy — Framework Note

**Origin:** Session 152 (2026-06-16, Adelaide). Emerged from the
accounts-setup cluster/platform field design. To be carried into the
future account-health / extraction strategy workstream.
**Status:** strategy record, not a build artefact.

---

## Core principle — registration timing ≠ exploitation intensity

These are two independent levers and must be managed separately. The
asset being protected is not any single account but the operator's
clean underlying identity (device, IP, KYC, behavioural profile).
Related companies share a view of that identity; once it picks up a
sharp/promo flag, the flag travels across the related group.

Therefore: **open related accounts early, while the identity is still
clean**, so the second account is banked before any flag exists. Then
**stagger exploitation** — never run same-owner brands hard at the
same time. Walk through the gate before it closes rather than racing
it down. Slow-burn the *activity*, not the *registration*.

## The two correlated-flag axes

1. **Cluster — shared corporate owner.** Well-documented: a
   restriction on one brand commonly propagates to siblings under the
   same parent (Entain = Ladbrokes + Neds; Flutter = Sportsbet;
   Tabcorp = TAB). IP/device linkage is tracked across the group.

2. **Platform — shared white-label provider and risk engine.** The
   provider runs risk management on behalf of every operator on the
   platform, so one trading/risk system sees activity across all its
   books. One provider (BetCloud) markets an explicit network that
   redistributes over-limit bets across its operators in real time.
   Treat same-platform as a correlated-flag risk, not an independent
   set of books.

The axes are complementary, not redundant: cluster = shared owner;
platform = shared interface + shared risk engine.

## Playbook split — protect vs harvest

- **Major-owner brand pairs** (Entain, Flutter, Tabcorp, etc.) →
  **PROTECT.** Open early, stagger, slow-burn, treat as keepers.
  These feed the clean-turnover and synthetic-each-way game
  (Strategy 4).

- **Small same-platform books** (the ~40 BetMakers books, ~26
  GenerationWeb, ~22 Punterstech, etc.) → **HARVEST.** Each is
  individually low-value and the shared risk engine will correlate
  the operator quickly regardless. Harvest signup + first-fortnight
  promos fast across a batch, accept they limit together, treat as
  disposable. Longevity was never the asset; the welcome value was.

Relatedness by **major owner** → protect and stagger.
Relatedness by **shared small-book platform** → harvest and burn.

The cluster and platform fields on each book are exactly what let the
operator tell, at registration time, which playbook a new book
belongs to.

## Worked question — Ladbrokes / Neds

Open both early and quietly while clean (bank the second account
before any flag). Run one hard, keep the other light, rotate. Do NOT
pump both hard simultaneously — identical sharp activity across two
same-owner brands at once is the loudest signal their cross-brand
system is built to catch, and it can poison the identity for the next
related brand too. "One nullifies the other" is real but rarely
absolute at signup; true dead-on-arrival is more a platform-risk-engine
outcome for very sharp play than a signup outcome.

## Future tool enhancement

Bet-time warning: flag when the operator is about to run hard on two
books that share an owner or a risk engine. Logged as a future
enhancement; not part of the accounts-setup build.

## Caveat

This is first-principles reasoning from how these systems are built,
not from inside any operator's risk desk. Tim's decade of observed
account history is the ground truth; where it contradicts this note,
the observed history wins.
