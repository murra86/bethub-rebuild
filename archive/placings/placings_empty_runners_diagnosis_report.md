# Report — empty-runners degradation: diagnosis + conditional fix

**Brief:** `placings_empty_runners_diagnosis_brief.md` — LOCKED (Session 212, 2026-07-01). Read at session start; all §3 pre-reads consumed in order.
**Status:** EXECUTED — diagnosis-first probe. **Fork resolved to §5.3 branch 3 (adapted): no behavioural change.** One instrumentation-only edit landed (§5.1); no pacing change, no retry added.
**Session:** 2026-07-01, ~13:10–13:55 ACST (DR-021 Adelaide, ACST = UTC+9:30; ≈ 03:40–04:25 UTC). Target `root@187.77.183.9` : `/home/racing/racing-data-capture`.
**Bet-safety:** CLEAN by construction — analytical/capture side only (DR-033). No operational/betting DB, no Betfair operational path, no bet mutation, no `race_date`/identity logic touched.

**Headline:** The empty-runners mode is **real and reproduced**, but the diagnosis overturns the brief's working hypothesis. It is **not** triggered by Racing-API request rate, cumulative volume, or time-of-day — a fetch-only client is **immune at up to ~9.8 req/sec** (nearly 2× the 5/sec ceiling) across 8 sustained dates. The mode is triggered **specifically by the `sync_day` write path against the shared, collector-contended `capture.db`**: writing the identical data to a throwaway DB is immune; adding equivalent artificial latency is immune. It is **intermittent** (fired hard in a ~5-minute window, absent before and after) and **resets within ~2 s of write-idle**. Because the cause is a DB-contention interaction with the live collector (out-of-scope, §9) — not a pacing- or provider-tier problem — **no pacing config defeats it (branch 1 rejected)** and **retry-defeatability under real degradation could not be verified (branch 2 not supported)**. This reframes the follow-up from "rate-tier / provider question" to an **architecture/operational contention question** for operator triage.

---

## 0 — Method & experiment timeline

Diagnosis strictly preceded any edit (§6 sequencing). The instrumentation (§5.1) was landed first so the mode could be seen clearly, then the sweep, then the fork, then verification. All API-side degradation measurements count runners **from the response**, independent of DB writes — because `runners_synced` is a known-unreliable write-side count (RC-2 write-key skips, duplicate/transient responses) per the throughput report; the clean signal is "runners present in the fetched `races` payload".

| # | ~UTC | Experiment | Purpose | Result |
|---|---|---|---|---|
| 0 | 03:40 | `git status`, pre-session snapshots, `mode=ro` baseline | setup + baseline | deficit 40,987; window 40 dates |
| 1 | 03:41 | §5.1 instrumentation → deploy → `py_compile`/import | see the mode | landed, +46 lines |
| 2 | 03:43 | Fetch-only Config A (0.2 s, 4 dates) + recovery probe | reproduce | **mode absent**; signature captured on a genuine-empty meet |
| 3 | 03:45 | Classify isolated empty meet; Config HIGH-RATE (0 s, 8 dates, ~9.8/s) | rate/volume | genuine-empty confirmed; **mode absent at 2× ceiling** |
| 4 | 03:48 | Config SLOW (1.0 s, 3 dates) | complete lever table | **mode absent** |
| 5 | 03:50 | Real `run_backlog_pass(0.2, 40)` — §7 burn | production path | **WALLED** — attempted 7, filled 1, +963, 6 truncated |
| 6 | 03:52 | Fetch-only probe of the just-walled dates | time-window test | full runners — **time-window rejected** |
| 7 | 03:53 | F1(fetch)→W(write)→F2(fetch), same 5 dates | isolate write-vs-fetch | F1/F2 clean, **W degraded** — write path is the trigger |
| 8 | 03:57 | A/B/C/D: throwaway-DB, latency-mimic, real-DB writes | mechanism | only real-`capture.db` write degrades (D); **contention isolated** |
| 9 | 04:02 | W-SLOW / W-PAUSE / W-VSLOW write-path pacing | branch-1 test | all still degrade — **no pacing floor** |
| 10 | 04:08 | Patched runners-empty retry, write path (3 then 8 dates) | branch-2 test | mode did not fire — **retry-defeat unverified**; intermittency shown |
| 11 | 04:20 | `mode=ro` after-state + ghost tripwire; git diff/status | verify + close | deficit → 36,650; ghost NIL; dirty-set unchanged |

The collector (`run_collector.py`) was read once (experiment 8) to confirm it does not call the Racing API — never edited.

---

## 1 — Mode characterisation + captured signature (§5.1)

