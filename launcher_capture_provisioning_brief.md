# Launcher capture-data provisioning — brief

**Status:** LOCKED — Session 202, 2026-06-29 22:35 ACST. Operator
locked the path; corrections from the S202 read-only investigation
(`launcher_capture_provisioning_investigation_report.md`) folded in.
Execution proceeds via the two follow-on briefs named in §6 — nothing
is built before those are drafted and the operator gives go.
**Drafted:** 2026-06-29 ~19:25 ACST (Session 202, headless runner,
DR-021 Adelaide anchor). **Locked + corrected:** 2026-06-29 22:35 ACST.
**Grounding:** live read-only — Mac launcher + v3 code, VPS `capture.db`
(`mode=ro`, never copied) over the 8400 tunnel. Done this session
before drafting (S202 first action, two-part grounding).
**Governing DRs:** DR-033 (placings analytical / settlement
Betfair-only), DR-027 / DR-028 (two-database boundary + single
integration point — re-read trigger fired: this brief touches the
cross-DB seam), DR-021 (Adelaide anchors).
**Bet-safety:** this brief is analytical/governance. Provisioning is a
read-only data link + launcher hygiene. It does **not** touch
settlement, money, lay placement, or any live-betting write path.

---

## 1. The problem in one line

The "Log Past Bet" late-entry flow (race lookup → pick runner → log)
is the only v3 feature that reads the analytical store `capture.db`,
and it is **non-operational in the launched app** — every race lookup
returns HTTP 500 because the launcher never tells the app where
`capture.db` is. This has been true and unchanged since Session 189.

Plain version: when you go to log a bet after the fact and need the
tool to look the race up for you, it falls over. It has never worked
in the real launched app — only in tests against a fake data file.

---

## 2. What the grounding confirmed (S202, this session)

**2a. The link is still missing — S189 blocker unchanged.**
- The launcher `BetHub.command` exports only the Betfair mode and the
  Betfair credentials path (lines 75–78). It sets **no**
  `BETHUB_CAPTURE_DB_PATH`.
- There is **no `capture.db` anywhere on the Mac**, and **no mount**
  of the VPS file. (`find` over Projects → none; `mount` → none.)
- The app's reader (`vps_client`, `_connection.py:29–45`) resolves a
  **file path** and opens it as a read-only SQLite file
  (`sqlite:///file:…?mode=ro`). With no path set it raises at startup
  of the call → the 500. It cannot read a network port — only a file.
- Net: the race-lookup endpoints (`bets.py:925/938/952` +
  `create_manual_bet`) 500 in the launched app exactly as the S189
  audit demonstrated. Re-verified by re-reading the live launcher and
  the live resolver this session.

**2b. The 8400 tunnel is alive — but it's an API, not a file.**
- The tunnel is `ssh -N -L 8400:localhost:8400 root@187.77.183.9`
  (live now). It forwards to a **uvicorn HTTP API on the VPS** that
  serves `capture.db`. `/health` → `status:ok`,
  `collector_active:true`, last Betfair snapshot today 09:44 UTC.
- So over the tunnel there is a working **read API**. But the v3
  reader wants a **file**, so today's tunnel does nothing for the
  launched app. This is the same shape S189 flagged: "the VPS link is
  an API the file-reading client can't use." Unchanged.

**2c. Recent data: lookup is supportable, placings are not.**
Per-date coverage in `capture.db` for the recent window (thoroughbred,
non-trial, `mode=ro`):

| date | runners | finish_position % | betfair_selection_id % |
|---|---|---|---|
| 06-15 | 827 | 0% | 86% |
| 06-16 | 1034 | 0% | 84% |
| 06-17 | 998 | 0% | 84% |
| 06-18 | 1105 | 8% | 100% |
| 06-19 | 2173 | 0% | 91% |
| 06-20 | 2700 | 51% | 86% |
| 06-21 | 1773 | 0% | 69% |
| 06-22 | 895 | 0% | 84% |
| 06-23 | 1104 | 0% | 100% |
| 06-24 | 1348 | 0% | 63% |
| 06-25 | 1445 | 7% | 91% |
| 06-26 | 1953 | 8% | 92% |
| 06-27 | 2127 | 53% | 77% |
| 06-28 | 1374 | 45% | 77% |
| 06-29 | 588 | 16% | 84% |

Read in plain terms:
- **Finding the race and its runners works.** `betfair_selection_id`
  (what the lookup picker needs) sits 63–100% across the window. The
  lookup surface is genuinely supportable once the link is provisioned.
- **Knowing where horses finished does not work yet.**
  `finish_position` is 0% on eight of the last fifteen dates (all with
  results long published) and never above ~53% on the rest. This is
  the once-daily subscription sync that stamps a date once and never
  re-pulls (`vps_supply_review.md` §4) — the same gap the recovery now
  running is grinding back in over ~4–6 weeks. The partial dates are
  the sync getting part-way before it stops; the zero dates are still
  waiting for the recovery.
