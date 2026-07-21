# B6 small-builds brief — worker visibility (r11), placement tripwire (r2), money-store backup

**Commissioned:** Session 231, 2026-07-06. Source scope: `b6_scope.md` Part 3 (operator-reviewed,
all held calls resolved at S231).
**Status:** LOCKED — ready for a Claude Code session.
**Target repo:** `~/Desktop/Projects/bethub-v3` — READ-WRITE. Expected start HEAD `a4cdab3`
(= origin/main, clean tree). If the tree is dirty or HEAD differs, STOP and report before editing.
**Bounded:** one session, three build items, nothing else. Suite baseline: **1383 backend green
(`uv run pytest`), 130 frontend green (`cd ui/web && npx vitest run`)** — both must be green at
finish, with the new tests added on top.
**Bet-safety:** NO Betfair contact. Any launch verification runs `BETHUB_BETFAIR_MODE=mock` with
`BETHUB_LAUNCH_NO_BROWSER=1` and `BETHUB_VPS_TUNNEL=0`. The live store (`data/bethub.db`) is
READ-ONLY for this build — item C copies it, never writes it.
**Git (S227 autonomy):** commit after the work lands, green tree only, descriptive message +
Claude co-author trailer, push to origin. Never commit `*.db*` or secrets (`.gitignore` enforces).
**Report:** write `~/Desktop/Projects/bethub-rebuild/b6_small_builds_report.md` — what changed,
file-by-file; test evidence (counts before/after); the tested-restore transcript (item C);
deviations flagged; finish HEAD.

---

## Why this build exists (context in one paragraph)

The cutover panel (unanimous GO-WITH-CONDITIONS) set nine hard gates before v3 becomes the
system-of-record. Three of them are small code builds, bundled here: **gate #2** (r11 — worker
state must be visible at launch; a silently-off worker is the panel's loudest correction),
**gate #8** (r2 — a tripwire test fencing a dormant placement function), and **blind-spot #1**
(the v3 money store is one SQLite file with no backup — cheapest check, worst downside). The
gate-#5 worker-defaults decision (RESOLVED S231: both workers ON by default at every launch,
explicit opt-out for dev only) is enforced here too — same code territory as r11.

---

## Item A — r11: worker visibility + gate-#5 default enforcement

**Problem (grounded).** `BetHub.command` (repo root) exports `BETHUB_BETFAIR_MODE`,
`BETHUB_CAPTURE_API_URL`, `BETHUB_BETFAIR_BACKOFF_PATH` — but never touches or echoes the two
worker flags. `ui/api/config.py` has `settlement_worker: bool = False` (opt-in, safe-by-default)
and `reconciliation_worker: bool = True` (opt-out). So today a live launch starts with
auto-settlement silently OFF unless the operator remembered the env var — exactly the
fault-masking the panel promoted to a hard gate. Additionally, the worker-health registry
(`ui/api/worker_health.py`, served by `/api/health/workers` in `ui/api/routers/health.py`) only
reports workers that actually **registered** — a worker that was expected but never started is
simply absent from the snapshot, `healthy` stays true, and the frontend fault banner stays
silent. Absent-expected is invisible at both surfaces.

**Build.**

1. **Launcher enforces the gate-#5 policy.** In `BetHub.command` live mode: default BOTH flags
   ON (`BETHUB_SETTLEMENT_WORKER=${BETHUB_SETTLEMENT_WORKER:-true}`, same shape for
   reconciliation), so an operator double-click always launches with both workers on. An
   explicitly-set env var still wins (that IS the dev opt-out — no new flag needed). Do not
   change the `config.py` code default: safe-by-default for bare imports/tests stays; the
   launcher is where the operational policy lives.
2. **Launcher echoes worker state.** After the health check passes, the launcher prints both
   worker states clearly (e.g. `SETTLEMENT_WORKER: ON` / `RECONCILIATION_WORKER: ON`, or a loud
   `⚠ OFF` line when one is disabled). Read the truth, not the intent: query
   `/api/health/workers` (curl + a small parse is fine) so the echo reflects what actually
   started, not just what was exported.
