# SESSION 211 — placings-recovery root-caused (no quota); throughput-fix brief locked & commissioned

**Opened:** 2026-07-01 10:12 ACST (headless runner) — operator engaged ~10:22
**Closed:** 2026-07-01 12:22 ACST
**Tool routing:** Chat (diagnosis, live probe, brief-drafting, Code-gate triage). Read-only VPS probes via Desktop Commander/SSH. Throughput brief hands to Code out-of-session.
**Governing DRs:** DR-021 (timestamps); DR-033 (Betfair operational / Racing API analytical — this work is analytical side); DR-032 / DR-034 (canonical race identity — the *excluded* fault-B territory).
**Bet-safety:** CLEAN — read-only analytical/capture side throughout; no operational/betting DB, no Betfair operational path, no money path touched.

## Anchor
- Open: runner ran `SESSION_211_opening_prompt` at 2026-07-01 10:12 ACST; operator opened chat ~10:22.
- Close: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → **2026-07-01 12:22 ACST**.

## Pre-flight checks
- Runner fast-path: fresh result present (ran 10:12, after S210 close 09:55) → presented straight, no re-verify.
- Drift-check clean: `current_state.md` last-updated (09:55) matched S210 close.
- Root dir listing clean; no phantom governance files (`.DS_Store` only, inert).

## Session shape
Opened as the diarised 1-Jul placings-recovery daily check (the S211 auto first-action), which the runner ran read-only against the VPS: burndown ZERO, deficit crept to 41,633, stall alarm fired. It then pivoted hard — on operator frustration that weeks of effort have recovered nothing — into a full root-cause diagnosis, grounded in the real VPS code plus a live API probe, ending in a decisive finding that overturns the standing "quota" model and a locked surgical-fix brief commissioned to Code. A meaty diagnostic + brief-drafting session, off the formal W-streams (placings-recovery is off-stream).

## What was delivered

1. **Daily check (runner).** Zero burndown; deficit 41,340 → 41,633 (new dates rolled in); stall alarm fired. Established "recovery recovers nothing" as a genuine stall, not a ghost-count artefact.

2. **Root-cause diagnosis — TWO faults, both evidenced.**

   **Fault A — throughput / false quota (the gate).** There is NO API quota. A live read-only probe showed the Racing API returns *no* rate-limit/quota headers of any kind, and a full resulted date (2026-06-06: 24 meets / 153 races / 1,944 runners / 1,855 placings) fetched clean in **7.8s at ≤5/sec, zero empties**. The "daily cap / budget" model is false — and it's baked into the code's own comments (`get_unsynced_dates` docstring: "hit the API's daily cap after ~13 dates"; `run_backlog_pass` "leftover quota" constants) and prior session summaries. The real mechanism: exceeding the per-second ceiling returns **HTTP 200 with an empty body** (not a 429); `_api_get`'s `raise_for_status()` passes; the empty result is logged "truncated"; `run_backlog_pass` walls after 3 (`BACKLOG_WALL_THRESHOLD = 3`). Pacing is throttled to **1.5s/req** (`BACKLOG_MIN_DELAY = 1.5`, ~0.67/sec) — ~7× too slow vs the real 5/sec. The nightly timer (`racing-metadata-backfill.timer`) fires **14:00 UTC / 23:30 ACST** — peak contention with the live collector, the plausible trigger. Also surfaced: the nightly job only sweeps a **14-day recent window** (`get_unsynced_dates`), so it never attacks the 41k historical backlog — that only moves on a manual `--days`/`--date` run.

   **Fault B — matching key / ghosts (deferred).** `upsert_race` keys the write-side identity on `(race_date, venue_normalised, race_number)`, and `race_date` is the two-path-skewed value (per `race_date_semantics_report.md`). So backfilled placings for ±1-day-skewed live-captured races can land on a duplicate **ghost row** rather than the real race. DR-032/034 canonical-identity territory → its own governance-aware brief, NOT folded into the surgical fix.

3. **Racing-API rate tier CONFIRMED.** Operator relayed support's reply: **5 req/sec** (not the assumed 1). Resolves the S205 open question. Support addressed the *rate*, not a daily cap — consistent with the probe's no-quota finding.

