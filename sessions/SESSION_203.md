# Session 203 — Brief 1 (VPS date endpoint) drafted, verified, locked

**Opened:** 2026-06-29 23:04 ACST (headless runner) · active operator
session 2026-06-30 ~08:41 ACST
**Closed:** 2026-06-30 08:51 ACST
**Tool routing:** Chat only — plan explanation, brief drafting/lock,
read-only VPS source probe + read-only capture.db check. No Code
commissioned. No v3/v2 code touched.
**Governing DRs:** DR-033 (racing data = analytical/enrichment; this
endpoint lives there; bet-safety clean), DR-028 (single integration
boundary; API read by reference), DR-027 (two-DB), DR-021 (Adelaide
anchors).

## Anchor
- Open (runner): 2026-06-29 23:04:47 ACST. Active operator open:
  2026-06-30 08:41 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-30 08:51 ACST.
- New calendar day vs the runner open (overnight gap); re-anchored
  per DR-021.

## Pre-flight checks
- Runner fast-path: the S203 opening result (ran 2026-06-29 23:04:47
  ACST) was fresh (later than the S202 close 22:35) → presented
  straight, no re-verify, per the open skill Step 0.
- Tunnel healthy at runner open (`:8400` 200 OK,
  `collector_active:false`).
- Close directory listing: rebuild root clean; `vps_date_endpoint_
  brief.md` present; `.close_out_backups/` held S202 + S203 prompts
  (S204 written this close).

## Session shape
Single-deliverable session. Open (runner fast-path) → explain the
provisioning plan and defend the approach → read-only grounding →
draft + verify + lock Brief 1. The operator drove three checkpoints:
explain the plan / is it the best approach / would catching it earlier
have helped; then challenge whether Code needed to review before lock;
then "go". Analytical/governance throughout — no Code commissioned, no
code touched.

## What was delivered

1. **Plan explanation + approach defence.** Walked the operator
   through the locked provisioning path (Option B API-backed read + a
   date-aware endpoint), why it is right within DR-028 (read by
   reference; SSHFS/Option A fights the WAL-coherence the two-DB
   design protects), the one real cost (B is a data-access-layer
   re-map, not a config flip), and the "earlier-catch" question —
   framed as a requirements-timing gap (same solution built once vs
   retrofitted), not an architecture mistake, with the nuance that the
   API-backed path only became available once the `:8400` service
   existed.

2. **Read-only VPS source pre-flight** (Session 33 precedent). SSH
   probe of `/home/racing/racing-data-capture` grounded every Brief 1
   anchor: FastAPI app; `races` router already registered
   (`main.py:28`); `/today` handler (`races.py:66-71`) the mirror
   target; `get_db` (`api/db.py`) a clean read-only per-request
   dependency; uvicorn runs WITHOUT `--reload` (restart required);
   large pre-existing dirty tree (15 modified + the whole `api/`
   package untracked, incl. the edit target `races.py`; last commit
   `5f71488` 2026-03-04).

3. **Pre-lock data verification** (operator-challenged). A read-only
   `sqlite3 -readonly` check of capture.db retired the
   "correct-but-hollow" risk: `races` spans 2025-03-03 → 2026-06-29
   (90,306 races); sampled past dates carry Betfair selection-IDs
   (62-89%) and win/lose (`result_status`) at matching rates;
   `finish_position` sparse (expected — placings recovery's job,
   manual per DR-033).

4. **Brief 1 DRAFTED + LOCKED** — `vps_date_endpoint_brief.md`
   (rebuild root, 199 lines, 8,277 bytes, sha `4c291d52`). One
   additive read-only endpoint `GET /racing/races?date=YYYY-MM-DD` →
   `list[RaceSummary]`, mirroring `/today` with a bound date; reuses
   the existing helper + dependency; single permitted import
   (`from datetime import date`); no main.py/model/db.py/schema
   change. Two robustness notes folded in (empty-path→`/` fallback;
   finish_position-sparse-is-expected). Full dirty-tree git discipline
   (no git ops; races.py untracked → verify by file-read not
   `git diff`). Bet-safety CLEAN by construction. Scope held to the
   single endpoint (results-by-date excluded — reached via the
   existing `/racing/results/{race_id}`).

## Standing-instruction adherence
- Tool routing stated explicitly (Chat vs Code) at every handoff. OK
- DB reads read-only, never copied; VPS probes read-only. OK
- Brief-drafting: surfaced the numbered "calls I made", handled
  technical detail inside the artefact; the one operator decision
  (single-endpoint scope) surfaced. OK
- Fenced review content wrapped ~60-70 chars for the in-chat draft. OK
- DR-021 anchors at open + close. OK
- No standing-instruction edits → no sweep, no skill-review trigger.

## Open items
Pointer to `current_state.md`. New/changed in S203: Brief 1 locked +
verified; placings-recovery daily-check real window opens today
(30 Jun). Carried: Brief 2 (after Code runs Brief 1), cash-modal
blank, settlement-worker, promo-seed, W16 cutover, recovery
monitoring, parking-lot.

## Open items out
- Brief 1 drafting — DRAFTED + VERIFIED + LOCKED. DONE
- "Best approach / does Code need to review first" — RESOLVED
  (approach defended; pre-lock data check done in Chat, no Code review
  needed). DONE

## Session close state
- Rebuild root: `vps_date_endpoint_brief.md` added. `current_state.md`
  rotated; `v3_build_picture.md` Interface-refinement stream advanced.
  All other governance files unchanged.
- WIP: none in-flight.
- `.close_out_backups/`: `SESSION_204_opening_prompt.md` written; S202
  prompt stale (operator can clear; Claude doesn't hard-delete).
- Project KB: `vps_date_endpoint_brief.md` in the rebuild folder for
  Code (Code reads filesystem; KB upload optional).

## Forward routing — CONFIRMED WITH OPERATOR
S204 first action = **triage `vps_date_endpoint_report.md`** (the
Brief 1 Code report). **Operator-confirmed gate:** if Code has not
finished, the operator confirms when complete — so S204 HOLDS on
report absence and does not proceed until the operator confirms Code
is done. On a clean triage → draft Brief 2
(`vps_client_api_rewrite_brief.md`). Then: cash-modal blank fix →
settlement-worker → promo-seed → W16 cutover.
