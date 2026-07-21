# Placings-recovery — root-cause review (read-only diagnosis)

**Date:** 2026-07-02 (Adelaide). **Mode:** produced by a read-only multi-agent
investigation — `capture.db` opened `mode=ro` only; live Racing-API probes were
fetch-only GETs; no VPS edits, git writes, or service/timer/schema changes made
*during the diagnosis*. **Scope:** capture-side (Racing-API analytical) only — no
Betfair / settlement / money path, no bethub-v3.

**Operator decision (2026-07-02):** proceed with **FIX 1 only** (the empty-runners
detect + re-fetch in `subscription/racing_api.py`); re-timing, ordering change,
provider escalation, and hygiene/refactor are **deferred** — re-timing gated on the
20:00-UTC probe (§4). FIX 1 was implemented in a follow-on bounded session after
this review; this document is the diagnosis it rests on.

---

## Why this review exists

~36,000 historical thoroughbred finish positions ("placings") have failed to
backfill into the analytical `capture.db` for weeks. **Nine** surgical fixes each
cleared one symptom and hit the next wall. The current wall is
`post_retry_truncated` — HTTP-200 responses with the `races` array populated but
every nested `runners` array **empty** ("empty-runners"), which survive the client
retry. This review answers: (1) the definitive root cause + the fix that will hold,
and (2) an evidence-based worth-it call (recover / retire / defer), since the only
consumer — an analytics layer — is not built yet but is coming into view.

The diagnosis has drifted three times, which is the reason to distrust the current
frame:

| Session | Model of the failure | Lever applied |
|---|---|---|
| S198/S201 | HTTP-429 **daily quota** | raise nightly ceiling |
| S211 | per-second **rate limit** / empty-200 | client retry on empty-races; pacing 1.5→0.2s; **re-time 23:30→05:30 ACST** |
| S212–S218 | **local `capture.db` write-contention** with the collector | within-date fetch/write decouple (S213); diagnosis only |

Produced by a read-only investigation: three parallel area probes (codebase, VPS,
API) + three adversarial verifiers + two follow-up forensic agents, with live
fetch-only API probes and full log/DB forensics on the VPS.

---

## 1. ROOT CAUSE

### 1.1 What it is NOT — the write-contention theory is refuted (HIGH confidence)

