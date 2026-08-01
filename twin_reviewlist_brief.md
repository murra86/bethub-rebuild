# 0m — twin-repair review-list correction pass (mini-brief, S259)

Status: DRAFT → one adversarial review → build. Scope: capture-side,
one quiet sitting (30 Jul). Successor to 0l; operates ONLY on markets
the 0l identity guard refused (or flagged) — it never touches markets
the merge handled.

## The class, diagnosed (live evidence 30 Jul)

The ~208 gate-refused markets (expect ~400-600 once nights 2-3 sweep
the rest of history) are overwhelmingly the **March-era consecutive-day
overwrite**: pre-W7, the collector's 12h-ahead discovery crossed the
UTC date line and upsert's new-value-wins stamped TOMORROW's market id
(and sometimes scheduled_start) onto TODAY's row at venues racing
consecutive days (Redcliffe, Pakenham, Bunbury, Flemington…). Result:
one market id on two REAL, different races — runner overlap 0%, which
is exactly why the 0l guard refused. Verified exemplars:
- Redcliffe 1.254775947: row 36212 (race_date 4 Mar, snapshots 4 Mar,
  scheduled_start 5 Mar ← overwrite smoking gun) vs row 47725 (5 Mar
  throughout, consistent). Market numerically ~28k ABOVE 4 Mar's
  entire single-row id range, dead-centre 5 Mar's.
- Flemington 1.254776469: row 68802 (dated 6 Mar, snapshots 7 Mar ←
  inconsistent, placeholder midnight start, confidence 0.5) vs row
  76325 (7 Mar throughout, venue+race_no+time_exact 1.0).

External authority is UNAVAILABLE (betfair_historical: zero coverage
of these markets). The correction must run on internal evidence only —
and therefore only CLEARS wrong stamps (restoring the row to the
pre-existing no-market-id shell state); it never re-stamps. No
restoration guessing.

## Decision rule (act only on agreement, else leave + audit)

Per refused market, per fragment, three independent signals:
- S1 envelope: numeric market id vs the per-day id range built from
  SINGLE-row (trusted) markets. Decisive only when the id falls
  OUTSIDE one candidate day's [min,max] entirely (adjacent-day ranges
  overlap — batch creation — so range membership alone never decides).
- S2 self-consistency (date↔start): local_day(scheduled_start) vs
  race_date. Disagreement marks the overwrite victim; midnight-
  placeholder starts abstain.
- S3 self-consistency (date↔activity): last betfair/bookmaker snapshot
  day vs race_date. Zero-snapshot fragments abstain.

KEEPER = the fragment consistent on every non-abstaining signal.
CLEAR the other fragment's betfair_win_market_id + betfair_place_
market_id ONLY when (a) exactly one keeper qualifies, (b) at least one
signal ACTIVELY marks the loser wrong (not just abstentions), and
(c) no signal contradicts. Anything else: leave, audit, stays on the
review list. Cleared rows get match_method='reviewlist_0m_cleared'
(confidence NULL) and a row in append-only `market_stamp_corrections`
(pre-image of every changed column, evidence per signal, run_id).
Post-clear, the market drops out of the twin census; if a cleared row
later gets its TRUE id stamped by any writer, normal 0l machinery
(B4/B6, all gates) handles it.

## Also in scope, REPORT-ONLY today

- The 12 contradictory-result merged races (verifier finding): extract
  both result sets + journal pre-images into a review report; the fix
  (authority re-verification via the subscription backfill) is its own
  small follow-up once classified.
- The 74 settled-excess audits: extract and classify (expected: the
  pre-existing 16-on-N contamination class), report-only.

## Safety

Nightly backup exists + S259 pre-repair backup retained; corrections
are two-column NULL-ing with full pre-images (trivially reversible,
per-market transactions); dry-run mode first, then live run with
counters; identity-write discipline (no other column touched);
runs fine alongside the collector (rows touched are March-era,
terminal, untracked). Tests red-before on fixtures built from the two
verified exemplars + an ambiguous case that must be LEFT.

## Deliverables

`scripts/reviewlist_correct.py` (+ shared evidence module if natural),
tests, dry-run + live run tonight-safe (no interaction with the 23:45
repair timer — different market set by construction: the repair skips
what this fixes, this only touches what the repair refused), report
appendix to twin_row_fix_report.md, session record §9.

## Review round (S259 sitting, one adversarial reviewer): SAFE WITH FIXES
Measured on the live refused set (204 unique, not ~208): rule decides
143 CLEAR / 61 LEAVE, zero wrong-loser cases found. Integrated fixes:
- F1 payload quarantine (MAJOR): ~25% of losers are chimeras (wrong
  market's snapshots + selection ids on the wrong race's horses — 22
  rows with post-date snapshots, 233 duplicated selection ids across
  28 pairs, chained-overwrite rows exist). Same-transaction fix:
  quarantine (delete, full pre-image to journal) snapshots whose
  venue-local day ≠ race_date on the cleared row; NULL selection ids
  duplicating the keeper's; NULL scheduled_start when S2 proved it
  overwritten (F3). Cleared rows excluded from calibration/model
  extracts until the data reset (report + DR note).
- F2: S1-envelope-only clears additionally require envelope n≥30 on
  BOTH candidate days AND the id inside the keeper's day envelope
  (all 21 current instances already pass).
- F4: timezones pinned — venue-local from state (fallback Sydney);
  placeholder = venue-local midnight; S2/S3 abstain within 3h of
  local midnight.
- F5: semantics pinned — keeper = zero wrong marks; loser = ≥1 ACTIVE
  wrong mark; a loser's consistency on other signals does not block.
- F6: age fence (no row younger than 14 days ever touched); LIVE RUN
  DEFERRED until the nightly repair converges (dry-run today) so the
  refused set is complete and verification baselines stay clean;
  future verifiers read market_stamp_corrections.
- F7: settled-excess count is 73 (not 74); classification/exclusion
  ordered BEFORE any model.db re-extract or historical EV recompute.