- **Distinguishing "not pulled yet" from "capture failing":** it is
  the **forward results-pull being once-only / quota-starved**, not the
  capture engine being down. The Betfair side is live to the minute
  (selection IDs, prices). It's the Racing-API *ordinal* (1-2-3-4) that
  isn't landing forward. So: not broken-broken, but not reliable
  forward either — and the recovery is the fix in flight, not this
  brief.

**Consequence for this brief:** even after the link is provisioned,
the supportable manual-entry surface is **race lookup + manual
win/lose + manual placings flag**. Auto-confirming placings (2nd–4th
for insurance) from `capture.db` is **not** supportable now and won't
be until the recovery backfills. Per DR-033 placings settle is a
manual operator flag anyway, so this does not block manual entry — but
the brief must scope the feature to lookup, not to placings
auto-settlement, and say so plainly on the screen.

---

## 3. The provisioning decision (software call — operator confirms)

The question is **how** to make `capture.db` reachable to the launched
app. Three shapes, judged against DR-027/028 (no caching, no
denormalisation, no second integration point — read the canonical
analytical store by reference, once).

**Option A — SSHFS read-only mount of the VPS file.**
Mount the VPS `capture.db` directory on the Mac read-only over the
existing SSH link; point `BETHUB_CAPTURE_DB_PATH` at the mounted file.
- *For:* zero app-code change — `vps_client` works unchanged; reads the
  canonical file by reference (no copy, no cache → DR-028 clean);
  cheapest to build.
- *Against:* SQLite over a network filesystem against a **live WAL**
  database (the VPS is writing snapshots every ~1 min) is a known
  correctness hazard — locking and `-wal`/`-shm` coherence over SSHFS
  can yield stale or inconsistent reads. Needs `macFUSE`/`sshfs`
  installed and the mount re-established on every boot/launch. Fragile.

**Option B — point the app at the existing 8400 API (recommended).**
The robust read path is the one where the read happens **on the VPS**,
where the file is local and the WAL is coherent, and the result comes
back over HTTP. The 8400 API already exists and is live. This means
giving `vps_client` an API-backed mode (read via
`http://localhost:8400/...` over the tunnel) instead of opening a file.
- *For:* no SQLite-over-network hazard; the tunnel is already up; this
  is the **single integration boundary** DR-028 wants (read the
  analytical store through one defined interface, by reference, no
  local copy). Most durable for cutover.
- *Against:* larger change — `vps_client`'s read methods must call the
  API, and the **VPS API must expose the lookup/results endpoints**
  the client needs (only `/health` is confirmed live this session;
  the meetings/races/resolve/results surface needs an endpoint audit
  before this is costed). The launcher must also ensure the tunnel is
  up (or start it) before the app needs it.

**Option C — local synced replica of `capture.db` (rejected).**
Periodically copy/rsync the 4 GB file to the Mac and read it locally.
- *Rejected:* this is precisely the caching/denormalisation DR-028
  forbids — a second, stale copy of the analytical store, with its own
  freshness-drift failure mode. Also the standing "never copy
  `capture.db`" discipline. Do not do this.

**LOCKED OUTCOME (S202, post-investigation).** The endpoint audit and
the read-only investigation are done. The `:8400` API is live and
healthy with 7 GET endpoints — but it is **today-only**:
`/racing/races/today` ignores a `?date=` parameter and every
date-aware variant returns 404. Past-date discovery is impossible via
the API unless the `race_id` is already known, which the Log Past Bet
flow never holds at the start. So **Option B alone regresses the
feature to today's races only** — unacceptable, since the feature
exists to log races that ran days ago. The current SQL/file path
supports any date in a 365-day window.

**Locked path: Option B + a date-aware VPS discovery endpoint.** Add a
small date-parameterised race/results lookup to the `:8400` API
(re-exposing the same SQL the file path already runs), then re-point
`vps_client` at the API. This is the DR-028 single-boundary path and
the shape the tool keeps after cutover — built once, not thrown away.

**Option A (SSHFS) rejected as interim.** Its main objection (stale
WAL reads) is actually weak *for this feature* — past races are static
once stamped — but it still needs `macFUSE`/kernel-extension install
and a mount lifecycle, and it gets torn out at cutover (W16, near). Not
worth standing up a throwaway this close to the line.

**Two corrections from the investigation, folded in (binding on the
execution briefs):**
- **Picker source is `/racing/races/{id}`, not
  `/racing/snapshots/{id}/latest`.** The snapshot endpoint carries
  price-ladder data only and **no `betfair_selection_id`**; race-detail
  carries selection IDs + names and is a superset of `resolve_race`.