The S212–S218 root cause ("our local `sync_day` write path, contending with the
live collector on the shared `capture.db`, makes the remote API return empty
runners") **is wrong**. A local SQLite write cannot alter a remote API's response
body for an independent HTTP GET, and the evidence now shows it never did:

- **The nightly run walls with the collector provably ASLEEP.** The timer fires at
  05:30 ACST = 20:00 UTC. The collector (`racing-capture.service`, a single
  process) is *diurnal* and writes **zero** `bookmaker_snapshots` rows for every
  Adelaide hour 01:00–08:59 (14-day profile + a direct spot-count of the last
  overnight = 0 rows). It isn't even started until 08:30 ACST. Yet the 20:00-UTC
  run walls 6/6 `post_retry_truncated`, net **+0** placings, every night
  (`backlog_recovery.log`, 2026-06-29 → 07-02).
- **The box is idle.** Single core, load 0.03, **81.8% idle CPU / 0 IO-wait even at
  the daily peak**, SSD, WAL stable at 4.3 MB, 3.5 GB of the 4.18 GB DB in page
  cache. Nothing to saturate — and the collector is off at run time regardless.
- **Under the OLD code, the write path filled ~111/115 dates FULL *while the
  collector was actively writing*** (2026-06-24 14:00 UTC / 23:30 ACST peak;
  11,637 runners). If contention caused empty-runners, that run had to wall — it
  did the opposite. (The last ~4 recent dates were 0 runners simply because the
  provider had not resulted them yet — normal, not the failure mode.)
- **The connection carries a 5 s busy timeout** (`sqlite3.connect` default
  `timeout=5.0` → `sqlite3_busy_timeout(5000)`), so even real lock contention is
  absorbed, not surfaced. (An earlier note of "busy_timeout=0" was mistaken — the
  *PRAGMA* is unset, but the driver default applies.)
- **S212's own "throwaway-DB immune vs real-DB degraded" experiment was a
  confound:** the 4.18 GB real DB writes far slower than an empty throwaway DB, so
  only the slow run *dwelt* long enough to overlap an intermittent API blip; and
  every fetch-only control used a 0 s inter-date gap while every write run used a
  1.0 s gap — "fetch vs write" was perfectly confounded with request-stream
  spacing. S212 rated its own HTTP mechanism only MEDIUM / "provider black box."

**Corollary that reverses the collector story:** the API is **healthiest during
peak collector hours** and **degraded when the collector is asleep** — the exact
inverse of the contention theory. Off-peak daytime multi-date runs (~03–05 UTC ≈
12:30–14:30 ACST) succeeded full on 06-28, 06-29, 07-01; a fetch-only probe at
04:51 UTC returned **full** runners for every currently-walling date incl. the
deepest March date; while the 20:00-UTC nightly is persistently empty.

### 1.2 What it IS — provider-side empty-runners degradation, exposed by the 2026-06-25 ordering change, made permanent by a missing retry

Three layers, in order of certainty:

**(a) The degradation is API-side (provider).** The empty-runners body is
generated by the Racing API's own Heroku origin: `via: 2.0 heroku-router`,
`cf-cache-status: DYNAMIC` (not cached), a *complete, valid* ~625-byte gzip body
with races present and every `runners:[]` empty and **no** error/notice field.
Those two headers are byte-identical on healthy responses, so only the empty
arrays are diagnostic. This is not a Cloudflare block (that is a 429/403, never a
200), not a rate/quota limit (openapi.json documents *only* 5 req/s per endpoint,
no daily quota, no concurrency limit; the documented failure is 429), and not a
truncated read (the body is complete). The most likely provider mechanism: the
endpoint builds the race scaffolding, then a **separate runner sub-query
intermittently returns empty** (backend DB/pool contention or a swallowed
statement timeout) under the provider's own load. It is **intermittent, recovers
on plain re-fetch** (proven repeatedly), and appears **worse/more sustained around
20:00 UTC** and **worsening day-over-day** at a fixed clock hour (the same 15-date
re-pull at ~14:01 UTC collapsed 2,348 → 124 runners over 4 days).

**(b) The 2026-06-25 code change turned intermittent, mostly-invisible provider
flakiness into a persistent nightly wall.** The onset is abrupt and verified at the
log boundary. The only source change at that boundary is `get_unsynced_dates()` in
`scripts/backfill_race_metadata.py`, rewritten from *oldest-first, unbounded
(~115 dates)* to **recent-first, trailing-14-day (~15 dates)** (confirmed against
git HEAD baseline + the live file + the S191 report; the per-date request pattern
and pacing were untouched). Why this matters:
  - **Recent-first leads the run with today + the freshest dates** — exactly the
    data the provider's backend is actively churning on (ingesting results), where
    empty-runners is most likely; oldest-first led with cold, fully-resulted March
    data and rode through.
  - **The bounded 15-date window removed the "harmless historical fills"** that
    used to dominate each run, so a run that hits the degraded state now has
    essentially nothing left to show → visible net +0.
  - **Smoking gun (run-shape sensitivity):** date 2026-06-20 returned **1,788
    runners fetched alone** at 12:31 UTC but **0 runners** as position-6 of a
    multi-date run **8 minutes later** — same date, same code, same provider.

**(c) The fatal amplifier — the empty-runners mode is the ONE mode with no
retry.** In `subscription/racing_api.py`, `_fetch_meet_races` (~lines 268–301)
retries only the empty-*races-list* mode (1-2-4 s backoff). When the races list is
non-empty but every `runners` array is empty, it returns **success,
`degraded=False`, no retry**. The detector `_log_empty_runners_signature` *already
computes* "all runners empty" and returns True/False — but the return value is
**discarded** (instrumentation only). Worse, the date-level guard
`if races_synced>0 and runners_synced==0` fires only when an *entire* date is
empty; a **partial** date (some meets full, some empty-runners) passes as
"complete," silently stranding those placings with no wall, no strike, no retry.
This is how ~36k placings strand invisibly, and why every night nets +0: the one
degradation actually firing has no recovery path.

### 1.3 The one open question, and the decisive experiment

What the evidence does **not** yet separate: whether the nightly emptiness is
**(i) purely provider/time-driven** (a sustained bad window around 20:00 UTC that
our run merely samples) or **(ii) partly triggered by our multi-date recent-first
request pattern** from one source IP/key. Both are downstream of the same trigger
(a multi-date sweep against an intermittently-degraded API), and — importantly —
**the recommended fix holds under both.** The clean way to settle it is one
read-only experiment (see §4): a fetch-only probe of the walling dates *at the
timer's firing hour* (20:00 UTC), compared against a known-healthy hour (04:51 UTC
already = full), plus an API-health-by-hour map. If fetch-only is also empty at
20:00 UTC → (i), the levers are retry + re-time to a healthy UTC window +
escalate to the provider. If fetch-only is full at 20:00 UTC while the write run is
empty → (ii), the additional lever is changing the request pattern (revert the
recent-first ordering / de-burst). The validated probe already exists at
`/tmp/probe_fetchonly.py` on the VPS.