**§5.1 instrumentation landed** in `subscription/racing_api.py` (the only code change this session, +46 lines, pure capture — no behaviour change): a `_log_empty_runners_signature()` helper wired into `_fetch_meet_races`'s success path, plus a module-level `_empty_runners_logged` latch. On the **first** "races present, runner arrays empty" response per process it logs, once, the full status line, response headers, and a compact body shape. This closes the gap the throughput-fix session flagged (its `_degraded_headers_logged` hook fires only on an empty *races-list*).

**The mode, precisely:** an HTTP **200** whose `races` array is fully populated (metadata intact, upserted fine) but every nested `runners` array is empty. Captured signature (representative, three independent captures 03:43–03:50 UTC):

```
EMPTY-RUNNERS degradation (meet met_aus_839431725665):
  status=200  races=6  total_runners=0  per_race_runner_counts=[0,0,0,0,0,0]
  top_level_keys=['races']   notices=None
  Content-Type: application/json   Content-Length: 625   Content-Encoding: gzip
  Server: cloudflare   via: 2.0 heroku-router   cf-cache-status: DYNAMIC
```

Key facts in the signature: it is a **clean 200**, small body, **no** `error`/`message`/`notice`/`warning`/`detail` field — the API does not flag the response as degraded in any way. `cf-cache-status: DYNAMIC` (not a stale cache hit); `via: heroku-router` (origin is a Heroku app behind Cloudflare). Two transfer encodings were observed for the same empty-runners shape — `Content-Length: 625` + `Content-Encoding: gzip` (multi-race meets) and `Transfer-Encoding: chunked` (single-race meet `met_aus_56116793303`) — i.e. the emptiness is content, not a truncated transfer. Nothing in status or headers distinguishes a degraded response from a healthy one **except the empty runner arrays themselves** — so the only viable client-side detector is exactly what the throughput burn already used (`races>0 and runners==0`), which cannot by itself separate a degraded meet from a genuinely runner-less one (that requires a re-fetch — §5.4).

**Two distinct populations produce "races present, runners empty":**
- **Genuinely runner-less meets** (abandoned/void, or meets the API simply never carries runners for): a small, stable background population, ~1–2 per date out of ~20–27 meets. These **stay empty** across isolated re-fetch *and* across 4 retry attempts. Confirmed examples: `met_aus_839431725665` (6 races/0 runners on 5+ isolated fetches) and `met_aus_56116793303` (1 race/0 runners).
- **Degraded meets** under the write-path mode: races-present/runners-empty that **recover to full data** when re-fetched fetch-only. Confirmed transient (below).

---

## 2 — Volume-vs-rate results (§5.2)

The brief's key question was whether the mode is triggered by **instantaneous rate** or **cumulative burst volume**. The controlled sweep answers: **neither** — on the *fetch* path.

### 2a — Fetch-only pacing sweep (counts runners from the API response; no DB write)

Same request pattern as `sync_day` (meets-list → paced per-meet `_fetch_meet_races`), driven through the §5.1-instrumented code.

| Config | inter-meet delay | inter-date pause | achieved req/sec | dates | wholesale empty-runners mode? |
|---|---|---|---|---|---|
| SLOW | 1.0 s | 0 | ~1.0 | 3 | **absent** — full runners every date |
| A (current 0.2 s) | 0.2 s | 0 | 3.1–3.4 | 4 | **absent** — full runners every date |
| HIGH-RATE | 0.0 s | 0 | **8.5–9.8** | 8 | **absent** — full runners every date |

The mode is **absent even at ~9.8 req/sec** — nearly double the nominal 5/sec ceiling, 196 requests in ~21 s — and equally absent at ~1 req/sec. Rate is not the trigger; cumulative volume is not the trigger (8 sustained dates / 196 requests, no onset). Inter-date pause is moot on the fetch path (already absent at zero pause). The only empties observed were the genuine runner-less meets of §1.

Raw per-date runner counts (fetch-only, HIGH-RATE config, in run order) — every date full:

```
2026-04-25: 160 races 1788 runners   2026-05-09: 135 races 1630 runners
2026-04-04: 178 races 1839 runners   2026-05-23: 143 races 1679 runners
2026-05-16: 137 races 1775 runners   2026-03-21: 148 races 1540 runners
2026-06-13: 149 races 1790 runners   2026-04-18: 143 races 1647 runners
```

