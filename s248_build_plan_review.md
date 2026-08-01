# S248 build-plan review — TRIAGED S248 (Tue 21 Jul pm)

**All findings accepted and folded: R1–R6 → `betfair_recon_fix_brief.md`
item 4 amendments section; T1–T7 → `tab_transport_hardening_brief.md`
inline [Tn] marks. Briefs are now the build source of truth.**

**S248's automatic first action: triage this file, fold accepted
findings into the two briefs, THEN build.** Adversarial review ran at
S247 close against v3 `64ff337` + capture `d4f4306`; every claim was
code-verified by the reviewer. Verdict: both plans are sound in
concept; four HIGHs must be folded in before building.

## Watchdog + cent-truing (`betfair_recon_fix_brief.md` item 4)

- **R1 HIGH — state the comparison basis.** Cleared-order `profit` is
  per-line and COMMISSION-FREE; our derived side is commission-netted
  per market. Naive line compare false-flags every winning lay by its
  commission share (alarm fatigue day one). Compare lines on GROSS
  (+S won / −L lost); reconcile commission at market level (expected
  = rate × max(0, market net) — `lay_commission_by_bet` already
  computes it).
- **R2 HIGH — idempotency or re-book runaway.** Stored rows stay 2dp
  forever, so a line's cent diff is PERMANENT — a daily+on-demand pass
  re-books the same cent every run. Booked adjustments need an
  idempotency key per bet_id (existing-adjustment check); on-demand
  runs must be no-ops on already-booked lines. (Drift would be
  invisible until the next pass calls it "unattributable" — R3.)
- **R3 HIGH — sign convention, explicitly.** Balance derivation ADDS
  book-side adjustment amounts (`balance_derivation.py:658`). Correct
  booking is `amount = real − derived` (the standing 3¢ books as
  **−0.03**, not +0.03). CRITICAL: the pnl self-check is neutral to
  adjustments of EITHER sign — a wrong-signed implementation passes
  silently and doubles the gap. Red-before test must assert the
  post-booking derived == real. Payload supports negatives; floats
  untouched (verified).
- **R4 MED — client extension is an unplanned prerequisite.**
  `list_cleared_orders` has no settledDateRange / paging, and the
  translation DROPS `moreAvailable` → an unfiltered daily pull
  silently truncates. Extend the client (date range + paging +
  more_available surfaced) before the watchdog consumes it.
- **R5 MED — funds compare with open positions.** Betfair exposure is
  market-netted; derived subtracts each pending liability fully.
  Compare (available + exposure) vs (derived + Σ pending committed),
  or run the funds compare only when flat.
- **R6 LOW** — daily cent rows are ledger noise in movements; the
  per-line naming keeps them legible. Accepted.

## TAB transport hardening (`tab_transport_hardening_brief.md`)

- **T1 HIGH — cadence gate.** The observed burns were
  FINGERPRINT-wide, not per-IP — round-robin pools do NOT make faster
  polling safe against that axis; 3s cadence would burn the whole
  candidate list faster. Cadence rises gate on item-3 telemetry
  showing IP-side blocks specifically (not just the EV case+Decodo
  tier). Update brief item 4 wording.
- **T2 MED — build from the DEPLOYED fingerprint order** (probed-200
  candidates first; burned ones last). The brief's own list is
  stale/inverted — following it literally wastes half of every hunt.
- **T3 MED — budget math + live-pool breaker.** 8-try budget < 6 fps
  × 2 sessions ⇒ tail candidates unreachable ("breaker only when ALL
  fail" is currently unachievable). And the live route has NO breaker:
  under total burn, every 8s poll runs a full hunt (~8×20s timeouts)
  on the API threadpool. Fix budget to cover the list; add a shared
  cooldown/breaker in tab.py covering both pools.
- **T4 MED — per-book alarm needs three gates:** (a) inside the
  racing+expected_up block (else nightly false alarms post-19:00
  clean exit); (b) post-lull arming — capture starts exactly T-60 =
  NEAR's forward edge, so require in-window time ≥ threshold or
  first-snapshot-seen before arming; (c) abandoned meetings = accepted
  false-alert limit or gate on non-abandoned. Detection latency as
  specced is 20–35 min — acceptable vs the 90-min blind spot; say so.
- **T5 LOW** — per-book MAX(snapshot_time) has no supporting index;
  scope the query to NEAR-window race ids or add
  (bookmaker, snapshot_time).
- **T6 MED — source-freshness scoping caveats:** control jurisdiction
  (feed pulls NSW; operator's browser may sit in an SA pool) and CDN
  edge variance before concluding host-level lag; and the tab.com.au
  site XHR is Akamai bot-manager territory — a host switch needs its
  own transport spike gate. Sequencing (source before speed) stands.
- **T7 LOW** — validate impersonate names against pinned curl_cffi at
  startup (unknown names currently burn hunt budget silently).

## Reviewer's sound-list (no action)

Rotation base already live-proven; per-book alarm belongs in the
battle-tested W2 machinery; pool separation correct; telemetry cheap
and the right evidence base; no-Decodo-buy call matches incident
data; flag-don't-absorb is the right watchdog shape; cent-truing is
self-check-neutral and float-safe once R2/R3 are stated;
post_settlement_void.py is the worker-embedded pattern to copy.
