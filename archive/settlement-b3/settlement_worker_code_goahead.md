# Settlement-worker build — operator GO-AHEAD to Code (clears the §3 gate)

> Session 217 (2026-07-02 ACST). Answers Code's §3 read-back
> (`settlement_worker_readback.md`) on the LOCKED
> `settlement_worker_build_brief.md`. Anchor unchanged: `e2638fa`, tree clean.

## Decision
**Go-ahead to build. §9 edit-surface pick = Option (1) — live-effective.**

Your read-back is accepted in full: anchor confirmed, all 39 anchors resolve
(the six drifts are cosmetic), §5.1a understanding matches, and the
enriched-settlement-payload sourcing is the right call over a companion
market-book read.

## What (1) authorises
- **One additive line** in `_translate_market_settlement`
  (`clients/betfair_client/v1/_translation.py`, ~:561-570): lift
  `r.get("adjustmentFactor")` off the same raw runner dict that already
  yields `removalDate`, and populate the new settlement-model field.
  Named explicitly here under the same "name exactly what you added"
  discipline §9 applies to the companion-read carve-out. This is the
  **only** edit outside §9's named `settlement.py` surface, and it is
  narrower than the carve-out §9 already blesses.
- Everything else stays inside §9's named surfaces:
  - `clients/betfair_client/v1/settlement.py` — `RunnerSettlement` gains
    `adjustment_factor` (+ applied flag), and `_parse_settlement` lifts it.
  - `bet_entry/v1/settlement.py` — the Option C guard logic
    (WIN parks ≥2.5%, PLACE parks on any factor >0; dead-heat parks on
    `dead_heat_count > 0`; `WINNER → SETTLED_WON` in both resolvers).
  - Refinement B export via `bet_entry/v1/__init__.py`.

## Non-negotiable invariants (from the brief)
- **Never silently auto-pay full on a parked case.** Option B (park on
  any removal) remains the pre-authorised fallback and **must** fire when
  `adjustment_factor` is `None` / unsourceable — never a silent full payout.
- **Never model the reduction maths** — read Betfair's factor, gate on it.
- **§5.1b verification record** on every removed-runner decision (park /
  paid-full / fallback-flagged) so the guard can be watched against real
  Betfair once live.
- Money-path invariant intact end to end.

## Ship state
- Worker lands **wired but OFF by default**: new opt-in flag
  `settlement_worker: bool = False` in `ui/api/config.py`
  (`Settings`, `env_prefix="BETHUB_"` → binds `BETHUB_SETTLEMENT_WORKER`).
  Not live-proven until the operator flips the flag.
- Full §7 5.1 success criteria via `MockSettlementReader` + domain
  `MarketSettlement` fixtures. `RealSettlementReader` mirrors
  `RealBetfairAdapter.get_market_settlement` (betfair_adapter.py:305-324).

## On completion
Return a build report (anchor sha, files touched, the `_translation.py`
line as landed, test results, flag-off confirmation) for S-next triage.
Do **not** flip the flag — that live-enable is the operator's call.
