# Session 245 — Mon 20 Jul 2026

**Opened** 09:22 ACST · **Closed** 17:07 ACST (same workday).
**Focus:** TAB API build arc (operator priority — "TAB live by Saturday")
→ race-watcher Phase 1 → UI pass #3 (in flight at close). **Closed:** yes.

## What was delivered

**TAB soft-odds — SHIPPED + live-proven (the session's spine).**
- **A1 spike corrected the root cause:** TAB's block is **geographic
  (Australia-only) + Akamai browser-fingerprint**, NOT the datacenter-TLS
  story the S241 scoping brief assumed. Proven transport (spike write-up
  `tab_spike_result_s245.md`): Decodo residential **country-targeted AU**
  (`gate.decodo.com:7000`, `user-<u>-country-au-session-…`) + `curl_cffi`
  **Safari** impersonation (Chrome → 403) + **hunt-and-pin** (most random
  AU IPs 403; a pinned working IP holds). Off the Decodo IP → **zero tie
  to the operator's home line or TAB account**. Decodo plan already
  includes AU free (3 GB, $11.25/mo) — **no new spend**.
- **Build 1 (background soft-odds auto-fill)** — capture transport +
  `DISABLED_BOOKMAKERS` drop + `GET /racing/markets/{id}/soft-odds` (VPS)
  + vps_client surface + racing route + frontend seed + toggle. Live-proven
  end-to-end. (`tab_soft_odds_build1_report.md`; bethub-v3 `fdd6c0b`.)
- **Live-proof fix (the real catch):** the frontend showed blank on Wagga
  R7. Root cause found by direct probe — the soft-odds endpoint's runner
  LEFT JOIN full-scanned the **6.8M-row** `bookmaker_snapshots` table
  (~**12 s/request** → app timed out → blank). Fix = add the known
  `race_id` to the join → uses an existing index → **~0 ms**, **no capture
  DB schema change**. Verified 12,320 ms → 0.01 ms, identical rows; live
  end-to-end 0.55 s through the tunnel. Added a plan-guard regression test
  (`tests/test_soft_odds_route.py`) that fails if the scan returns. Also
  added: frontend **refetch** (30 s) + **keep-updating** (auto-seed tracks
  the feed; `operatorTouchedRef` protects edits) — bethub-v3 `8e49c97`.
- **Build 2 (dedicated live-refresh IP)** — operator-commissioned (odds
  move fast near the off; he lays quickly). Per-pool pinned sessions in the
  transport (`pool="live"` ≠ collector), new `GET …/live-soft-odds`
  (fetch_tab live → selection-id join → clean 503 degrade), frontend
  fast-poll (visible + within-30 m; 15 s → 8 s in the final 5 m; live
  overrides background; edits protected). **Live endpoint proven vs real
  TAB** (prices moving vs background). Found+fixed: the API wasn't loading
  `.env` → live fetch failed-closed to 503 (added `load_dotenv()`).
  (`tab_live_refresh_build2_report.md`; bethub-v3 → `09d0897`.)
- **Feedback 1 (book-driven, no checkbox)** — TAB fills only when the
  armed book is TAB (`/\btab\b/i` on the book name — "NSW TAB"/"TAB (SA)"
  yes, "Tabcorp" no), blanks on other books, operator edits survive book
  switches. (`tab_book_driven_fill_report.md`; bethub-v3 → `abd84e1`.)
- **Coverage answered:** TAB feed is **thoroughbred-only** (discover
  filters raceType "R"; dogs/harness get zero TAB odds) — operator elected
  to **leave dogs/harness for now**.

**Race watcher Phase 1 — SHIPPED (implemented-not-live, first-cut).**
Walkthrough locked via mock (`race_watcher_execute_bar_mock.html`, take 2 =
the row-level "Call" column): **one global execute bar** (hidden), **STRONG
ceiling (no CERTAIN)**, **faint-dot for dead runners / explicit LEAVE for
tempting traps**, reasons on hover, **grade stamped at log**, grades against
the **top-bar armed promo**. Built (`raceWatcher.ts` + Call column + Part-C
grade-at-log; bethub-v3 `7aab1e8`). **Bands are an explicit first cut** —
sharpen on data. Outcomes recorded in `race_watcher_design_note.md` §7.

**UI pass #3 — IN FLIGHT at close** (brief `ui_pass3_build_brief.md`, mock
`ui_pass3_betlog_row_mock.html`). BetLog row **P&L column far right +
🛡 shield on insurance bets** (operator-locked); unmatched-lay bar → real
values (lay-price echo fenced: stake-only fallback if it'd touch the money
path); live total-matched on the race page; refresh-cadence review. Build
agent running uninterrupted past close → **S246 first action = triage its
report.**

## Operator decisions locked / captured
- Watcher: one global bar; STRONG ceiling; dot/LEAVE; top-bar promo
  (Phase 1). **Phase 2 (whole-card + promo-assignment "Today's promos"
  list) PARKED** — operator unsure the systematic workflow fits his edge
  cases (ad-hoc promos, multiple-per-race); live with Phase 1 first.
- **FB-conversion CALL uses 70%** (rule-of-thumb target); **all EV
  calculations stay 65%** (conservative). Captured `tab_watcher_feedback_s245.md`.
- Build 2 cadence (15 s / 8 s), tunable.
- UI pass #3 BetLog row: P&L far right, 🛡 shield.

## Standing-instruction adherence
Silent open (fast-path result presented); W5 mailbox ticks ×2 handled — both
the **Pakenham Synthetic "Stamped coverage" false alarm** (Betfair calls it
"Pakenham", bookies "Pakenham Synthetic" → the coverage check's twin-dedup
misses the name-split; race IS Betfair-stamped; **logged as a low-priority
capture-side alert-noise fix**). One autonomous capture-side action (manual
identity-sweep re-run, reported). Mock-first held (watcher + BetLog row).
Build delegation pattern used ×4 (Build 1, Build 2, Feedback 1, UI pass #3).
Git autonomy: bethub-v3 `2e9abd3` → `abd84e1` pushed (green). Capture-side
changes deployed **uncommitted** by design, `.pre-*-bak` backups left.
Feedback 2 explicitly NOT built (recorded).

## Live-integration honesty (S189)
- **Live-proven:** TAB transport, capture, soft-odds endpoint (post perf
  fix), Build 2 live endpoint, tool-side reads through the tunnel.
- **Implemented-not-live** (need the next race-day look — TAB thoroughbred
  race into the jump): the on-screen TAB auto-fill refresh, Build 2
  fast-refresh, book-driven fill, and the watcher Calls. UI pass #3 all
  display-only, same bucket.
- Watcher grade **bands = first cut**, not tuned.

## Governance / state at close
bethub-v3 HEAD `abd84e1` (UI pass #3 uncommitted, build agent live);
suites backend 1530 / frontend 249 green as of `abd84e1`. Capture VPS:
soft-odds perf fix + Build 2 transport/endpoint + `.env` load, all
deployed + running, uncommitted, backups left. No money paths touched all
session. Rebuild root clean.

## Forward routing
**S246 first action = triage `ui_pass3_report.md`** (guarded: if present
triage; else the build is still running → hold for it). Then the operator's
**TAB live look** (thoroughbred race into the jump — the one outstanding
live-proof for the whole TAB + watcher + book-driven batch). Then the
finish-v3 sequence continues: **B2 money-safety doors → UI residuals →
triage sitting (D) → forensic money-surface review → cutover flip.**
