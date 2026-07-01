**Last updated:** 2026-07-01 14:44 ACST (Session 212 close)

**Timezone:** DR-021 standard applies — Adelaide anchors, no
overrides active.

---

## Where we are

**S212 closed the git-drift gap, triaged the throughput fix, and
locked + (via Code) executed the empty-runners diagnosis — which
reframes the placings gate from pacing to DB contention.**

- **Git baseline restored.** `c7f71ab` put Sessions 198–211 (46 files —
  governance docs, briefs, reports, session records) under version
  control after ~13 sessions of untracked drift; `.close_out_backups/`
  + `skills/*.zip` gitignored. The runner's "brief hash mismatch"
  open-flag was a FALSE alarm (git-blob SHA-1 `3f34…` vs the recorded
  sha256 `8880f78c…` — identical content, verified twice). Stale
  `.close_out_backups/` prompts + the `SESSION_9001` test fixtures were
  operator-deleted.
- **Throughput fix triaged — PARTIAL success.** Pacing corrected
  (~3.15 req/sec clean, zero empty-200s); **ghost-row tripwire CLEAN
  (fault B not biting)**; ~892 placings recovered (deficit 41,879 →
  40,987); nightly timer moved to **05:30 ACST** (answers the dated
  1-Jul timer-shift check). Surfaced the **empty-runners degradation
  mode** as the real remaining gate.
- **Empty-runners diagnosed — NOT pacing; it's DB write-contention.**
  The diagnosis brief (`placings_empty_runners_diagnosis_brief.md`,
  99 lines, sha `6bae8914`) was locked and Code executed it
  out-of-session (~13:10–13:55). FINDING: a fetch-only client is immune
  at ~9.8 req/sec (≈2× the 5/sec ceiling); the mode is triggered by the
  `sync_day` **WRITE path contending with the live collector on the
  shared `capture.db`** (throwaway-DB write immune; artificial latency
  immune) — intermittent, resets ~2s of write-idle. No pacing config
  defeats it; retry-defeatability unverifiable. Resolved to §5.3
  **branch 3 (no behavioural change, instrumentation only).** The
  follow-up is now an **architecture / operational-contention
  question**, not a rate-tier / provider one. **Report present,
  un-triaged — S213's first action.**

**Prior anchor (S210):** cash-modal back-stake blank fix SHIPPED,
committed `e2638fa`. Detail in `sessions/SESSION_210.md`.

## What's next

**S213 first action (CONFIRMED with operator — AUTO, no gate) — triage
`placings_empty_runners_diagnosis_report.md`.** Read against the locked
brief's §7/§8/§9; digest the DB-write-contention headline; confirm the
instrumentation-only edit stayed in scope + the ghost tripwire; then
route the contention question and **take stock with the operator on
whether placings recovery stays worth chasing** — the pacing/provider
rabbit hole is closed by the finding. Report is present, so no hold
expected.

**Contention routing to weigh at triage:** accept intermittent
write-degradation as a fact of the shared DB (trickle regardless);
serialise the backfill burn against the live collector's write windows;
or a larger change to the capture.db write path. All operator-triage
territory — none a pacing brief.

**Then, in order:**
1. **Settlement-worker brief** (IOU + manual-match-to-lay) — next build
   item; money-path, diligence-first before Code.
2. **Promo-seed** → **W16 cutover.**

**Parallel / not gating:** Data Foundation harvest (§A.4 → §C/§D/§E).

**Parked (revisit-triggered):** full-backlog burn (downstream of the
contention resolution); fault-B / `race_date` identity (tripwire clean,
no forcing event); DR-034 stance-4 fragment-collapse; Cowork sub-agent
review → pre-W16 go/no-go.

## Required reads for Session 213

In order:
1. `current_state.md` (this file).
2. `standing_instructions.md` — in full per Cat 2.
3. `project_context.md` — orientation primer.
4. `sessions/SESSION_212.md` — the S212 record.

Reference-only — read on demand:
- `placings_empty_runners_diagnosis_report.md` — the report S213 triages.
- `placings_empty_runners_diagnosis_brief.md` — the locked contract it's triaged against.
- `placings_throughput_fix_report.md` — the burn that surfaced the mode (ghost-tripwire baseline).

## Pending operator-side actions

**Between S212 → S213:**
- **GitHub off-machine backup of bethub-rebuild + bethub-v3** — `c7f71ab`
  (governance repo) and `e2638fa` (app repo) are LOCAL-only until an
  off-machine push runs; pending operator login.
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** running; jump-start-only to retirement.

**Done this session (fold when docs next touched):** stale
`.close_out_backups/` prompts + `SESSION_9001` fixtures deleted;
Racing-API rate tier (5 req/sec, no daily quota) confirmed — fold into
`BETHUB_DATA_REFERENCE.md` §G.

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

Pointer-only — full detail in `sessions/SESSION_212.md`.

**New / changed in S212:**
- **Empty-runners = DB write-contention** — S213 triages the report →
  routes the architecture/contention question. Pacing/provider framing
  retired.
- **sha256-not-git-blob** — the open-ritual drift-check should compute
  `shasum -a 256`, not `git hash-object` (the false-alarm source).
  Advice recorded; future standing-instruction candidate.

**Closed in S212:**
- Git 13-session uncommitted drift — `c7f71ab`. ✅
- Stale `.close_out_backups/` prompts + `SESSION_9001` fixtures —
  operator-deleted. ✅
- Brief "hash mismatch" — diagnosed benign (git-blob vs sha256). ✅
- Dated 1-Jul timer-shift check — timer at 05:30 ACST. ✅
- Throughput-fix triage — partial success (pacing fixed, tripwire clean,
  empty-runners surfaced). ✅

**Carried to S213:**
- Settlement-worker brief (next build item).
- Promo-seed; W16 cutover scoping.
- Data Foundation arc (parallel, not gating).
- Full-backlog burn + fault-B ghost fix — gated on the empty-runners
  contention resolution.
- Cowork sub-agent review → pre-W16 go/no-go.

**Carry-forward sensitivity flags:**
- **Bet-safety — CLEAN** (read-only racing/analytical; no v3 / settlement
  / money path).
- **capture.db reads read-only** (`mode=ro`, never copy); **v2 never
  modified**; **VPS repo dirty** — surgical no-git discipline on VPS
  Code work.
- **The write-path contention finding** means burns intermittently
  degrade — don't mistake a contention wall for a data or code fault.

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
  S209. Betfair WIN market = the spine. **Fault-B / ghost territory.**
- **DB read discipline** (`mode=ro`, never copy, `start_process` Python).

Full DR list in `decisions.md`.