- **Connection failure must map to the existing 503 envelope, not an
  unhandled 500.** Today the missing-path case raises a bare
  `RuntimeError` that the route's `OperationalError`-only `try/except`
  doesn't catch → silent 500. The API-backed client must wrap
  transport errors into an `UnavailableEnvelope` (503), mirroring how
  `map_operational_error` wraps `OperationalError` today.

---

## 4. Scope of the feature once provisioned

- **In:** race lookup (date → venue → race → runners with Betfair
  selection IDs), manual runner selection, log the bet, manual
  win/lose, manual placings flag (operator sets it — DR-033).
- **Out (now):** auto-confirming placings (2nd/3rd/4th) from
  `capture.db`. Gated on the placings recovery, not on this brief.
  The screen should state plainly that placings are operator-flagged.
- **Edge cases to carry from `vps_supply_review.md`:** the empty-runner
  edge (a matched-but-not-snapshotted race resolves to an empty runner
  list — Finding A, ~12.5% of recent stamped races) and the
  harness/greyhound mislabel-as-thoroughbred contamination (Finding C).
  Both are lookup-UX papercuts the build should handle gracefully
  (show "no runners captured for this race" rather than an empty
  picker), not blockers.

---

## 5. Carried launcher risks to fold in

This brief is the agreed home for three launcher-hardening items (all
in `BetHub.command` / the auth path) — Code closes them in the same
pass:

- **F9 (MED-HIGH) — Betfair login back-off resets on restart.** The
  login throttle/back-off state is in-memory
  (`_auth_betfair.py:118–120, 54–56`). A process restart wipes it, so
  relaunching during a Betfair outage re-hammers the login — the v2
  ~48h-lockout path. **Fix: persist the back-off state to disk** so it
  survives a restart. This is the most operationally serious of the
  three (account-safety adjacent — a lockout takes Betfair offline for
  ~2 days).
- **F10 (MEDIUM) — double-session via port override.**
  `BETHUB_LAUNCH_PORT` (`BetHub.command:16`) lets a second instance
  start → two concurrent Betfair sessions/streams. **Fix: guard against
  a second concurrent instance** (single-session lock).
- **rebuild-if-source-newer — stale served screen.** The launcher only
  builds the frontend when `dist/index.html` is *absent*
  (`BetHub.command:67`); it does not rebuild when the source is newer.
  Every Code rebuild leaves a stale served bundle until a manual
  `npm run build` (the S172 BetLog trap). **Fix: rebuild when source is
  newer than `dist`.**

> Related but **not** in this brief unless the operator adds it: **F12**
> (TEMPORARY_BAN-port handling + shutdown-logout). Flagged in the same
> launcher-review lineage; can be folded in or kept separate — operator
> call in §6.

---

## 6. Locked decisions (S202)

1. **Provisioning path:** Option B (API-backed) **+ a date-aware VPS
   discovery endpoint**. A and C rejected (see §3).
2. **Feature scope:** lookup + manual win/lose + manual placings flag
   now; auto-placings deferred to the recovery. Screen states plainly
   that placings are operator-flagged.
3. **F9 kill-state policy:** persist the **back-off timer only**
   (`_next_attempt_at` / `_consecutive_failures`), **not** `_killed` —
   a v3 restart still clears a Betfair login kill, preserving today's
   documented contract.
4. **F12:** **out** of this launcher pass (kept in its own lineage).
5. **Picker source** and **failure→503** corrections per §3 are
   binding on the execution briefs.

**Execution split — two follow-on briefs, in sequence:**
- **Brief 1 — VPS date endpoint** (`vps_date_endpoint_brief.md`): the
  small unblock. Adds date-aware race/results discovery to the `:8400`
  API. Drafted first because it unblocks past-date lookup and the Mac
  rewrite depends on it. Touches the VPS API repo, not the Mac app.
- **Brief 2 — Mac `vps_client` API rewrite**
  (`vps_client_api_rewrite_brief.md`): re-points the lookup trio
  (`list_meetings` / `list_races` / `resolve_race`) + `race_results`
  at the API, picker from `/racing/races/{id}`, transport errors →
  503, plus the three launcher fixes (F9 timer-only, F10
  single-session lock, rebuild-if-source-newer). Sequenced after
  Brief 1.

Both briefs are drafted in Chat (S203), reviewed, and only then
handed to Code. No Code work starts before that.

---

## 7. Out of scope / non-goals

- No settlement-worker work (that's the next queue item, its own
  bet-safety framing).
- No change to the recovery (self-running; this brief depends on its
  output but does not touch it).
- No `capture.db` writes, no copy of the file, no v2 changes.
- No promo-seed / cash-modal work (separate queue items).

---

*DRAFT. Grounded against live launcher + VPS this session. Holds for
operator lock; nothing actioned until then.*