3. **Expected-but-absent worker = visible fault.** Teach the health surface which workers are
   *expected* (from the resolved settings: live mode + each flag) and mark the response
   unhealthy — with a per-worker "expected but not running" status — when an expected worker
   never registered or has stopped. The existing frontend banner polls this endpoint; making
   `healthy=false` with a clear reason surface through the banner is the goal. Touch the
   banner's copy only if needed to render the new state legibly; no frontend redesign.

**Acceptance (gate #2, judge's wording).** A launch visibly prints SETTLEMENT_WORKER /
RECONCILIATION_WORKER state; a deliberately-disabled expected worker produces a visible alert.
Verify with a mock-mode launch for the echo path, plus unit tests on the health endpoint for
the absent-expected fault (live-mode assertions via settings injection, not a real Betfair
session). Frontend: if the banner rendering changed, `npm run build` so the served bundle is
current (the launcher's staleness rebuild also covers this — don't rely on memory, check).

## Item B — r2: tripwire test on the dormant placement function

**Problem (grounded).** `place_hedge` (`workflows/bet_entry/v1/orchestrator.py`, ~line 780)
has no production caller — placement goes through other entry points — and it lacks the stake
invariant the wired paths carry. Latent overpay vector if some future change wires it up
without noticing.

**Build.** One test (suggested home: `tests/workflows/bet_entry/v1/test_orchestrator.py` or a
dedicated `test_r2_tripwire.py`) that statically scans the production source tree (`ui/`,
`workflows/`, `domain/`, `clients/`, `store/`, `contracts/` — exclude `tests/`) and FAILS if
any call site of `place_hedge(` exists outside its own definition module. Keep it dumb and
grep-like (AST or text scan — Code's call); the point is a fence, not elegance. Include a
comment naming WHY: the function is caller-less by design and must not gain a caller until the
stake invariant is added — panel gate #8.

**Acceptance (gate #8, judge's wording).** That test exists and is green (i.e., still
caller-less); any future caller turns the suite red. Prove the red path once during the build
(add a throwaway caller, watch it fail, remove it — note this red-proof in the report).

## Item C — v3 money-store backup + one tested restore

**Problem (grounded).** The operational store defaults to `<repo>/data/bethub.db`
(`BETHUB_DB_URL` / `BETHUB_DB_PATH` overrides — resolve the same way the app does). It is
git-ignored (correctly) and has no backup of any kind. Post-flip, a lost or corrupt file is
total operational-state loss.

**Build.** Automated, timestamped backups:

- **On every launch:** `BetHub.command` takes a backup BEFORE uvicorn starts (nothing is
  writing at that moment, which sidesteps most WAL hazards — but still use an SQLite-safe
  method: `sqlite3 <db> ".backup <dest>"` or `VACUUM INTO`, never a raw `cp` of a live WAL db).
- **Daily:** a scheduled mechanism (launchd plist, or a date-check inside the launcher run —
  Code's call; the operator's machine is a Mac and v3 currently only runs attended, so
  launcher-driven "backup if today's not done yet" is acceptable and simpler than launchd).
- **Destination:** outside the repo working tree (suggested `~/.bethub/backups/`), timestamped
  filenames, retention pruned to a sane count (suggest keep last 30) — design details are
  Code's to fix, the acceptance is not.
- **Documented restore, tested once for real:** stop the app, restore a backup over a scratch
  copy (NOT the live file), open it, verify row counts / a known recent bet is present. Write
  the exact steps into the report AND into a short `ops/RESTORE.md` in the repo so the
  procedure survives outside session memory.

**Acceptance (blind-spot #1 / DAY-10).** Backups appear automatically (launch + daily); a
restore has been performed successfully once and its steps are written down.

---

## Out of scope — hard fence

NO edits to placement, settlement, reconciliation, or any money logic (item B is test-only;
item A touches the launcher, health surface, and banner only). No forensic-review blind-spot
items (crash-recovery, double-place, adversarial API — those belong to the later review). No
accounts/books seeding. No dependency upgrades. If any item can't land inside the fence,
STOP on that item, note it in the report, and land the rest.

## Order of work

B (smallest, pure test) → A (launcher + health) → C (backup + restore proof). Run the full
suites after each item; commit per item or as one commit at the end (Code's call — green
either way).
