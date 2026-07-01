**Last updated:** 2026-07-01 12:22 ACST (Session 211 close)

**Timezone:** DR-021 standard applies — Adelaide anchors, no
overrides active.

---

## Where we are

**S211 root-caused the placings-recovery stall and locked the fix
brief.** The diarised 1-Jul daily check (the S211 runner first-action)
found ZERO burndown — deficit crept 41,340 → 41,633, stall alarm fired.
That triggered a full root-cause diagnosis, and the standing "quota"
model turned out to be FALSE.

Two faults, both evidenced:

- **Fault A — throughput / false quota (the gate).** A live read-only
  probe proved the Racing API returns NO quota/rate-limit headers, and a
  full resulted date (2026-06-06: 24 meets / 153 races / 1,944 runners /
  1,855 placings) fetched clean in **7.8s at ≤5/sec, zero empties.**
  There is no daily budget to exhaust. What actually walls the job:
  exceeding the per-second ceiling returns HTTP 200 with an EMPTY body
  (not a 429) → `_api_get`'s `raise_for_status()` passes → logged
  "truncated" → `run_backlog_pass` walls after 3
  (`BACKLOG_WALL_THRESHOLD = 3`). Pacing is `BACKLOG_MIN_DELAY = 1.5`s
  (~0.67/sec) — ~7× too slow vs the confirmed 5/sec. The nightly timer
  fires 14:00 UTC / 23:30 ACST — peak contention with the live
  collector (the plausible degradation trigger). And the nightly only
  sweeps a 14-day recent window — it never touches the 41k historical
  backlog (that needs a manual `--days`/`--date` run).
- **Fault B — matching key / ghosts (deferred).** `upsert_race` keys on
  `(race_date, venue_normalised, race_number)`, and `race_date` is the
  two-path-skewed value (`race_date_semantics_report.md`), so backfilled
  placings for ±1-day-skewed live rows can land on a duplicate GHOST row
  instead of the real race. DR-032/034 territory → its own
  governance-aware brief, NOT folded into the surgical fix.

**Racing-API rate tier CONFIRMED: 5 req/sec** (support reply relayed
this session; resolves the S205 open question). Support addressed the
rate, not a daily cap — consistent with the no-quota probe finding.

**Throughput-fix brief LOCKED + commissioned to Code.**
`placings_throughput_fix_brief.md` (rebuild root, 124 lines, sha
`8880f78c`). Surgical, two VPS files + one timer: §5.1 retry degraded
`/races` fetches (+ log headers on first degraded response); §5.2 pace
≤5/sec (set empirically); §5.3 de-fang the false wall (split hard-error
vs post-retry-truncated, second threshold ~6 for the latter); §5.4 move
the timer off the 14:00-UTC contention slot. §7 = a real bounded
~40-date backlog burn measuring placings gained / req·sec / empty-200s
before-vs-after retry / a GHOST-ROW tripwire (fault-B signal). Code's
read-back FAITHFUL + two design calls approved (burn via
`run_backlog_pass` capped ~40 not `main --days`; second wall threshold
~6). Accepted: the burn WRITES real placings (intended recovery);
`mode=ro` is verification queries only.

**Prior anchor (S210):** cash-modal back-stake blank fix SHIPPED,
committed `e2638fa`. Full detail in `sessions/SESSION_210.md`.

## What's next

**S212 first action (CONFIRMED with operator — AUTO, GATED) — triage
Code's `placings_throughput_fix_report.md`.** If present on open →
auto-triage: rows flowed at scale? req/sec ≤5? post-retry empties ~0?
no unexpected wall? — and READ THE GHOST TRIPWIRE. Route: clean + no
ghosts → commission the full-backlog burn brief; ghost tripwire fired →
the `race_date` identity fix (fault B) becomes the priority brief with
its DR-032/034 governance check. If the report is absent (Code hasn't
run) → HOLD and notify.

**Then, in order:**
1. **Settlement-worker brief** (IOU + manual-match-to-lay) — the next
   build item; a money-path piece, diligence-first before Code.
2. **Promo-seed** → **W16 cutover.**

**Parallel / not gating:** the Data Foundation harvest
(§A.4 → §C/§D/§E → roadmap → supersede).

**Parked (revisit-triggered):** DR-034 stance-4 fragment-collapse
remediation — now effectively subsumed by fault B (the ghost/race_date
identity fix); revisit when the S212 ghost tripwire reports.

## Required reads for Session 212

In order:
1. `current_state.md` (this file).
2. `standing_instructions.md` — in full per Cat 2.
3. `project_context.md` — orientation primer.
4. `sessions/SESSION_211.md` — the S211 record (recovery root-cause + throughput-fix brief).

Reference-only — read on demand:
- `placings_throughput_fix_brief.md` — the locked contract Code executed; the triage reads its report against this.
- `race_date_semantics_report.md` — fault-B mechanism (what the ghost tripwire is watching).
- `placings_trickle_report.md` — prior recovery design/context.

