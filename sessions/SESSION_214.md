# Session 214 — settlement-worker diligence mapped; read-only Code investigation brief drafted, locked, and commissioned

**Opened:** 2026-07-01 15:41 ACST (headless runner, fast-path — result stamp 15:41:59, S213 close 15:36, fresh, session-number match)
**Closed:** 2026-07-01 16:54 ACST
**Tool routing:** Desktop Commander (filesystem/process) throughout — brief drafting, locking, session-record and governance-artefact writes. No Code executed inside this chat session; the settlement-worker investigation runs out-of-session against the locked brief once the operator pastes the commissioning prompt to Code.
**Governing DRs:** DR-021 (Adelaide timestamps, every anchor), DR-033 (settlement is the Betfair-operational side — the first money-path build item this stretch), DR-027/DR-028 (two-database boundary — settlement reads Betfair, writes v3 operational bet-state; re-confirmed clean at first read, folded into the brief as §5G), DR-032 (Betfair market as settlement spine, referenced not re-litigated).

## Anchor
- Open: runner fast-path, 15:41 ACST (result stamp 15:41:59; S213 close was 15:36 — fresh, session-number match).
- Close: `TZ="Australia/Adelaide" date` → 2026-07-01 16:54 ACST.

## Pre-flight checks
- Runner opened on the fresh S214 result (`settlement_worker_diligence_scope.md` already drafted by the headless runner at open); presented straight per the Step 0 fast-path (no re-verify).
- Root clean at open; `.close_out_backups/` held only `SESSION_214_opening_prompt.md`, expected and unremarkable pre-close (swept at Step 9 below).
- No phantom files.

## Session shape
A single-arc session, fully in the "Chat maps → Code grounds → Cowork gates" staged-hybrid pattern set at open. The runner had already produced the diligence scope document (`settlement_worker_diligence_scope.md`) as its S214 first action; this session's job was to get operator sign-off on the outsourcing route, then translate the scope doc's risk list into a locked, Code-bound investigation brief and hand it off. No triage of a Code report this session — that's S215's job once Code has run.

## What was delivered

1. **Fast-path open presented, route confirmed.** The runner's diligence scope map — settlement worker is fully coded/tested against fixtures but never wired live, manual-resolution path is live-wired but starved (feeds off an auto-worker that never runs) — was presented with the runner's staged-hybrid recommendation (Chat maps → Code grounds read-only → Cowork gates at the pre-W16 launch decision). Operator confirmed the route with a single "go."

2. **Read-only Code investigation brief drafted via the brief-drafting skill.** `settlement_worker_diligence_investigation_brief.md` (115 lines, 11,940 bytes, sha256 `40b65d25…`) — source-review shape (Session 33 precedent), seven per-area sections (§5A–§5G) each anchored on a specific claim from the scope doc: live-integration status (the headline "never wired" finding), test-coverage shape, the settlement→free-bet-credit failure window (the sharpest money-path risk), non-idempotent reconciliation bookkeeping, the v1 deferred/carve-out list, PROVISIONAL-parking exhaustiveness, and a quick two-database boundary re-check. Explicit calls surfaced at hand-off: no fresh pre-flight probe (leaned on the scope doc's own grounding, per the Session 35 well-anchored-prior-report precedent); 5A and 5B sequenced first since they calibrate confidence in the rest; output capped ~150–350 lines with no launch-readiness verdict (that stays operator-Claude territory next session).

3. **Brief LOCKED without a section-by-section walk.** Operator approved with "Good to go, please provide prompt" — a delegate-on-recommendation lock, matching the Session 35/36 precedent for tightly-anchored briefs grounded in a just-reviewed prior document, rather than the section-by-section cadence Session 39-style scope-defining briefs get.

4. **Ready-to-paste Code commissioning prompt produced.** The wrapper distinct from the brief itself, per standing pattern — names the read-and-confirm gate, the read-only scope, the hard limits, and the output spec, and instructs Code to start with the confirmation gate rather than running straight through. Handed to the operator to paste into Code out-of-session.

5. **First-action gate satisfied explicitly.** Operator's close instruction — "please close - triage report as first action" — is the confirmed forward routing this skill requires before close-out can complete (Step 2's hard first-action gate). S215's first action is the gated triage of `settlement_worker_diligence_investigation_report.md`, held if Code hasn't finished by then.

## Standing-instruction adherence
- Desktop Commander as default for all filesystem/process ops — honoured (with one mid-session correction: the brief was first drafted into Claude's own sandbox filesystem by mistake, caught before hand-off, and rewritten via Desktop Commander to the real project path).
- DR-021 Adelaide timestamps throughout — honoured.
- Brief-drafting ritual (grounded anchors from the scope doc, universal spine, explicit-calls surfaced, operator lock before hand-off) — honoured.
- Money-path diligence-first discipline — honoured; the staged-hybrid route keeps Chat from asserting live-code behaviour it can only read, not run.
- First-action gate (S200 hard instruction) — honoured; explicit operator confirmation obtained before this close-out proceeds.

## Open items
Pointer to `current_state.md`. New this session:
- **Settlement-worker investigation brief commissioned, awaiting Code execution.** S215 first action = gated triage of the resulting report (HOLD if Code hasn't run it yet).
- **Cowork multi-agent review still parked** for the pre-W16 go/no-go — unchanged, now explicitly the next gate after the settlement worker is wired toward launch.

Carried unchanged: placings burndown check (tonight's 05:30 ACST nightly run — still the next clean data point on the empty-runners contention fix); promo-seed → W16 cutover; Data Foundation harvest (parallel, not gating); full-backlog burn (downstream of the contention resolution); fault-B / `race_date` identity (parked, tripwire clean).

## Open items out
- Settlement-worker outsourcing-route decision (S214's own open question, set at S213 close) — CLOSED, staged hybrid confirmed by operator.
- Settlement-worker investigation brief drafting — CLOSED (locked + commissioned; execution is now Code's out-of-session job).

## Session close state
- Rebuild root clean; new artefacts `settlement_worker_diligence_scope.md` (from the runner's open) and `settlement_worker_diligence_investigation_brief.md` (LOCKED, this session) present. No report yet — Code hasn't run.
- `.close_out_backups/` → swept to `SESSION_215_opening_prompt.md` only, after this close.
- `current_state.md` rotated to the S214 close.
- `v3_build_picture.md` untouched — no formal build stream moved this session; settlement-worker diligence/investigation is tracked in `current_state.md` and session records, matching the S212/S213 precedent for the placings-recovery arc (in-flight diligence work off the formal stream table until it reaches a build-brief milestone).
- `standing_instructions.md` untouched — no instruction edits this session.

## Forward routing
**S215 first action (CONFIRMED with operator — "please close - triage report as first action") = gated triage of `settlement_worker_diligence_investigation_report.md`.** GATED per the established pattern (S192, S209, and others): if Code has run the investigation by S215 open, triage it against the locked brief's §7 success criteria and §8 output spec; if not, HOLD and surface that plainly rather than guessing at findings. On clean triage, the confirmed/refuted/indeterminate findings route to the next decision — most likely a settlement-worker build brief, or a further narrow investigation if something in §5A–§5G needs its own follow-up. Also carried, not gating: tonight's 05:30 ACST placings nightly run, worth a look at the next natural opportunity.