These are the *same* dates the throughput burn (and this session's §7 burn) walled on with 0 runners — proving the walls were not a property of the dates or the request rate.

### 2b — The reversal: the production (write) path DOES reproduce it

The bounded `run_backlog_pass` burn (§7) walled exactly as the throughput session did. A back-to-back **fetch → write → fetch** isolation on identical dates, one process, ~3.2 req/sec each burst, made the trigger unambiguous:

| Burst | 05-16 | 06-13 | 05-09 | 05-23 | 03-21 |
|---|---|---|---|---|---|
| **F1** fetch-only | 1775 | 1790 | 1630 | 1679 | 1540 |
| **W** write-path `sync_day` | 1133 (partial) | **0** | **0** | **0** | **0** |
| **F2** fetch-only (immediately after W) | 1775 | 1790 | 1630 | 1679 | 1540 |

Fetch-only is immune (F1 and F2 both fully clean, bracketing W); the write path degrades from date 2 (date 1 partially, 1133 < 1775) and **resets instantly** (F2 clean ~2 s later). A **time-window** hypothesis was tested and rejected: a fetch-only probe at 03:52:50 UTC — two minutes *after* the burn walled on these exact dates — returned full runners on all five.

### 2c — Mechanism triangulation

Four bursts isolating write-vs-fetch, DB-target, and timing:

| Burst | 05-16 | 06-13 | 05-09 | 05-23 | 03-21 | verdict |
|---|---|---|---|---|---|---|
| **A** fetch-only (control) | 1775 | 1790 | 1630 | 1679 | 1540 | clean |
| **B** write → *throwaway* DB | 1758 | 1785 | 1622 | 1648 | 1515 | **clean** |
| **C** fetch + 0.3 s/meet latency mimic | 1775 | 1790 | 1630 | 1679 | 1540 | clean |
| **D** write → *real* `capture.db` | 1153 | **0** | **0** | **0** | **0** | **degraded** |

The single variable separating clean-B from degraded-D is the **database file**. Writing the identical data to an uncontended throwaway DB does not degrade; smooth artificial latency does not degrade; only writing to the shared `capture.db` — continuously written by the live collector `run_collector.py` (WAL mode) — degrades. The collector was verified **not** to touch the Racing API (no `racing_api`/`theracingapi`/`sync_day` reference in `run_collector.py` or `capture/orchestrator.py`), so this is not concurrent API load — it is a **local `capture.db` write-contention interaction** that manifests as empty runner arrays on the co-timed Racing-API fetches. The exact HTTP-level cause sits inside the provider's stack (behind Cloudflare/Heroku) and is a black box; the **causal factor on our side is isolated**: contended `capture.db` writes.

### 2d — Write-path pacing does not defeat it (the real branch-1 test)

Because §2a paced only the (immune) fetch path, the write path was paced directly:

| Config | date 1 | date 2 | date 3 | date 4 |
|---|---|---|---|---|
| W-SLOW (inter-meet 1.0 s) | 1699 | **0** | **0** | **0** |
| W-PAUSE (0.2 s + 20 s inter-date) | 1790 | 256 | **0** | **0** |
| W-VSLOW (inter-meet 2.0 s) | 1713 | **0** | **0** | **0** |

No lever defeats it: inter-meet delay up to 2.0 s and a 20 s inter-date pause both still degrade from date 2 (the pause helped marginally — date 2 partial 256 — then collapsed). Date 1 is reliably full; the mode is a *second-date-onward* onset that pacing does not prevent.

### 2e — Intermittency

Critically, the mode is **intermittent**. It fired hard in bursts W and D (~03:50–03:55 UTC) but did **not** fire in any subsequent write-path run: two retry-capable write bursts (3 dates, then 8 dates, ~04:05–04:20 UTC) returned full runners on every date, 0 meets needing retry. This is consistent with dependence on the live collector's *instantaneous* `capture.db` write-load — which tracks live-race density and varies minute-to-minute — rather than on any property of our request stream.

---

## 3 — Fork decision + what was changed (§5.3 / §5.4)

**Decision: §5.3 branch 3 (adapted) — change nothing to fetch/write/pacing behaviour; keep the §5.1 instrumentation; route to operator triage with the mechanism.** No edit to `scripts/backfill_race_metadata.py` (byte-identical to session start). The only code change is the §5.1 instrumentation in `subscription/racing_api.py`.

Reasoning, strictly from the diagnosis:

- **Branch 1 (a pacing config reliably avoids it) — REJECTED empirically.** Fetch-only is immune at all rates; the write path degrades at inter-meet 0.2/1.0/2.0 s and inter-date 20 s alike (§2a, §2d). There is no pacing floor to set, and slowing the backlog walk would only throttle recovery for zero demonstrated benefit.

- **Branch 2 (persists regardless of pacing but retry-defeatable) — NOT SUPPORTED.** The literal precondition is split: the mode *does* persist regardless of pacing (✓), and isolated *fetch-only* re-fetch returns full data (✓). But **retry-defeatability inside the write path is unverified**: across every retry-capable run the mode did not fire (§2e), so **zero degraded meets were observed recovering via retry**. Three further concerns make an unvalidated retry the riskier action, not the safe one:
  1. The contention source is the **collector's** continuous writes, not ours; a retry's backoff pauses *our* writes but cannot quiet the collector, so recovery within a contended burst is not assured.
  2. On a fully-degraded date **every** meet returns empty, so a runners-empty retry would fire on all ~22 meets × up to 4 attempts (1-2-4 s backoff) — a retry-storm that could add minutes per date and still wall if contention persists.
  3. The retry would also fire on the confirmed **genuine runner-less meets** (~1–2 per date) every night, costing bounded backoff for no benefit.
  Adding control-flow to close a mode whose true cause is out-of-scope contention, on a trigger condition it was never confirmed to defeat, is exactly the "less-certain-semantics" restraint the throughput session itself exercised.

- **Branch 3 (change nothing; characterise; operator triage) — TAKEN.** The diagnosis **reframes** the problem. It is *not* a Racing-API rate-tier/provider issue (fetch-only immune above the ceiling), so the theracingapi.com add-on question is likely a red herring for this mode. It is a **`capture.db` write-contention interaction with the live collector**, and it is intermittent. The clean fixes are architectural/operational and **out of scope** per §9: e.g. decouple fetch from write so all of a date's meets are fetched (immune) before any `capture.db` write; run the backlog walk in a collector-idle window; or isolate the backlog write connection. None is a pacing constant or a `_fetch_meet_races` retry, so none is pre-authorised by the fork; all belong to operator/architect triage.

**§5.4 guard:** not implemented (retry branch not taken). The distinguishing signal it would have relied on is nonetheless **validated on the genuine side**: genuine runner-less meets stay empty across isolated re-fetch *and* all 4 retry attempts, whereas degraded meets recover on fetch-only. Observed distribution across the session: genuine runner-less meets **~1–2 per date** (stable, e.g. `met_aus_839431725665`, `met_aus_56116793303`); degraded-meet-recovered-via-retry **0 observed** (the mode did not fire during any retry-capable run).

---

## 4 — Verification burn results (§7)

**Baseline (`mode=ro`, before any work):** recoverable deficit (≥ 2026-03-15) = **40,987** (matches the throughput report's close); 101 backlog dates; burn window = 40 deficit-ordered dates (2026-04-04 … 2026-04-24); filled across window = 1,570; thoroughbred race rows across window = 3,212.

**Burn (chosen config = unchanged, `run_backlog_pass(delay=0.2, max_attempts=40)` — the exact production mechanism, writing placings via the normal path):**

| Metric | Value |
|---|---|
| Wall time | 53.0 s |
| Dates attempted | **7** (of 40 — walled early) |
| Dates that gained placings | 1 (2026-04-04) |
| Total placings gained (this burn) | **963** |
| Achieved req/sec | **3.12** (≤ 5/sec ✓) |
| Walled | 6 (hard_error = **0**, post_retry_truncated = **6**) |
| empty-runners occurrences (this burn) | 6 dates (dates 2–7, mode fired) |
| Still walls? | **Yes** — on 6 consecutive post-retry-truncated (the empty-runners mode), identical to the throughput session |

The production path reproduced the throughput session's wall precisely (date 1 clean, dates 2+ empty runners). **empty-runners occurrences before vs after remediation: unchanged** — branch 3 makes no behavioural change, so the count stands as observed. Because the mode is write-path/contention-driven, the same `run_backlog_pass` walls when the collector is busy and flows freely when it is quiet.

**Aggregate session recovery (intended, via the diagnostic write bursts, all normal-path upserts):** because the mode was absent for most of the session (§2e), the write-path bursts recovered a large slice of the window as a side effect:

| Metric | Before | After | Δ |
|---|---|---|---|
| Recoverable deficit (≥ 2026-03-15) | 40,987 | **36,650** | **−4,337** |
| Filled across burn window | 1,570 | **6,011** | **+4,441** |

This is reported as intended recovery, **not** as "the mode is defeated" — it flowed only because the intermittent mode happened to be quiescent. Per §8 this session issues **no** "recovery is solved" verdict; that is operator-Claude's triage call.

---

## 5 — Ghost-row tripwire result (fault-B guard, `mode=ro`)

Race-row counts (thoroughbred proxy: `race_class IS NOT NULL`, non-trial, non-jump-out) across the burn window, before vs after the full session's writes.

| Metric | Value |
|---|---|
| Race rows across burn window, before | 3,212 |
| Race rows across burn window, after | 3,212 |
| Net delta | **0** |
| Dates with **positive** (new-row / ghost) delta | **NONE** |

**The ghost tripwire did NOT fire.** Despite ~4,441 placings written across the window (many dates fully re-synced, ~150 race upserts each), zero new race rows were created — every upsert matched an existing row, confirming the subscription path's `race_date` alignment held for these dates. Measured only; **no remediation, no `race_date`/identity work** (§7/§9).

---

## 6 — Self-assessment

### Scope adherence & hard limits (§9)

- **Files edited:** exactly **one** — `subscription/racing_api.py` (§5.1 instrumentation, +46 lines, pure capture, no behaviour change). `scripts/backfill_race_metadata.py` was **byte-identical** to its session-start state at close (`diff` confirmed) — branch 3 required no pacing change. No file outside the two named anchors touched.
- **`race_date` / identity:** `race_date`, `upsert_race`'s conflict key, and all canonical race-identity logic — **untouched**. No schema change (no columns/tables/indexes).
- **Operational/betting:** timer, live-capture orchestrator/collector, Betfair path — **untouched** (the collector was read for the mechanism check only, never edited).
- **Full 41k:** not attempted; the §7 burn was capped at `max_attempts=40` and walled at 7 (bounded proof).
- **Ghost rows / `race_date`:** measured and reported only (§5); no remediation, no follow-up briefs written. No fault-B recommendation beyond the tripwire result.
- **Git:** no `add/commit/stash/restore/checkout/reset` — zero git write ops. Only the one named anchor's content changed.
- **Escalation:** none mid-session. The central surprise — the mode being write/contention-triggered rather than rate/volume-triggered, and intermittent — is captured here as a finding, per §1.
- **`capture.db`:** all *verification* queries opened `mode=ro` at the canonical `DB_PATH` via `start_process` Python; never copied. The diagnostic write bursts and the §7 burn wrote placings via the normal `init_db` upsert path — the intended recovery, per the brief.

### Dirty-set confirmation (§4)

Session-start and session-close `git status --short` are **identical in composition**: the same **16 modified** files (my `subscription/racing_api.py` and the already-dirty `scripts/backfill_race_metadata.py` among them) and the same **9 untracked** entries — **no new tracked files**. The dirty-file *set* changed only in the *content* of `subscription/racing_api.py` (the §5.1 instrumentation); `scripts/backfill_race_metadata.py` content is unchanged from session start. Off-repo harnesses, pre-session snapshots, and JSON result files live under `/root` (never in the repo). Both files `py_compile` clean under the venv.

### Confidence

- **empty-runners mode is real, reproduced, and transient:** HIGH (reproduced in 2 independent write bursts + the production `run_backlog_pass`; fetch-only recovery observed dozens of times).
- **Not triggered by rate / volume / time:** HIGH (fetch-only immune 1.0–9.8 req/sec, 8 dates, many repetitions; time-window explicitly refuted).
- **Triggered specifically by contended `capture.db` writes:** HIGH for the *correlation* (throwaway-DB clean vs real-DB degraded, position-independent across two experiments; timing-mimic clean); MEDIUM for the *precise HTTP mechanism* (provider-side black box).
- **Intermittent / collector-load-linked:** MEDIUM-HIGH (fired only in a ~5-min window; the collector-load link is the best-supported explanation but was not directly instrumented against collector write-rate).
- **No pacing config defeats it:** HIGH (write-path inter-meet ≤ 2.0 s and 20 s inter-date all still degrade).
- **Retry-defeatability under real degradation:** UNVERIFIED (the mode did not fire during any retry-capable run) — this uncertainty is itself the basis for not taking branch 2.

### Routing to operator triage (§10)

The mode is **not defeated**, but the finding reshapes the follow-up away from the brief's anticipated framing:
- It is **not** primarily a rate-tier / provider question — a fetch-only client is immune well above the 5/sec ceiling, so the pending theracingapi.com add-on reply is unlikely to move this mode.
- It **is** a `capture.db` write-contention interaction with the live collector, intermittent and collector-load-linked. The candidate fixes (fetch-then-write decoupling in `sync_day`; scheduling the backlog walk in a collector-idle window; isolating the backlog write connection) are architectural/operational and outside this bounded diagnosis's pre-authorised edits. Operator-Claude owns that decision; this session writes no follow-up brief.