---

## 2. Is re-timing enough, or is a structural fix needed?

### Critique of the operator's candidate (re-time to a quiet collector window)

**Reject as framed — it is a no-op, twice over.** (1) The timer already fires at
05:30 ACST, dead-center in the 8-hour zero-collector-write window, and it still
walls — so re-timing *away from the collector* changes nothing. (2) The collector
was never the cause; the API is in fact healthiest during peak-collector hours.
The operator's instinct (schedule matters) is *half* right, but aimed at the wrong
target: what matters is the **provider's** health-by-hour, not the collector's.
And S211's earlier move (23:30→05:30 ACST) was an unverified guess that plausibly
landed the run in a *worse* provider window (20:00 UTC). **Re-timing must not be
repeated as another unverified guess** — pick the slot from an API-health probe
(§4), not intuition. Critically, because the degradation is intermittent
*everywhere*, re-timing alone can never be sufficient: the pipeline must self-heal
regardless of window.

### The fix that will hold (ranked; robust regardless of (i) vs (ii))

**FIX 1 — Add an empty-runners detect + re-fetch (PRIMARY, must-have, ~15 lines).**
The single highest-leverage change and the first fix in nine sessions that cures
the *symptom mechanism-independently* instead of betting on a cause. In
`_fetch_meet_races` at `racing_api.py:274–278`: use the `True/False` that
`_log_empty_runners_signature` already returns; on "races present + all runners
empty," back off **≥2 s** (past the measured ~2 s reset) and re-fetch, reusing the
existing retry loop and backoff; on persistent empty after N attempts, return
`degraded=True`. `sync_day` already treats `degraded=True` as truncated → soft-wall
(no strike, retried next night), so **no downstream change is required**. Fixes
both the whole-date and the silent partial-date cases. Void-vs-degraded
discrimination must use **persistent-empty** (accept only after N re-fetches) —
*not* a `race_status` check, because `race_status` is not parsed in the client.

**FIX 2 — Re-time to a provider-healthy UTC window, chosen from data (gated on the
§4 probe).** Preliminary evidence points to ~03:00–05:00 UTC (≈12:30–14:30 ACST)
being healthy — which is peak collector, but daytime runs prove collector
co-presence is harmless (5 s busy timeout, WAL, they succeed). This *inverts*
S211's move. Confirm with the API-health-by-hour map before changing the timer.

