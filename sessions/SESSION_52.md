# Session 52

**Title:** Saturday API observation probe — commission, monitor, report-handoff received.
**Opened:** 2026-05-02 09:48 ACST
**Closed:** 2026-05-02 22:13 ACST
**Wall-clock:** 12h 25min (probe was set-and-forget through ~12h of operator-AFK idle; active Claude work ~40min across open, two check-ins, handoff verification, and close)
**Tool routing:** Claude Chat (governance + monitoring) + Claude Code out-of-session (probe execution).
**Governing DRs invoked:** DR-029 (data layer fit-for-purpose review — probe is §2.1 unblock), DR-027 (two-database architecture — probe respects analytical-line isolation), DR-028 (cross-DB integration boundary — probe doesn't touch capture.db), DR-021 (timestamp anchoring).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-02 09:48 ACST`.
Close: same command → `2026-05-02 22:13 ACST`.

Same calendar day. Adelaide local Saturday.

## Pre-flight checks

Open ritual run cleanly:

- 12 `.md` files at rebuild root (expected).
- All directories present: `sessions/`, `dr029/`, `agent_review/`, `diagrams/`, `orchestration_pack/`, `skills/`, `.close_out_backups/`.
- `.close_out_backups/` contained `SESSION_52_opening_prompt.md` only (Session 51 close artefact, expected).
- Drift-check: `current_state.md` last-updated `2026-05-02 08:11 ACST` matched Session 51 close. `sessions/SESSION_51.md` present, 171 lines. `v3_build_picture.md` not updated last close (expected — Session 51 was probe-brief walk-through within §2.1, no stream movement).
- Probe report file (named in current_state.md as Session 52 Required Read) confirmed not yet present at open — matched operator's framing that the probe needed commissioning during this session.

## Session shape

Session 52 was **probe-commission-and-handoff-verification**, not substantive triage. The session opened ~12 minutes ahead of the brief's 10:00 ACST start window; operator confirmed go; locked Code prompt was pasted into a fresh Claude Code session at 10:05 ACST. The probe ran end-to-end on the VPS through to 20:17 ACST (10h12min capture + 1h44min idle between race windows); Code wrote `analyze.py` and `api_probe_report.md` post-capture; total session wall-clock 12h25min.

Active operator-Claude work was minimal by design — the brief was source-review-style with explicit "no mid-probe operator escalation" (§11). Three check-ins during the day: (1) early commissioning verification at 09:48 confirming probe was healthy; (2) mid-day status request from operator at probe ~12% complete confirming both streams writing as expected; (3) end-of-probe report-handoff verification.

The session structurally mirrors Session 30 (probe execution + read-and-report) but with the key difference that Session 30 deferred analysis to a fresh session whereas Session 52 had the analysis written by Code in the same out-of-session run. Session 53 reads the report fresh and triages Fix 4 / BSP-write-back-redo / cross-source identity.

## What was delivered

### 1. Probe commissioned, executed, and handed off

Code ran the probe end-to-end across 4 markets per brief §4.1 quota (2 thoroughbred + 1 harness + 1 greyhound, all metros):

| # | Code | Venue | Race | Sched UTC | Runners | BF snaps | RA snaps |
|---|---|---|---|---|---|---|---|
| 1 | thoroughbred | Hawkesbury | R1 | 01:20 | 8 | 5,535 | 185 |
| 2 | thoroughbred | Newcastle | R4 | 04:00 | 14 | 6,473 | 216 |
| 3 | harness | Albion Park | R1 | 07:04 | 10 | 6,514 | 0 |
| 4 | greyhound | Wentworth Park | R3 | 09:45 | 8 | 7,345 | 0 |

**Totals: 25,867 Betfair snapshots + 401 Racing API snapshots across ~443 MB of raw JSONL.**

Output landed at `dr029/2_1_race_data/api_probe_data/` (6 JSONL files + `manifest.json` with 22 events logged) plus `dr029/2_1_race_data/api_probe_report.md` (365 lines, in 250–450 target). Re-runnable scripts `probe.py` and `analyze.py` saved to `dr029/2_1_race_data/` for future probe passes (e.g. PLACE markets, repeat run with different app key entitlements).

### 2. Five-question answers received

Per operator's handoff message (full report at `dr029/2_1_race_data/api_probe_report.md`):

1. **`r.sp.actualSP` reachable on closed AU markets across all three codes when SP_AVAILABLE accompanies SP_TRADED.** 100% of active runners from SUSPENDED-onset, sustained through 45-min CLOSED tail. **Fix 3's "no sp field on closed runners" was a projection-set artefact, not a structural API limit.**

2. **Cross-code shape parity holds.** Greyhound POST_START is 0% actualSP (markets suspend faster) — only structural delta.

3. **8–9 API fields not captured by writer.** Highest-value gap is `sp.actualSP` (one-line fix).

4. **1s cadence justified for INTENSIVE/POST_START** (40–88% change rate). **Wasted on STANDARD (1–8%) and CLOSED (0%).** 45-min CLOSED tail captures zero new info.

5. **Thoroughbred BF↔RA join feasible today.** Harness/greyhound need a different RA endpoint or alternate source.

### 3. Major surprises (per report §4)

- **EX_LADDER structurally rejected on this app key** (`DSC-0018` every call across all 4 races). Depth-of-market data unavailable on free-tier entitlement. Genuine probe contribution.
- **`sp.actualSP` is NaN for REMOVED runners** — needs `isnan` guard wherever consumed.
- **`bspReconciled` is True throughout, not a useful gate.** Use `market_status == CLOSED` instead.

### 4. Probe behaviour during execution — adaptations Code made within §7.1 latitude

- **EX_LADDER fallback** triggered on every race within 1 second of capture start; combined-call dropped EX_LADDER per §4.4. Ladder-only retry attempts disabled after 5 consecutive failures per Code's extension to §4.4 step 3 (sensible — burning API calls on unrecoverable error).
- **Racing API harness/greyhound coverage absent** — Code's Racing API meet-discovery returned no match for Albion Park (harness) or Wentworth Park (greyhound) on free tier. Logged `racing_api_meet_missing` to manifest, continued Betfair stream uninterrupted per §7.1 failure-isolation rule. This is a real finding for question 5 — Racing API is thoroughbred-first, not all-codes.
- **One transient DNS failure at 06:29 UTC** during race 3 capture (`Temporary failure in name resolution` for `api.betfair.com`). Recovered on next call. Single-second gap. Worth a note in the report's §4.
- **Hourly Betfair keep-alives** firing as designed (00:35, 03:35, 06:35, 09:35 UTC). Session held across full 12-hour run.
- **Initial selection bug auto-corrected pre-launch** — Code's first race-selection pass picked greyhound twice and missed a thoroughbred; Code spotted the deviation from §4.1 quota, patched the priority logic, redeployed before launching. Caught and fixed before any capture started.
- **Race spacing widened from 110min to 160min** during dry-run validation — Code observed that 110min would cause capture-window overlap given the brief's T-60min through CLOSED+45min window (~105min per race + settlement variance). Bumped to 160min. Sequential, no overlap.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named in open ritual.
- **Cat 1 (V3 build picture conditional render)** — skip silent at open (no stream movement Session 51); skip silent at close (no stream movement this session — probe is unblocking Fix 4 design but Fix 4 brief drafting is Session 53+ work; §2.1 stream stays `in flight` with next-milestone shifting to "Fix 4 brief drafting + BSP write-back fix").
- **Cat 1 (open-items delta)** — skip silent at open; skip silent at close (no items closed/opened that aren't already in current_state.md routing forward).
- **Cat 2 (timestamp re-anchoring)** — open and close timestamps captured per DR-021.
- **Cat 2 (pre-flight directory listing)** — done at open, done before this close.
- **Cat 2 (Desktop Commander default)** — held throughout. All filesystem ops via Desktop Commander.
- **Cat 2 (operator-facing brevity)** — held. Active responses ranged from 1-line confirmations (Wi-Fi switch) to medium-length governance summaries (probe status, MVP estimate). No essay-length responses produced.
- **Cat 2 (operational/analytical line discipline)** — held. Probe was framed as analytical-line work throughout (capture for downstream Session 53 triage, no operational impact).
- **Cat 2 (no mid-probe escalation)** — brief §11 honoured; Code ran end-to-end without checking in.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — omitted per skill default; one-paragraph plain-language probe summary provided per operator request.

No new standing instructions surfaced this session.

## Open items in (carried forward)

All items from Session 51 carry forward to Session 53. Routing changes to existing items based on probe outcomes:

- **§2.1 surgical-fix arc** — probe answers reframe the scope. Fix 4 brief drafting now unblocked (cadence empirically grounded). **New item: BSP write-back fix** (small additive — add `SP_AVAILABLE` to projection set, add `sp.actualSP` to writer, add `isnan` guard for REMOVED runners, use `market_status==CLOSED` as gate). Fix 5 venue harmonisation already done Session 47. §2.1 close now visible after Fix 4 + BSP-write-back-fix lands.
- **§2.4 Betfair Streaming spec + cadence** — was `blocked-on-probe`, now unblocked. Fix 4 brief drafting is the active deliverable.
- **§2.10 external analytics scan** — was `blocked-on-probe`, now substantially fed. 8–9 fields named as gaps.
- **§2.5 soft-book interface contract** — gets a partial input via Q5: Racing API thoroughbred-only finding affects how source-flexible filling for harness/greyhound gets specified.

## Open items out

- **Probe execution** — closed cleanly. Re-runnable scripts saved for future passes (e.g. PLACE markets, post-app-key-upgrade ladder retest).
- **Question 1 (BSP reachability)** — answered yes with one-line fix path identified.
- **Question 2 (cross-code parity)** — answered yes with greyhound-suspends-faster nuance noted.
- **Question 4 (cadence)** — answered with empirical phase-by-phase data; Fix 4 design grounded.
- **EX_LADDER question** — answered as structural app-key entitlement issue, not request-shape issue.

## Session close state

- **Rebuild folder root:** 12 `.md` files unchanged from open. No phantom files.
- **`current_state.md`:** updated by close ritual.
- **`v3_build_picture.md`:** updated by close ritual (§2.1 next-milestone shifts; §2.4 status changes from `blocked-on-probe` to `in flight`; §2.10 status changes from `blocked-on-probe` to `unfinished`).
- **`standing_instructions.md`:** untouched (no new instructions, no edits).
- **`sessions/`:** Session 52 record written.
- **`.close_out_backups/`:** Session 53 opening prompt to be written by close ritual; Session 52 prompt to be removed.
- **`dr029/2_1_race_data/`:** gained `api_probe_report.md` (365 lines), `analyze.py`, `analyze_output.txt`, `probe.py`, and `api_probe_data/` directory containing 6 JSONL files + manifest.json.
- **Project knowledge base:** no canonical-doc changes need re-uploading.

## Forward routing

**Confirmed with operator at close: Session 53 triages the probe report.**

Session 53 primary deliverables (in order):
1. Read `api_probe_report.md` in full (365 lines).
2. Triage findings against §2.1 surgical-fix arc remaining scope.
3. Decide whether BSP write-back fix is its own brief (Fix 9-equivalent) or folds into Fix 4.
4. Draft Fix 4 cadence brief if scope is clear from probe data; otherwise scope further.
5. Apply §3.5's harness/greyhound Racing API gap to §2.5 soft-book interface contract framing.
6. Update `dr029/dr029_scope.md` with probe outcomes affecting §2.1, §2.4, §2.5, §2.10.

**Out of scope for Session 53:** v3 build proper (still gated on DR-029 close); Fix 4 Code execution (post-brief-lock); §2.6/§2.7/§2.8/§2.9 reframing (sequenced after §2.1/§2.4 close).
