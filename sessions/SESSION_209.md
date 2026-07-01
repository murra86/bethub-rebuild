# Session 209 — Brief 2 Code report TRIAGED → Log Past Bet LIVE-PROVEN; drop-counter floor recalibrated to an empirical band

**Opened:** 2026-06-30 14:31 ACST (runner fast-path open, HELD at the gate)
**Closed:** 2026-06-30 15:14 ACST
**Tool routing:** Chat for the triage, the operator decisions, and the follow-up brief authoring + write; Code in-session (operator-run, out-of-session-style) for the live-proof + floor recalibration. Filesystem read-write scoped to the two new rebuild-root artefacts (`log_past_bet_liveproof_brief.md`, then its report read-back). The live resolve + 14-day floor measurement were read-only GETs over the operator-managed 8400 tunnel; one `_lookup_api.py` constant edited on the v3 repo by Code (checkpoint `b0f05b0`).
**Governing DRs invoked:** DR-034 (canonical race-identity model / most-complete-fragment collapse — the thing live-proven), DR-032 (Betfair market required at logging — why no-market races drop), DR-033 (analytical/settlement split), DR-028 (single integration boundary — the HTTP read path), DR-021 (Adelaide anchors).

---

## Anchor

- Open (runner): `2026-06-30 14:31 ACST` — fast-path, runner result `SESSION_209_opening_prompt_result.md` (ran 14:31:51), presented HELD (Brief 2 report absent at open).
- Close: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-06-30 15:14 ACST`.

Same-workday continuation of S208 (closed 14:21 ACST). ~43 min active. No split trigger fired (well under 3h, no day-rollover, clean scope — triage + one bounded follow-up).

## Pre-flight checks

Runner fast-path presented a FRESH open result (run stamp 14:31:51 > S208 close 14:21, session number matched) and was surfaced straight per Step 0 — opened HELD because `vps_client_api_rewrite_report.md` was absent (Code had not yet run Brief 2). Drift-check (in the runner result) was clean: `current_state.md` last-updated == 14:21; `SESSION_208.md` present + non-empty (9,283 B); `v3_build_picture.md` current; locked Brief 2 sha/size matched (`f7f5e7e3…`, 601/31,633). One housekeeping drift surfaced by the runner: `.close_out_backups/` held the leftover `SESSION_208_opening_prompt.md` alongside `SESSION_209_opening_prompt.md` — both swept this close. Close-side pre-flight directory listing clean — no `STATUS.md`/`CLAUDE.md`/`system_snapshot.md`; root carries the full data-foundation-arc brief/report set + the two new S209 artefacts (legitimate, not phantoms).

## Session shape

A runner-opened HOLD that released when the operator ran Brief 2 in Code in-session. Three strands. First, the triage: the operator ran Brief 2, `vps_client_api_rewrite_report.md` landed (344 lines), and Chat triaged it against the brief §8/§10 — all three gate questions passed, two items held the live-proven label, one Code finding accepted as-built. Second, the operator (non-technical, per the standing plain-language requirement) asked for the triage in plain terms and chose to close the two open items with one final verification pass. Third, Chat drafted + wrote a tight follow-up brief (`log_past_bet_liveproof_brief.md`) via the brief-drafting skill, the operator ran it in Code in-session, and its report (`log_past_bet_liveproof_report.md`, 178 lines) was triaged — both items closed, Log Past Bet marked LIVE-PROVEN. Bet-safe throughout (read-only analytical GETs + one observability constant; no settlement/money/lay/capture.db/VPS path).

## What was delivered

1. **Brief 2 report TRIAGED — all three S209 gate questions PASS.** The DR-034 most-complete-fragment read-time collapse returns the populated fragment (client-layer live smoke on the 2026-06-29 Emerald duplicate market `1.259530858` — 13 runners, not the 0-runner shell); transport-down → 503 wrap holds across the three lookup routes; F9 back-off-survives-restart / F10 single-session-lock / rebuild-on-source-newer all verified. Tests 1202 passed / 1 pre-existing xfail; `ruff` clean; bet-safety CLEAN. No surgical fix needed on the rewrite itself.

2. **Code finding #1 ACCEPTED as-built (operator-Claude triage call).** The list payload's `state` field is the geographic state, not settlement status, so the brief's §5.2 "settled-first" completeness order is not implementable from list fields. Code ranks fragments by `n_runners` → source-breadth → recency instead — which satisfies the load-bearing shell-vs-populated property and the mandatory §7 test (the 0-runner PENDING shell always loses to the populated fragment). Accepted; NOT re-opened. The pinned §5.2 VPS-completeness dependency now rests on `n_runners` + `sources_with_data` accuracy. The rare settled-vs-pending-both-populated edge (a results-fetch could land on the pending sibling) parked as a tracked follow-up.

3. **Two held items closed by a follow-up brief — run in-session.** `log_past_bet_liveproof_brief.md` (DRAFT S209, operator-approved) commissioned: (§5.1) the live route-bridge resolve and (§5.2) the floor recalibration. Code ran it and `log_past_bet_liveproof_report.md` (178 lines) landed:
   - **§5.1 — live-proven.** Driven through the real FastAPI app (`TestClient` → route bridge → client → live 8400 tunnel, default-raises-on-500): `lookup/races` for 2026-06-29 Emerald lists R7 exactly once; `lookup/race` → **200 + 13 runners** ("Flexihire Emerald Hcp"), never the 0-runner shell; clean Albury R1 → 200, 9 runners. This closes the live-proof gap Brief 2's client-layer smoke left — the collapse holds in the running request path on live data. **S189 live-proven gate satisfied.**
   - **§5.2 — floor recalibrated.** Measured the no-market drop fraction over 14 captured days (min 0.517, max 0.822, mean 0.712, median 0.730 — all normal; the high rate is the correct steady state, most captured races being non-Betfair greyhound/harness, dropped per DR-032 / DR-034 stance 3). Replaced the dead `NO_MARKET_FLOOR_LOW/HIGH = 0.003/0.019` with a two-sided band `NO_MARKET_NORMAL_LOW/HIGH = 0.40/0.90` (`above_floor` → `outside_normal_band`): fires > 0.90 (enrichment stale / market ids dropping out) or < 0.40 (a non-Betfair source vanished), False on every normal day — demonstrated live + synthetically.
   - Edit confined to the §5.2 band constant + its comparison + log line; parser/Candidate-B/collapse/ordering byte-for-byte unchanged; finding #1 not re-opened. `ruff` clean; `tests/clients/vps_client/` 71 passed; full repo 1202 passed / 1 xfailed (unchanged). One checkpoint commit `b0f05b0` (only `_lookup_api.py`). Bet-safety CLEAN.

4. **Log Past Bet → LIVE-PROVEN.** Both §10 triage decisions resolved: the route-bridge resolve returned the populated fragment (mark live-proven), and the [0.40, 0.90] band is sensible (confirmed). The feature is complete — a bet on a finished race resolves the correct race data end-to-end in the running app.

## Standing-instruction adherence check

- **DR-021 anchors** — open 14:31 (runner) + close 15:14. ✓
- **Tool routing stated explicitly (Cat 1)** — Chat for triage + brief authoring; Code in-session for the live-proof + floor edit; named at each point. ✓
- **Surface operator-relevant decisions only; handle technical detail autonomously (Cat / memory)** — the two open items + the live-proven call surfaced; the brief's anchors, the band maths, and the route-bridge mechanics handled inside the artefact. ✓
- **Plain-language for operator** — after an over-technical first triage, corrected to a dumb-high-level explanation + tappable decision on operator request; held that register for the rest of the session. ✓ (The operator re-flagged this preference; it is memory #16 — honoured, not re-authored.)
- **Brief-drafting skill exercised** — `log_past_bet_liveproof_brief.md` drafted per the skill (surgical-fix + verification shape; calls surfaced; written + read-back). Locked on operator go-ahead (the "give me the prompt" + run was the approval). ✓
- **DB reads** — none direct; the live resolve + 14-day measure were Code-side read-only GETs over the tunnel. No `capture.db` open/copy. ✓
- **Standing-instruction sweep** — no standing instruction authored or edited this session → close Step 7 skipped.

## Open items

Pointer-only — full list in `current_state.md`. New/changed this session:

- **Log Past Bet — LIVE-PROVEN** (was: implemented, awaiting live-proof). Feature complete; the live-integration item closes.
- **NEW follow-up — settled-vs-pending-both-populated ordering edge.** With the accepted `n_runners`→source→recency ordering, a market whose fragments are BOTH fully populated (one settled, one pending) resolves by recency, so a results-fetch could land on the pending sibling (soft NOT_YET_CAPTURED, not a wrong settlement). Rare (the dominant duplicate case is shell-vs-populated). Tracked, not urgent.
- **(carry) Cash-modal back-stake blank fix** — now next in the build queue; S210 opens onto it.
- **(carry) Stall-alert threshold / DR-034 stance-4 collapse remediation** — PARKED; re-measure floor after first material burn (pair with 1 Jul daily check).
- **(carry) Nightly throughput cap** `BACKLOG_MAX_ATTEMPTS = 20` — assess at 1 Jul.
- **(carry) Racing-API rate-tier reply** — awaited from `support@theracingapi.com`.

## Open items out (closed this session)

- **Brief 2 Code report triage** (the S209 confirmed first action) — DONE; all three gate questions passed. ✅
- **Log-Past-Bet live-proof** — DONE; route-bridge resolve proven on live data, S189 taxonomy satisfied. ✅
- **Drop-counter floor mismatch** (Brief 2 finding #2) — DONE; recalibrated to the empirical [0.40, 0.90] band. ✅

## Session close state

- Rebuild folder root: clean, no phantom files. `SESSION_209.md` written. `current_state.md` rotated to the 15:14 close. `v3_build_picture.md` updated (Log-Past-Bet stream moved implemented → LIVE-PROVEN; "Last updated" → 15:14). Two new artefacts at root: `log_past_bet_liveproof_brief.md`, `log_past_bet_liveproof_report.md`.
- WIP: none in flight.
- `.close_out_backups/`: `SESSION_210_opening_prompt.md` staged; the consumed `SESSION_208_opening_prompt.md` and `SESSION_209_opening_prompt.md` swept.
- `sessions/`: SESSION_209.md present.
- `standing_instructions.md`: untouched (no edits this session).
- v3 repo (`bethub-v3`): one checkpoint commit `b0f05b0` on `main` (only `clients/vps_client/v1/_lookup_api.py` — the floor→band constant), made by Code in-session.
- Bet-safety: CLEAN — read-only analytical GETs over the tunnel + one observability constant; no v3 settlement / money-path / lay / capture.db / VPS / v2 touch.

## Forward routing — CONFIRMED WITH OPERATOR

**S210 first action (CONFIRMED, no gate): a short, non-technical overview of the bet-entry (cash-modal) screen + the proposed approach.** The operator explicitly set this as the S210 auto-action at close. It opens the cash-modal back-stake blank fix — the small-but-must-fix frontend item where, in cash-lay mode, the back-stake box seeds off the soft price rather than a dollar stake, under-sizing a cash lay if not overwritten (the lay PRICE is unaffected — always live from Betfair; free-bet mode, ~99% of use, carries face value through correctly). S210 opens with the plain overview + approach, then proceeds into scoping the fix.

Then, in order: cash-modal blank fix → settlement-worker brief (IOU + manual-match-to-lay) → promo-seed → W16 cutover. The Data Foundation harvest sits parallel and does NOT gate this line. Recovery monitoring continues (1 Jul first clean daily burndown check + the 20/night-cap assessment); Racing-API rate-tier reply awaited. The settled-vs-pending ordering edge is a tracked follow-up, not gating.