**FIX 3 — If the probe shows (ii): revert/soften the 2026-06-25 recent-first
ordering.** Test oldest-first (or de-bursted) selection for the backlog/recovery
pass, since that ordering coincided with the onset and empirically rode through
before. Targeted, low-risk, addresses the one code change at the boundary.

**FIX 4 — Escalate to theracingapi.com.** A recurring, worsening, intermittent
HTTP-200-with-populated-races-but-empty-runners is a provider defect. Report it
with the captured signature (cf-ray, status, headers, body shape). Especially
load-bearing under (i).

**Deliberately NOT the fix:**
- **Whole-run fetch-all-then-write-all.** Feasible (~166–650 MB, fits) but *low
  value and risky*: it targets the refuted write-timing location, sacrifices crash
  durability on a zero-swap box, regresses wall semantics, and — since the cause is
  API-side — the long API burst still happens (it becomes one uninterrupted 92-date
  burst). Only reconsider if the §4 probe proves a pure dwell effect a fast
  continuous fetch demonstrably avoids.
- **Batched commits / staging DB.** Contention is refuted; this doesn't touch the
  cause. The ~1,801 self-committing transactions per date (`synchronous=FULL`, WAL)
  are chatty *hygiene* worth improving later (session-level
  `busy_timeout`/`synchronous=NORMAL` on the backfill connection only), not the fix.

**Why this holds where nine fixes did not:** every prior fix cured one *presumed
cause* pathway (quota ceiling, pacing, empty-races retry, within-date decouple,
re-time-vs-collector) and hit the next uncovered pathway — and the one mode
actually firing (empty-runners) is the one mode with *no retry*. FIX 1 closes that
gap mechanism-independently; FIX 2/3 remove the *exposure* using measured data
instead of a guess; FIX 4 addresses the deteriorating external condition.

---

## 3. Worth-it: recover / retire / defer

**The numbers (read-only, exact predicate):**
- Recoverable deficit = **36,033 runners across 92 dates** (2026-03-15 → 2026-06-17);
  `exhausted = 0` confirmed. **100% proven recoverable** — a fetch-only probe pulled
  every walling date full, including the deepest (2026-03-15).
- Age: >90d **6,651** / 19 dates; 60–90d **12,746** / 29; 30–60d **11,263** / 29;
  <30d(>14d) **5,373** / 15. (S218's "only ~5–6 old dates ~6k need recovery" is
  wrong; the deep-stuck set alone is 19 dates / 6,651.)
- **The "two-speed drain" is refuted.** The recent sync only touches race_date ≥
  now−14d; the entire deficit is older, so **0% drains organically** — all 92 dates
  need the (walled) recovery pass. Worse, the recent pass is *also* hitting
  empty-runners with no retry, so **~230 runners/day of NEW deficit are being
  manufactured** as unfilled dates age past 14 days. **Doing nothing means the
  deficit grows.**

