# B6 small-builds report — worker visibility (r11), placement tripwire (r2), money-store backup

**Executed:** 2026-07-06, Claude Code session, against brief `b6_small_builds_brief.md` (LOCKED).
**Start HEAD:** `a4cdab3` (= origin/main, clean tree — verified before any edit).
**Finish HEAD:** `4f98ad5` (pushed to origin/main).
**Outcome:** all three items landed. No fence breaches: no placement/settlement/reconciliation/money
logic touched; no Betfair contact (launch verification ran `BETHUB_BETFAIR_MODE=mock`,
`BETHUB_LAUNCH_NO_BROWSER=1`, `BETHUB_VPS_TUNNEL=0`); live `data/bethub.db` was only ever read.

## Suites

| Suite | Baseline | Finish |
|---|---|---|
| `uv run pytest` | 1383 green (confirmed at start) | **1390 green** (+2 tripwire, +5 health) |
| `cd ui/web && npx vitest run` | 130 green* | **132 green** (+2 banner) |

\* The very first frontend baseline run showed 2 failures — it was running concurrently with the
full pytest suite and the failures were load-induced timing flakes; an immediate clean rerun was
130/130 in 2.6s. Recorded here for honesty; baseline treated as green.

## Commits

1. `14c7e3f` — item B (test-only).
2. `4f98ad5` — items A + C together (they share `BetHub.command`; the brief allowed per-item or
   combined commits — splitting one file's hunks across two commits wasn't worth it).

---

## Item B — r2 tripwire (gate #8) ✅

**New file:** `tests/workflows/bet_entry/v1/test_r2_tripwire.py` (2 tests).

- `test_place_hedge_has_no_production_caller` — grep-like line scan of the production roots
  (`ui/`, `workflows/`, `domain/`, `clients/`, `store/`, `contracts/`; `tests/` excluded;
  `node_modules`/`dist`/`__pycache__`/`.venv` skipped) for `\bplace_hedge\s*\(` outside the
  definition module `workflows/bet_entry/v1/orchestrator.py`. Fails listing every offender
  `file:line`, with the WHY in both the docstring and the assertion message: place_hedge is
  caller-less by design and lacks the stake invariant the wired paths carry — overpay vector.
- `test_fence_is_anchored_to_the_definition` — fails if `place_hedge`'s definition module moves
  or the `def` disappears, so a rename can't leave the fence scanning for nothing.

**Red-proof (performed and reverted):** created throwaway `workflows/_r2_red_proof_throwaway.py`
containing a `place_hedge(request)` call → `test_place_hedge_has_no_production_caller` FAILED as
designed → file deleted → 2 passed. Nothing of the throwaway remains in the tree or the commit.

## Item A — r11 worker visibility + gate-#5 defaults ✅

**`BetHub.command`** (launcher only):
- Live mode now exports `BETHUB_SETTLEMENT_WORKER="${BETHUB_SETTLEMENT_WORKER:-true}"` and the
  same for reconciliation — an operator double-click always launches with both workers ON
  (gate #5, resolved S231). An explicitly-set env var wins: that is the dev opt-out.
  `ui/api/config.py` code defaults are untouched (safe-by-default for bare imports/tests stays).
- After the health check passes, the launcher curls `/api/health/workers` and prints per-worker
  truth (what actually started, not what was exported) via a small python3 parse:
  `SETTLEMENT_WORKER: ON`, or loud `⚠ ... OFF` / `⚠ ... EXPECTED BUT NOT RUNNING — restart
  BetHub; do not trust auto-settlement.` lines. A non-answering endpoint prints a
  worker-state-unknown warning rather than nothing.

**`ui/api/routers/health.py`** (health surface only):
- New `_expected_worker_names()` reuses the exact lifespan start gates
  (`should_start_settlement_worker` / `should_start_reconciliation_worker` against the settings
  resolved the same way `lifespan` resolves them, via `app.state.betfair_settings`), so the
  expectation can never drift from what actually starts.
- An expected worker that never registered gets a synthetic `WorkerStatus` entry with
  `expected_not_running=true, running=false, healthy=false`; an expected worker that registered
  then stopped keeps its real record and gains the fault flag. Overall `healthy` flips false.
  OFF-by-design (mock mode, flag unset) stays invisible — unchanged.
- `WorkerStatus` gained `expected_not_running: bool = False`; fields a synthetic entry can't
  supply got defaults (`started_at` is now nullable). `ui/web/src/api/types.ts` regenerated from
  the app's OpenAPI spec (dumped via `create_app().openapi()` — same generator,
  openapi-typescript 7.13.0, no server needed).

**`ui/web/src/components/HealthBanner.tsx`** (copy only, no redesign): `problemsFrom` renders the
new state ahead of stale/erroring: *"The settlement worker should be running but is NOT — its job
is not being done. Restart BetHub (close the Terminal window and relaunch)."* Cleanly-stopped
unexpected workers are still ignored.

