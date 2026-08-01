# S250 open brief — staged at S249 close

**FIRST ACTION: worklist 0g — commission per-market cent-rounding.**
The only visible money discrepancy in the tool: Betfair row reads
$2,428.98 vs real $2,428.96 because Betfair rounds each market's
commission to the cent and `lay_commission_by_bet` keeps fractions
(proven S249: 71.1728 vs 71.19 over 21 markets = −0.0172). Build
constraints:

- Money-path discipline: red-before tests per shape (single lay,
  multi-lay allocation summing to the market's rounded figure,
  net-loss market zero-commission), operator walkthrough not needed
  (no store write — derivation only) but suite + watchdog re-proof
  required.
- Per-bet shares must still SUM to the market's rounded commission
  (largest-remainder or adjust-last) — display lines must not drift
  from the market total (S247 item 2 contract).
- Verify Betfair's rounding mode on live data before locking
  (half-even matched the S249 read).
- DONE = watchdog funds gap 0.00, Betfair row == real to the cent,
  banner clear, suites green.

## Session-open standing checks

1. `uv run python -m ops.vps_health` (from bethub-v3).
2. Gmail `subject:"RACING ALERT"` — auto-fix capture-side per
   standing authority.
3. Bankroll row == UBank app to the cent ($3,000.00 at S249 close,
   PASSED).
4. NEW: glance the watchdog's first unattended daily pass (banner /
   `GET /api/health/workers` money block) — expect books nothing,
   flags only the known 2¢ until 0g lands.

## Queue (from SESSION_249.md forward routing)

1. 0g (above).
2. **Dual-vantage freshness probe** — same near-jump race, same
   minutes, Mac + VPS simultaneously:
   `python3 -m scripts.source_freshness_probe --venue X --race N
   --code R|G|H --interval 6 --minutes 7` (script deployed both ends,
   capture `a2f4e50`); merge the two jsonl files by timestamp. If
   VPS lags Mac → the Warren R3 fix is residential egress for the
   live pool (real Decodo case, T1 gate evidence); if not → drop the
   freshness thread (cadence already ruled out: site polls ~7s).
3. Day-2 TAB transport telemetry read (rotations, per-book alarms,
   changed=Y lines).
4. Standing queue: 0d transfer door (priority raised S248) · 0c
   hygiene + watchdog flag-detail display quantisation · 0f
   hide/archive + permissive entry (commissioned, conservatism rule
   attached) · fingerprint burn-list persistence across collector
   restarts (small) · racing-health-check exit-code cosmetic ·
   take-SP Stage 0 on next race day · next race day remains the big
   full-stack live-proof sitting.

## Key references

- `sessions/SESSION_249.md` (authority for S249).
- Watchdog surfaces: `ui/api/account_watchdog_service.py`, route in
  `cash_flow.py`, daily trigger in `settlement_worker.py`, section in
  `ops/settlement_review.py`.
- Freshness: `tab_transport_hardening_brief.md` item 5 (S249 status
  block) + `racing-data-capture/scripts/source_freshness_probe.py`
  + first log `probe_output/freshness_VCY_R2_222418.jsonl` (Mac).
- v3 HEAD `20f5611` (suites 1724/301-vitest-303); capture `a2f4e50`.