**The three paths:**
- **(i) Recover-and-drain — RECOMMENDED (evidence under the operator's call).** Cost
  is low: FIX 1 (~15-line retry) stops the bleed immediately (the recent pass
  self-heals) and lets the backlog drain over nights; or a one-off fetch-only sweep
  in a healthy window clears all ~1,200 stuck meets in ~7 minutes of fetching.
  Benefit: the full, proven-available 36k for the imminent analytics layer, and the
  ~230/day bleed stops. Risk: low.
- **(ii) Retire-the-oldest.** Near-zero cost but discards *proven-available* data a
  forthcoming consumer will want, and does **not** stop the bleed. False economy
  unless the analytics layer will provably never need pre-90d finish positions.
- **(iii) Defer.** Deferring the *historical sweep* is tolerable (do it post-fix in
  a quiet window). Deferring the *fix* is the worst option: the deficit compounds
  ~230/day and the stall alert keeps firing. There is no evidence of imminent
  provider purge of old results, but there is no SLA either — sooner de-risks.

**Net:** ship FIX 1 now (cheap, stops the bleed, mechanism-independent); do not
retire; do not defer the fix. The recover/defer split on the *historical* 36k is
genuinely the operator's call — this review puts the numbers under it.

---

## 4. Concrete next steps (ordered)

1. **Run the decisive read-only probe (settles §1.3 and chooses FIX 2's slot).**
   At ~19:55–20:10 UTC (05:25–05:40 ACST), run `/tmp/probe_fetchonly.py` (already
   validated, fetch-only, never opens `capture.db`) over the exact walling dates,
   and compare with a healthy-hour run (04:51 UTC = already full). Extend to a
   fetch-only **API-health-by-hour map** (same handful of dates probed at several
   UTC hours) — the schedule input, analogous to the collector load profile. Pure
   GETs, well under 5 req/s.
2. **Implement FIX 1** (empty-runners retry at `racing_api.py:274–278`) — the
   must-have, independent of the probe result. *(Done in the follow-on session.)*
3. **Apply FIX 2** (re-time to the probe-chosen healthy UTC window) and, if the
   probe shows (ii), **FIX 3** (revert recent-first ordering).
4. **Escalate to the provider** (FIX 4) with the captured empty-runners signature.
5. **Drain the historical 36k** via the recovery pass over nights, or a one-off
   fetch-only-then-write sweep in the healthy window; re-measure the deficit.
6. *(Optional hygiene, later)* session-level `busy_timeout`/`synchronous=NORMAL`
   on the backfill connection; fix the `_sync_single_race` arity bug (returns a
   2-tuple on missing/invalid `race_number` but the caller unpacks 3 → the race is
   silently dropped); revive the effectively-dead `BACKLOG_MIN_DELAY` (the argless
   service's `delay=1.0` overrides the 0.2 s pace via `max(...)`).

## 5. Verification (how to confirm the diagnosis + fix)

- **Confirm the root cause:** the §4 probe. Fetch-only empty at 20:00 UTC ⇒
  provider/time (i); fetch-only full at 20:00 UTC while the write-run is empty ⇒
  run-pattern (ii). Either result is consistent with "not local contention."
- **Confirm FIX 1 works:** after deploy, watch `metadata_backfill.log` — an
  empty-runners meet should log a re-fetch and recover to full runners; a run that
  previously netted +0 should net positive; `backlog_recovery.log` deficit should
  fall night over night. Quick before/after: run the recovery pass in the healthy
  window and confirm placings flow (`_count_filled` rises; deficit drops).
- **Confirm the drain + no regression:** re-measure the recoverable deficit
  (`mode=ro`) trending to ~0; confirm the ghost-row tripwire stays silent (no new
  race rows created), consistent with all prior burns.

---

## Appendix — key evidence, corrections, and minor findings

- **Deficit / load / resource numbers:** direct `mode=ro` SQL + systemd reads
  (§1.1, §3). Collector 24h profile: hours 01–08 ACST = 0 rows; peak hour 14 ACST =
  8,956 rows/hr; S218's "~15k rows/min" is wrong (measured peak ~284 rows/min).
- **Onset:** log boundary 2026-06-24 (last full, 11,637 runners) → 2026-06-25
  (first recent-first / "15 date(s)" / date-1-only). Code change pinned via git
  HEAD (`5f71488`, 2026-03-04) vs live file vs S191 report.
- **Corrections to prior reports:** (1) busy_timeout is 5 s, not 0; (2) the
  2026-06-24 run was ~111/115 full (recent tail unresulted, not a failure);
  (3) `race_status` is not parsed → use persistent-empty, not a status check;
  (4) retirement is *armed* (`not BACKLOG_FREEZE_RETIRE` = True) — `exhausted≈0`
  only because degradation is mis-binned as soft-wall, never "resultless"; FIX 1
  keeps it that way (safe).
- **Scope/safety:** capture-side (Racing-API analytical) only; no Betfair /
  settlement / money path, no bethub-v3, touched. The collector does not call the
  Racing API (Betfair is not in this loop). All investigation read-only.