**Tests:** +5 in `tests/ui/api/test_worker_health.py` (never-registered → fault; live-with-flags-
off → invisible; mock-with-flags-on → invisible, gates reused; expected+running → no flag;
registered-then-stopped → fault with real record) — all live-mode assertions via settings
injection on `app.state`, no Betfair anywhere. +2 in `HealthBanner.test.tsx` (banner alert
rendering; `problemsFrom` flags stopped-only-when-expected).

**Acceptance evidence (mock-mode launch, real `BetHub.command` run):** launcher output showed the
staleness rebuild fire (banner change picked up → served bundle current), then

```
  ⚠ SETTLEMENT_WORKER: OFF (mock mode: workers only run live)
  ⚠ RECONCILIATION_WORKER: OFF (mock mode: workers only run live)
```

read from the live endpoint. The deliberately-disabled-expected-worker alert path is proven by
the unit tests above (per the brief: settings injection, not a real Betfair session). Clean
shutdown, port released.

## Item C — money-store backup + tested restore ✅

**`BetHub.command`:**
- `_resolve_db_path()` mirrors `ui/api/dependencies/composition.py::resolve_db_path` exactly:
  `BETHUB_DB_URL` (`sqlite:///` relative and `sqlite:////` absolute) → `BETHUB_DB_PATH` →
  `<repo>/data/bethub.db`. An unsupported URL scheme skips the backup with a loud warning
  rather than backing up the wrong file.
- `_backup_db()` uses `sqlite3 <db> ".backup <dest>"` (online-backup API — WAL-safe; never a
  raw `cp` of the live db) into `~/.bethub/backups/bethub-YYYYMMDD-HHMMSS.db`
  (override: `BETHUB_BACKUP_DIR`), then prunes to the newest **30**. A failed backup removes
  the partial file and warns loudly.
- **Every launch:** `_backup_db` runs before uvicorn starts (nothing writing at that moment).
- **Daily:** a background loop (same pattern as the tunnel watchdog, reaped on shutdown) checks
  hourly whether today already has a backup and takes one if not — covers sessions left open
  across days; `sqlite3 .backup` is safe against a live writer. Chosen over launchd per the
  brief's explicit allowance (attended Mac, simpler).
- Observed live during the mock launch: `Money-store backup:
  /Users/tim/.bethub/backups/bethub-20260706-193003.db`.

**`ops/RESTORE.md`** (new): full operator procedure — stop the app, pick a backup, verify it on
a scratch copy first, move damaged live files (+ `-wal`/`-shm` sidecars) aside rather than
deleting, copy the verified backup into place, relaunch and reconcile anything newer than the
backup against the Betfair statement.

**Tested restore transcript (performed for real, scratch copy — live file untouched):**

```
Using backup: /Users/tim/.bethub/backups/bethub-20260706-193003.db
cp "$BACKUP" $SCRATCH/restore-test/bethub.db
sqlite3 restore-test/bethub.db "PRAGMA integrity_check;"   → ok
Row counts, restored vs live (live opened read-only, file:...?mode=ro):
  bets             9 = 9
  bet_legs         9 = 9
  accounts         1 = 1
  cash_flow_events 0 = 0
  promo_events     0 = 0
Known recent bets present in the restored copy, incl. the S227/S228 live-proof records:
  bet-0dc0c309-… | LAY | matched_stake 3.15 | settled_lost | betfair 434257406420
  bet-df31ffcd-… | LAY | matched_stake 5.26 | settled_won  | betfair 433957436009
```

Daily-glob and prune expressions sanity-checked standalone (today-already-backed-up → skip;
prune candidate count 0 at 1 backup).

## Deviations / judgement calls (all inside the fence)

1. **Backup failure does not abort the launch** — it warns loudly ("fix this before betting
   on") and continues. The brief was silent; blocking the whole tool on a backup error felt
   wrong for an attended launcher. Flag if you want it fatal.
2. **Backups run in mock launches too** — "on every launch" taken literally; a mock launch
   backing up the real store is free safety.
3. **Items A and C share one commit** (same file); B is its own commit. Brief allowed either.
4. **types.ts regeneration** used the spec dumped from `create_app().openapi()` instead of the
   package script's live-server URL — same generator and output, no server required.
5. First concurrent frontend baseline run flaked (2 timing failures under full-suite load);
   clean rerun green. Noted under Suites.

## Gate status after this build

- **Gate #2 (r11):** MET — launch prints both worker states from the live endpoint; a
  disabled/absent expected worker produces a visible alert (banner + launcher line + unhealthy
  endpoint).
- **Gate #5:** ENFORCED at the launcher — live double-click = both workers ON; env var = dev
  opt-out.
- **Gate #8 (r2):** MET — tripwire green, red path proven once.
- **Blind-spot #1:** CLOSED — automatic launch + daily backups, retention 30, restore tested
  and documented in-repo.
