# §2.3 — Periodic-only API pattern, reframed on the operational/analytical axis

**Status:** Locked. Closes DR-029 §2.3.
**Authored:** Session 58 (2026-05-03 ACST).
**Governing DRs:** DR-027 (two-database architecture: BetHub owns operational state, capture.db owns analytical/source data), DR-028 (cross-database integration boundary discipline), DR-029 (data-layer fit-for-purpose review before v3 build).
**Source recommendations:** multi-agent review Recommendations 1 and 5 (`agent_review/Judge/judge_synthesis.md`).
**Cross-references:** `dr029/dr029_scope.md` §1.2 (two direct lines into Betfair), §2.4 (Betfair Streaming spec — operational line), §2.5 (soft-book interface contract — operational line); `architecture.md` §B (operational layer).

---

## 1. Framing

The periodic-only API pattern is the locked position that `vps_client` against `capture.db` does not expose an on-demand fresh-now endpoint. Reads return what `capture.db` already holds, written there by the periodic scrape loop on the VPS.

The multi-agent review surfaced that this pattern was being asked to do double duty: serve both analytical consumers (post-hoc review, model calibration, BSP archive, market-curve analysis, analytical fields on bet records at read time) and operational consumers (live pricing, bet entry, burst-window decision support). Recommendations 1 and 5 of the synthesis flagged that the pattern is correct in scope but the scope was drawn wrong.

§2.3 reframes the pattern on the operational/analytical axis. Periodic-only is reaffirmed for the analytical line. Operational consumers are carved out as a separate concern, handled by §2.4 (Betfair Streaming spec) and §2.5 (soft-book interface contract). The bracketing argument that justifies periodic-only for analytical reads is shown to hold there and not transfer to operational reads.

This is documentation work, not new design. The two-direct-lines architecture in §1.2 of the scope document already commits to the split. §2.3 makes the consequence for `vps_client`'s contract explicit so v3 build does not drift back toward dual-purpose reads.

---

## 2. Analytical reads — periodic-only reaffirmed

The analytical line runs from the VPS scrape loop into `capture.db`, and from `capture.db` into v3 via `vps_client`. The reads serve backward-looking work: post-hoc bet review, model calibration, BSP archive lookups, market-curve analysis, and analytical fields attached to bet records at read time per DR-019 (derived state on read).

`vps_client` does not expose an on-demand fresh-now endpoint against the analytical line. Reads return what `capture.db` holds at the time of the call, written there by the periodic scrape loop. There is no path that triggers a fresh Betfair API call on behalf of an analytical consumer.

**The bracketing argument.** Analytical reads are structurally stronger when they return surrounding-interval snapshots from `capture.db` than when they return a single fresh on-demand snapshot. The reason: analytical questions are about market movement *around* the bet (or around the moment of interest), not about a single point. A bracket of snapshots before and after the moment tells you whether the price was drifting, firming, or stable; a single fresh snapshot tells you only what the price is now, which is rarely what the analysis needs. The periodic scrape cadence is calibrated to make brackets dense enough to support the analytical questions v3 will ask.

**Cadence is `capture.db`-internal.** The periodic scrape cadence is set on the VPS side and may evolve as analytical needs mature. `vps_client`'s contract does not surface the cadence as a parameter; it surfaces the data and its timestamps, leaving consumers to reason about freshness from the timestamps themselves. This keeps the integration boundary lean per DR-028.

**Staleness signalling.** When `capture.db` is unavailable or its most recent snapshot is older than the consumer's tolerance, `vps_client` returns explicit staleness or unavailability signals — not silent fallbacks, not stale data dressed up as fresh. The contract for these signals is part of the v1.0 lock per §1.1 of the scope document.

---

## 3. Operational reads — separate concern

The operational line runs from v3 directly to the external source via dedicated client modules: `betfair_client` for Betfair pricing and bet entry, `softbook_client` for soft-book pricing and bet entry. These modules are operational-only. They do not write to `capture.db`, they do not read from `capture.db`, and they are not fronted by `vps_client`.

Operational reads serve live decision support: the racing page, the sports page, the burst-review workflow, bet entry, and any other surface where v3 is asking "what is the price right now" on behalf of the operator's next action. The cadence requirement is sub-second to one-second-class for Betfair (per §2.4 — the Streaming spec), and source-flexible at vendor cadence for soft books (per §2.5 — the interface contract is locked, the source implementation is deferred).

**No analytical input to the operational flow.** The two lines are independent by construction. `capture.db` does not feed operational reads. `vps_client` is not called from operational code paths. The analytical line's periodic cadence has no bearing on operational read freshness. Per DR-028's integration boundary discipline: no caching, no denormalisation, no second integration point — the operational clients are the integration point for operational reads.