4. **Throughput-fix brief LOCKED + commissioned.** `placings_throughput_fix_brief.md` (rebuild root, **124 lines, 11,593 bytes, sha `8880f78c`**). Surgical, two files + one timer: §5.1 retry degraded `/races` fetches (+ log headers on first degraded response — instruments the ground truth); §5.2 pace ≤5/sec (set empirically from the burn); §5.3 de-fang the false wall (split hard-error vs post-retry-truncated streaks; second higher threshold ~6 for the latter); §5.4 move the timer off the 14:00-UTC contention slot (proposed ~20:00 UTC / 05:30 ACST). §7 verification = a real bounded **~40-date backlog burn** measuring placings gained, achieved req/sec, empty-200s before/after retry, AND a **ghost-row tripwire** (fault-B signal). §9 hard limits exclude the `race_date`/identity key, schema, and everything off the two files + timer. Code prompt issued; Code's read-back confirmed **FAITHFUL** + two design calls approved: (1) burn via `run_backlog_pass` capped ~40 (the real walling path), scratch harness off-repo, not `main --days`; (2) second higher wall threshold (~6) for post-retry-truncated, hard errors stay at 3. Accepted consciously: **the burn writes real placings** (intended recovery); `mode=ro` governs verification queries only.

## Standing-instruction adherence check
- DR-021 timestamps — open + close anchored ACST. ✓
- Cat 1 calendar-calibrated open — same-workday; runner fast-path presented straight. ✓
- Diligence-first before Code — full grounding (live probe + real code reads) before drafting; Code read-and-confirm gate honoured before build. ✓
- brief-drafting skill — universal spine, hard limits, single bounded session, output spec, what-happens-after, calls surfaced at hand-off. ✓
- No standing instructions authored/edited this session (Step 7 sweep: none).

## Open items

Pointer to `current_state.md`. New/changed this session:

**New:**
- **Throughput-fix Code commission** — brief locked; the between-session operator action is to run Code against it. S212 auto-triages the report (gated).
- **Fault B (`race_date` identity-key / ghosts)** — now a named next brief + governance question (does the canonical race-identity key drop `race_date`? DR-032/034). Priority contingent on the ghost tripwire in Code's burn.
- **The "quota" model is FALSE** — correct lingering quota framing when docs are next touched (`BETHUB_DATA_REFERENCE.md` §G; the code comments are corrected by the fix itself).

**Closed / resolved:**
- Racing-API rate-tier open question (S205) — **5/sec confirmed.** ✅
- "The 20-attempts/night cap is the choke" hypothesis — **DISPROVEN** (recovery mode already lifts it to 120; the real choke is the per-second-degradation misread). ✅
- The 1-Jul runner's "move the timer to catch fresh budget" recommendation — **superseded**: no budget exists; the timer move is justified as contention-avoidance, folded into the brief §5.4. ✅

## Forward routing

**S212 first action (CONFIRMED with operator — AUTO, GATED):** triage Code's `placings_throughput_fix_report.md`.
- **If present** when S212 opens → auto-triage: confirm rows flowed at scale, req/sec ≤5, post-retry empties ~0, no unexpected wall, AND read the **ghost-row tripwire**. Route: clean + no ghosts → commission the full-backlog burn brief; ghost tripwire fired → the `race_date` identity fix (fault B) becomes the priority brief with its DR-032/034 governance check.
- **If absent** (Code hasn't run) → HOLD and notify.

Then, in order: settlement-worker brief (IOU + manual-match-to-lay) → promo-seed → W16 cutover. Data Foundation harvest parallel, not gating.

## Session close state
- Root: `placings_throughput_fix_brief.md` added (124 lines, sha `8880f78c`). No phantom files.
- `v3_build_picture.md`: **NOT updated** — no formal W-stream moved (placings-recovery off-stream); timestamp left at S210 close.
- `standing_instructions.md`: unchanged.
- `.close_out_backups/`: `SESSION_212_opening_prompt.md` written; any stale prompts flagged for operator delete (Claude doesn't hard-delete).
- Pending operator-side (between S211 → S212): **run the Code session against the locked throughput brief** (the load-bearing action); GitHub off-machine backup still pending; stale-artefact deletes (`SESSION_9001`, consumed opening prompts).
