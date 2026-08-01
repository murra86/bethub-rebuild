# S249 open brief — staged at S248 close (auto-open agent)

**AUTO FIRST ACTION: wire the account watchdog through the LIVE app.**

## Close verification (all checks PASS; one expected NOTE)

- **PASS** — SESSION_248.md read fully; claims list below verified against it.
- **PASS** — v3 repo: HEAD `f410a6c`, log order `f410a6c` → `9e9dd0c` →
  `404a928` → `64ff337`; tree clean except untracked `.claude/`;
  `git status -sb` = `## main...origin/main` (no ahead/behind — pushed).
- **PASS** — Capture repo: HEAD `625c650` → `d4f4306`; tree clean;
  `## master...origin/master` (no ahead/behind).
- **PASS** — VPS deploy state: box HEAD `625c650`; `racing-capture` active,
  `racing-api` active; `GET /health/tab-transport` returned live telemetry
  (`{"process":"racing-api","tab_transport":{"requests":0,"hunts":0,...}}` —
  all counters 0, consistent with the no-race window).
- **PASS** — bethub-rebuild files all exist, non-empty:
  `sessions/SESSION_248.md` (6,276 B); `s248_build_plan_review.md` (5,265 B,
  header "TRIAGED S248"); `betfair_recon_fix_brief.md` (7,408 B, S248 status
  block line 7 + amendments section line 108); `tab_transport_hardening_brief.md`
  (6,404 B, "S248 BUILD + DEPLOY" block line 10); `worklist.md` (8,605 B,
  items 0 / 0b / 0c / 0d / 0e all present); `bank_transfer_playbook.md`
  (3,649 B); `bank_transfer_quickref.html` (5,483 B).
- **PASS** — Backups in `~/.bethub/backups/`:
  `bethub-pre-s248-remit-fix-20260721.db` and
  `bethub-pre-s248-bankroll-seed-20260721.db` both present.
- **NOTE** — Live money check: `curl localhost:8787/api/v1/cash-flow/pnl`
  → connection refused = **app closed at time of check** (expected —
  operator shut it for the night). Session-record figures stand as written:
  P&L 1,054.97 / op cash 14,940.14 / floats 4,669.80 / self-check green.
  Re-verify on the operator's restart (which also makes `404a928` live).

## Session-open standing checks

1. `uv run python -m ops.vps_health` (from `~/Desktop/Projects/bethub-v3`).
2. Gmail: check `subject:"RACING ALERT"` in Sent; auto-fix capture-side
   per standing authority.
3. **NEW standing check:** Bankroll row (**$3,000.00 at close**) must equal
   the UBank bank app, to the cent.

## Queue (from SESSION_248.md Forward routing)

1. **AUTO first:** wire the account watchdog through the LIVE app
   (on-demand route + daily trigger + fault banner), then
   operator-supervised first pass — expect it to book the standing
   3¢ and go clean.
2. Source-freshness probe (transport brief item 5): site-XHR endpoint
   discovery + probe script; tomorrow's cards supply the near-jump
   head-to-head. Cadence stays 8s.
3. Operator restart of BetHub → bankroll screen live; walk the
   quick-ref card on first real transfer.
4. Read the day's first transport telemetry
   (GET /health/tab-transport + live-poll lines + per-book alarms).
5. Glance: `racing-health-check.service` failed state on the VPS
   (pre-existing 6AM email unit, untouched tonight).
6. Standing: worklist 0d (transfer door) queued; 0c holdings
   quantisation; 0e UBank API (LOW, when commissioned).

Plus: **operator must restart BetHub to make the bankroll screen live —
commit `404a928` is implemented-not-live until then.**

## Key references

- Briefs: `betfair_recon_fix_brief.md` (item 4 = watchdog; S248 status:
  R4 client + core module BUILT, in-app wiring is S249) and
  `tab_transport_hardening_brief.md` (S248 BUILD + DEPLOY block; item 5
  source-freshness is next).
- `worklist.md` items 0–0e: 0 bankroll model (built S248), 0b bankroll
  tile (folded into 0), 0c holdings cent-quantisation, 0d transfer door
  (priority raised), 0e UBank automation (LOW).
- `bank_transfer_playbook.md` (10 scenarios; #5/#8 = the interim
  bankroll↔intermediary remittance+funding pair) + one-screen
  `bank_transfer_quickref.html`.
- Watchdog code: `workflows/balances/v1/account_watchdog.py` with
  `tests/workflows/balances/v1/test_account_watchdog.py` (13 tests;
  v3 suite 1704 green at `f410a6c`).
- R1–R5 rules (recon brief "S248 review amendments", binding):
  - **R1** compare lines on GROSS (cleared `profit` is commission-free);
    reconcile commission at MARKET level via `lay_commission_by_bet`.
  - **R2** cent diffs are permanent (2dp rows) — idempotency key per
    bet_id; re-runs are no-ops on already-booked lines.
  - **R3** book `amount = real − derived` (standing 3¢ books as −0.03);
    self-check is sign-neutral — red-before must assert post-booking
    derived == real.
  - **R4** client extension first: settledDateRange + paging +
    `moreAvailable` surfaced (done `9e9dd0c`); loud truncation.
  - **R5** funds compare market-netted: (available + exposure) vs
    (derived + Σ pending committed), or only when flat.
