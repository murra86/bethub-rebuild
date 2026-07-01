# Session 204

**Title:** Brief 1 re-locked v2 + executed (date endpoint LIVE) +
race_date-semantics diagnostic run & triaged → client query contract
settled (Candidate B); Brief 2 drafting set as S205 auto-action.
**Opened:** 2026-06-30 09:01 ACST (headless runner) — manual
continuation from the `s204` prompt.
**Closed:** 2026-06-30 09:49 ACST.
**Tool routing:** Chat = brief re-lock, diagnostic brief drafting,
report triage, governance/close. Code (out-of-session) = Brief 1
execution + the race_date diagnostic run.
**Governing DRs:** DR-021 (Adelaide anchors), DR-033 (data-source
roles — racing data analytical), DR-028 (single integration boundary),
DR-027 (two-DB).
**Bet-safety:** CLEAN throughout — read-only racing/analytical layer
only (DR-033). No Betfair / settlement / money-movement / lay /
live-betting path touched. `capture.db` read-only.

---

## Anchor

- Open (runner): `2026-06-30 09:01 ACST` (from
  `SESSION_204_opening_prompt_result.md`, run 09:01:20).
- Close: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` →
  `2026-06-30 09:49 ACST`.
- Re-lock anchors during session: Brief 1 v2 09:11; diagnostic brief
  09:35.

## Pre-flight checks

Opened via the runner fast-path (fresh result, run 09:01 > S203 close
08:51) — presented straight per the session-open Step 0. Runner had
HELD at the gate (`vps_date_endpoint_report.md` absent → Brief 1 Code
not finished). Drift-check + pre-flight were clean in the runner
result; Brief 1 intact at the time (199 lines, sha `4c291d52`).

## Session shape

A HOLD-clearing execution session that turned into more than the
predicted triage. It opened held (Brief 1 Code not yet run). The
operator then surfaced a pre-execution *review* of the locked Brief 1
(written against the brief's internal logic, no VPS access). Because
Code had not yet built, this landed in the ideal window — re-lock
before commissioning. Brief 1 was re-locked as v2 folding in the
actionable findings, then executed out-of-session (endpoint live), and
its timezone probe surfaced a real semantics problem in `race_date`
that warranted a dedicated read-only diagnostic before Brief 2 could
be safely scoped. The diagnostic ran and triaged clean, settling the
client query contract Brief 2 builds on. The session closed with Brief
2 drafting staged as the S205 auto-action.

## What was delivered

1. **Brief 1 RE-LOCKED as v2** (`vps_date_endpoint_brief.md`, 289
   lines, sha `55395a7d`, supersedes v1 `4c291d52`). Folded in 7 of 8
   review findings: #1 prefix-contingency hard gate (`@router.get("")`
   correct only if router prefix == `/racing/races`; else stop-and-
   report, no silent path adaptation); #2 copy `/today`'s full
   predicate verbatim (shown SELECT illustrative); #3 bare-root
   404→422 smoke check + self-assessment note; #4 timezone-basis probe
   + Brief-2 carry; #5 corrected ordering rationale (empty-path can't
   collide with `/{race_id}`, so belt-and-suspenders not correctness);
   #7 untracked-file marker comment + permitted `/tmp` pre-edit copy;
   #8 quiet-window restart. Dropped #6 (report path bethub-rebuild vs
   bethub-v2) as a false positive — `bethub-rebuild/` is the live
   project root.

2. **Brief 1 EXECUTED by Code** (`vps_date_endpoint_report.md`).
   Endpoint `GET /racing/races?date=YYYY-MM-DD` LIVE + verified. The
   prefix hard gate PASSED (`router = APIRouter(prefix="/racing/races")`),
   so `""` resolves correctly — confirmed by a 200 on a populated past
   date. `/today` confirmed a plain single-predicate query (no JOIN /
   filter), so the mirror was a clean `date('now')`→bound-param swap.
   Empty dates → `[]`+200; malformed → 422; bare-root → 422 (404→422
   shift recorded); regressions (`/today`, `/{id}`, `/upcoming`) all
   200. Dirty tree byte-identical before/after (15 M / 8 ??, `races.py`
   still untracked), no git ops, marker present, `/tmp` rollback copy
   taken, restart in a confirmed quiet window. Bet-safe.

3. **RACE_DATE SEMANTICS DIAGNOSTIC drafted + locked + run +
   triaged.** Brief `race_date_semantics_brief.md` (163 lines, sha
   `c1f53f68`) → report `race_date_semantics_report.md`. Read-only
   (no edits, no writes, no restart, no git ops). Findings:
   - **Population rule pinned at source (both writers quoted).**
     `race_date` is never derived from the race instant; it is owned by
     the *first* inserter (`upsert_race` never updates it on conflict).
     Path A (subscription) = the upstream Racing API `/meets?date=`
     grouping copied verbatim → skews 0/−1 (late meetings filed next
     day). Path B (live orchestrator, since 2026-03) = UTC clock date
     at *discovery*, up to 12h ahead of the race → skews 0/+1.
   - **Offset characterised:** of 58,858 rows with a start, ~72.6%
     align with the Adelaide date, ~13.1% −1, ~14.2% +1. Path-segmented:
     subscription = 0/−1 only; live = 0/+1 only. State-dependent — VIC
     ~50/50 (night meetings); WA/NSW/QLD/NZ/SA/TAS ~95–100%. 34.8% of
     all rows (31,472) are start-less discovery shells (only from
     2026-03; the same rows that show 0 runners).
   - **`scheduled_start` encodings:** 3 distinct, all explicit-UTC —
     `Z`+3-digit millis, `Z`+7-digit fraction (breaks Python
     `fromisoformat`, must truncate to ≤6), `+00:00` no fraction (from
     2026-03). Brief 2's parser must accept all three.
   - **CLIENT QUERY CONTRACT settled = Candidate B:** to fetch races
     run on Adelaide-local day D, query D−1, D, D+1, union, then keep a
     row when its `scheduled_start` (UTC→Adelaide) lands on D; for
     start-less rows fall back to keeping `race_date == D`. Candidate A
     (naive single `?date=D`) rejected — misses ~¼ overall, ~½ of VIC.

4. **Triage verdict + routing decision.** Both Code runs clean, scope
   held, bet-safe. Decided (operator delegated) to run the diagnostic
   as a standalone Brief 1.5 *before* drafting Brief 2, so Brief 2 is
   built on a known contract not a guess. Brief 2 adopts Candidate B +
   the 3-encoding parser fix. Two data-quality items PARKED: the 34.8%
   start-less shells (should they exist?) and a DST near-midnight
   caveat in the offset analysis.

## Standing-instruction adherence check

- **DR-021 anchoring** — honoured (open 09:01 runner; re-anchored at
  re-locks 09:11 / 09:35; close 09:49).
- **Tool routing stated explicitly** — honoured throughout (Chat vs
  Code named at each hand-off).
- **Brief drafting: surface only operator decisions, technical detail
  autonomous** — honoured (the re-lock changelog + the diagnostic-first
  call surfaced; module/SQL/anchor detail handled inside artefacts).
- **Fenced content narrow-wrapped** — honoured (Code prompts + brief
  bodies ~60–70 cols).
- **DB reads read-only via `start_process` Python / never copy** —
  honoured (all Code DB work `mode=ro`; Chat ran no DB reads).
- **Session close produces a complete opening prompt unasked** —
  honoured (S205 prompt produced; Brief 2 auto-action).
- **Bethub session-open/close skills used** — honoured (fast-path open;
  full close ritual).

## Open items

Pointer-only — full detail in `current_state.md`.

**New / changed in S204:**
- Brief 1 RE-LOCKED v2 + EXECUTED — date endpoint LIVE + verified.
- race_date semantics DIAGNOSED — client query contract = Candidate B
  (window D−1/D/D+1 + UTC→Adelaide refine; start-less fall back to
  race_date==D). Brief 2's input.
- 3-encoding `scheduled_start` parser requirement (one breaks
  `fromisoformat`) — Brief 2 must handle.
- PARKED: 34.8% start-less discovery shells (data-quality, revisit);
  DST near-midnight caveat in the offset analysis.

**Carried to S205:**
- **Draft Brief 2** (`vps_client_api_rewrite_brief.md`: re-point the
  Mac lookup-trio + results at the API, picker from
  `/racing/races/{id}`, transport→503, + launcher fixes
  F9/F10/rebuild-if-source-newer) — **S205 AUTO-ACTION**, building on
  the Candidate B contract. Draft → operator review → lock → Code.
- Cash-modal back-stake blank (pre-cutover must-fix, small frontend).
- Settlement-worker brief (highest-risk; own bet-safety framing).
- Promo-seed item.
- W16 cutover scoping.
- Recovery monitoring (daily checks; first clean 1 Jul).
- Parking-lot items (see `current_state.md`).

## Open items out (closed this session)

- Brief 1 re-lock + execution + triage. ✅
- race_date semantics question (the timezone unknown from Brief 1's
  probe) — resolved into the Candidate B contract. ✅
- Diagnostic-first vs fold-into-Brief-2 routing call — decided
  (standalone first). ✅

## Session close state

- Rebuild folder root: Brief 1 v2 + its report, the diagnostic brief +
  its report all present. No phantom files (`system_snapshot.md` /
  `context_index.md` / `STATUS.md` / `CLAUDE.md` absent, per
  governance §1).
- `.close_out_backups/`: swept to hold only `SESSION_205_opening_
  prompt.md` after this close.
- `sessions/`: `SESSION_204.md` written.
- Project KB: optional re-upload of the two new briefs (Code reads
  from filesystem; not required for execution).

## Forward routing

**Confirmed with operator:** close S204, and draft Brief 2 as the
**auto-action** for S205. The S205 runner opens the session, runs the
open ritual, and auto-drafts Brief 2 against the Candidate B contract —
producing a DRAFT held for operator review (it does NOT lock or
commission Code unattended; the brief-drafting discipline keeps
operator sign-off before hand-off). On review → lock → Code prompt.

Then in order: cash-modal blank fix → settlement-worker brief →
promo-seed → W16 cutover. Recovery monitoring runs in the background
(first clean daily check 1 Jul).