**No on-demand fresh-now from `vps_client`.** Where v3 needs fresh-now data for an operational decision, the path is the operational client, not a punch-through to `vps_client` that would itself trigger a fresh Betfair API call. That punch-through pattern is exactly what the periodic-only commitment closes off on the analytical line. Operational fresh-now is the operational line's job; analytical reads return what's in `capture.db` at the time of the call.

**The two lines query the same Betfair API.** Per §1.2 of the scope document, this means the lines are consistent by construction modulo cadence lag for Betfair-sourced data. The analytical line's `capture.db` content lags the operational line's live reads by the scrape cadence; this is expected and is what the bracketing argument is built on.

---

## 4. The bracketing argument does not transfer to operational reads

The bracketing argument justifies periodic-only for analytical reads. It does not justify periodic-only for operational reads, and it should not be invoked when reasoning about operational fitness.

**Why bracketing works for analytical reads.** The analytical question is about market movement around a moment — was the price drifting, firming, stable, on what trajectory, against what volume. A bracket of surrounding-interval snapshots answers that question; a single fresh-now snapshot does not. The periodic scrape produces brackets as a side effect of its cadence. Analytical consumers are time-insensitive — the analysis runs after the moment, not during it — so the periodic cadence's lag is irrelevant to analytical fitness.

**Why bracketing does not work for operational reads.** The operational question is about price right now, on the cusp of a decision the operator is about to make. A bracket of past snapshots tells the operator where the price was; it does not tell the operator where the price is. Cadence lag is the dominant fitness criterion: a snapshot taken sixty seconds ago is materially worse than a snapshot taken sub-second-ago for bet entry, regardless of how rich the surrounding bracket is. The analytical line's strengths are operational weaknesses.

**Pattern of error.** Reading a cadence number from `capture.db`-side measurement (e.g. "last analytical snapshot was 45 seconds ago") and reasoning about whether it's "tight enough near jump" is an analytical-line measurement applied to an operational-line question. The framing only makes sense if the same line serves both purposes, which is exactly what §2.3 is closing off. Surfaced and corrected mid-Cluster-3 of Session 31, and again at top of Cluster 2 of Session 32 — same drift both times. The operational/analytical line discipline standing instruction (`standing_instructions.md` Category 4) names the pattern explicitly so it is caught on sight.

**Test for which line a question is on.** Two questions resolve ambiguity:

1. Is the consumer time-sensitive (acting now, before the next tick)? If yes, operational. If no, analytical.
2. Does the answer need to describe movement around a moment, or the price at a moment? If movement, analytical. If price, operational.

If a question splits across the two — e.g. "show me the live price plus a small history of the last few minutes for context" — the live price comes from the operational line and the history comes from the analytical line. They are stitched at the v3 consumer surface, not inside `vps_client` or `betfair_client`.

---

## 5. What this closes

§2.3 is locked. The DR-029 stream count drops from nine to eight.

**What changed vs. pre-reframe scope.** The pre-reframe position treated the periodic-only API pattern as a single decision applying to all `vps_client` reads. The reframe splits the position by line:

- **Analytical line (`vps_client` against `capture.db`):** periodic-only reaffirmed, bracketing argument preserved as rationale, no on-demand fresh-now endpoint.
- **Operational line (`betfair_client`, `softbook_client`):** separate concern, handled by §2.4 and §2.5, bracketing argument does not apply.

The reframe does not change `vps_client`'s contract — `vps_client` was already periodic-only by intent. It changes how the project talks about the pattern: the pattern is not a universal property of v3's data reads, it is a property of analytical reads specifically.

**What this enables.** §2.4 (Betfair Streaming spec) and §2.5 (soft-book interface contract) can specify operational-line behaviour without inheriting analytical-line constraints. Cadence, freshness signalling, error semantics, and reconnection patterns for operational reads are designed against operational requirements, not against the bracketing argument.

**Open items routed forward.**

- §2.4 — Betfair Streaming spec and cadence design. Documentation in hand (`external_api_resources.md` §1 — Reference Guide, Sample Code, API Tools Demo, plus the Streaming API surface itself). Fix 4 brief drafting unblocked.
- §2.5 — soft-book interface contract, source-flexible. Q5 input from the API observation probe adds harness/greyhound coverage gap as design input. Racing API OpenAPI spec (`openapi.json`) is the canonical reference for the Racing API side of the soft-book interface.

**No new debt surfaced.** §2.3 closes cleanly without adding to the three pieces of named debt (no test coverage, no migration framework, monolithic orchestrator file) carried at DR-029 close-out time.