## Pending operator-side actions

**Between S211 → S212:**
- **RUN THE CODE SESSION** against the locked throughput brief
  (`placings_throughput_fix_brief.md`) — the load-bearing action; S212's
  first action triages its report.
- **Racing API rate tier** — REPLY RECEIVED (5 req/sec). Fold into
  `BETHUB_DATA_REFERENCE.md` §G when docs are next touched; note there is
  no daily quota (probe-confirmed).
- **Delete the `SESSION_9001` watcher-test artefact** in
  `/Users/tim/.bethub-cycle/results/` (Claude doesn't hard-delete).
- **Delete consumed opening prompts** in `.close_out_backups/` — the
  S212 prompt is the only one that should remain (Claude doesn't
  hard-delete).
- **GitHub off-machine backup of bethub-v3** — pending operator login
  (the `e2638fa` checkpoint is local-only until this runs).
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** running; jump-start-only to retirement.

**Carried (parking-lot):** the `by-market` results route follow-up; the
settled-vs-pending-both-populated ordering edge; VPS git-hygiene debt
(`racing-data-capture` broadly dirty); the stray `['DB_PATH` file on the
VPS (inert); the 34.8% start-less discovery-shell rows; `venue_normalised`
drift; the other four `vps_client` surfaces; DST near-midnight caveat;
persisting the Racing-API race id (DR-034 stance-5); terminal-migration
(W16); deploy-before-settle / IOU free-bet credit (settlement-worker);
hedge-link on manual entry; bet-mutation-log viewer; BetLog promo-events
delete-check; streaming hardening (F1/F3/F4/F5); 200-market
over-subscription; audit-sink durability (F8) + place-then-commit (F11);
partial free-bet draw-down; in-app catalogue-management UI; shared
canonical account-ref type (post-cutover, DR-030); tunnel
auto-start/health-check; the Racing.tsx cash-branch lint debt (~117–118);
the blank cash-box inline-prompt parity.

## Open items

Pointer-only — full detail in `sessions/SESSION_211.md`.

**New / changed in S211:**
- **Throughput-fix Code commission** — brief locked; run Code; S212
  auto-triages (gated).
- **Fault B — `race_date` identity-key / ghosts** — named next brief +
  governance question (drop `race_date` from the canonical key?
  DR-032/034); priority contingent on the S212 ghost tripwire.
- **"Quota" model FALSE** — no daily API quota; correct doc/comment
  framing when next touched.

**Closed in S211:**
- Racing-API rate-tier open question — 5/sec confirmed. ✅
- "20-attempts/night cap is the choke" — DISPROVEN. ✅
- "Move timer for fresh budget" — superseded (no budget; contention
  move folded into brief §5.4). ✅

**Carried to S212:**
- Settlement-worker brief (next build item).
- Promo-seed; W16 cutover scoping.
- Data Foundation arc (parallel, not gating).
- Recovery: throughput fix in Code's hands; full-backlog burn + fault-B
  ghost fix gated on the S212 triage.

**Carry-forward sensitivity flags:**
- **The burn WRITES to live capture.db** — intended recovery; idempotent
  upserts, analytical DB not bet-facing, nightly capture.db backup
  (19:30 UTC) exists; the ghost tripwire halts before any wider burn.
- **Ghost floor is a floor-at-this-moment, not a ceiling** — genuine→ghost
  as burn lands; don't over-read the raw deficit.
- **Bet-safety — CLEAN** (read-only racing/analytical; no v3 / settlement
  / money path).
- **capture.db reads read-only** (`mode=ro`, never copy); **v2 never
  modified**; **VPS repo dirty** — surgical no-git discipline on VPS Code
  work.

## Active governing decision records

- **DR-021** (timestamp anchoring, Adelaide local) — every open + close.
- **DR-019** (derived state on read).
- **DR-022** (book / account / account-at-book vocab).
- **DR-025** (hedge-state classification / ops-log audit trail).
- **DR-026** (at-log market snapshot — narrow cross-DB durability exception).
- **DR-027 / DR-028** (two-database architecture + single integration boundary).
- **DR-029** (data-layer fit-for-purpose) — closed (S78); amended S191.
- **DR-030** (v3 repo layout / module boundaries).
- **DR-031** (v3 tech stack; SQLite WAL; uv/httpx).
- **DR-032** (Betfair canonical reference layer) — amended S180; a
  Betfair market is required at logging time.
- **DR-033** (data-source roles) — placings analytical, settlement
  Betfair-only. **This session's work is analytical side.**
- **DR-034** (canonical race-identity model) — LOCKED S206; live-proven
  S209. Betfair WIN market = the spine. **The fault-B / ghost territory
  (excluded from the throughput fix).**
- **DB read discipline** (`mode=ro`, never copy, `start_process` Python).

Full DR list in `decisions.md`.
