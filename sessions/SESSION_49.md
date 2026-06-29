# Session 49 — Fix 7 design report triaged + Fix 8 merge-execution brief locked

**Opened:** 2026-05-01 19:00 ACST (Friday evening, +76 min after Session 48 close).
**Closed:** 2026-05-01 19:23 ACST (~23 min, single calendar day, same workday as Session 48).
**Tool routing:** Claude Chat.
**Governing DRs invoked:** DR-029 (active arc — Fix 7 triage + Fix 8 brief drafting against §2.1 surgical-fix arc); DR-027/028 (named at open, not invoked substantively — merge work is intra-`capture.db`); DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-05-01 19:00 ACST` at open and `2026-05-01 19:23 ACST` at close. Same workday as Session 48 close (17:44 ACST, +76 min) — calendar-calibrated short recap delivered.

## Pre-flight checks

- **Rebuild folder root at open:** 12 .md files plus expected directories. `.close_out_backups/` contained `SESSION_49_opening_prompt.md` only (per Session 48 close). No phantom files.
- **Drift-check Session 48 close-out:**
  - ✅ (a) `current_state.md` last-updated `2026-05-01 17:44 ACST` matches Session 48 close.
  - ✅ (b) `sessions/SESSION_48.md` exists, 170 lines, non-empty.
  - ✅ (c) `v3_build_picture.md` last-updated `2026-05-01 17:12 ACST` — predates Session 48 close, correct (Session 48 did not move streams, no update warranted).
- **`dr029/2_1_race_data/` at open:** confirmed `surgical_fix_7_design_report.md` (486 lines) had landed — Code finished out-of-session between Session 48 close and Session 49 open (Code wall-clock ~9 min, well inside brief's 60-90 min envelope). Saturday probe report not present (probe runs tomorrow morning).
- **V3 build picture inline:** skipped at open — no stream state moved since Session 48 close.
- **Open-items delta:** Fix 7 Code execution closed (design report landed). Saturday probe (WIP §17) and 23:30 nightly metadata-backfill verification flagged as within 24h. Surfaced explicitly.
- **23:30 ACST nightly metadata-backfill verification:** session opened at 19:00 — pre-23:30 — so verification probe deferred to Session 50 pre-flight. Surfaced rather than running blind against an unfired backfill.

## Session shape

Session 49 opened ~76 min after Session 48 closed. Fix 7 design report had landed during the gap (Code wall-clock ~9 min). Triage produced three load-bearing findings plus three anomalies surfaced for separate work. Operator confirmed default forward routing (commission Fix 8 directly) and delegated technical calls ("Please make any data structure/architecture or other technical calls, advise/request only where material operational impact and strategic direction required").

Brief drafting fired naturally on the operator's "Do now" trigger. End-to-end full-pass authoring — no section-by-section walk-through (operator delegated technical decisions, Session 35/36 surgical-fix precedent). Brief drafted at 485 lines (within 350-450 anticipation, slight overrun by ~35 lines, comparable to Fix 7 design brief's 283 lines for the smaller scoping shape and Fix 6's 352 lines for surgical execution shape).

Operator-language summary delivered at hand-off per `standing_instructions.md` Cat 1. Code hand-off prompt produced via `message_compose_v1`. Operator confirmed close at "Close session. Last session for the day" with explicit forward routing for Session 50 (Fix 8 triage primary, probe brief walk-through secondary).

## What was delivered

### Fix 7 design report triage (consumed)

`dr029/2_1_race_data/surgical_fix_7_design_report.md` (486 lines) read in full. Three load-bearing findings:

1. **No existing merge function in the racing-metadata-backfill service.** Race-row "merging" is purely an artefact of `upsert_race`'s `ON CONFLICT (race_date, venue_normalised, race_number) DO UPDATE SET col = COALESCE(excluded.col, col)` clause, firing at sync time when natural keys collide. Pre-existing orphans (where keys didn't collide because of venue-normalisation drift) are not retroactively merged. Brief §6 contingency triggered: Fix 8 framing shifts from "inspection of existing pattern" to "fresh design proposal".
2. **Runner-level convergence (Fix 5 §7b) has clean mechanistic explanation.** All 22,836 runners under merged race-rows are 100% Betfair-side because the Racing API returned EMPTY `runners` arrays for those races. Not a runner-key issue, not a code bug — Racing-API-response-shape issue. For the 784 mergeable subset, runner-key alignment is 96.2%.
3. **Survivor convention: LC-side (target) wins.** Reasoning: dependent-row volumes (~565k target-side vs ~83k orphan-side); preservation of stable Betfair market IDs and match metadata.

Three anomalies surfaced for separate work (none block Fix 8): §6a `has_subscription_sync` flag desync (4,063 rows), §6c three-row collision keys (52 instances), and Fix 9 (Racing API re-fetch for 2,081 already-merged race-rows).

### Fix 8 merge-execution brief locked (`dr029/2_1_race_data/surgical_fix_8_brief.md`, 485 lines)

Surgical-fix brief shape (Sessions 35/36 precedent), 11 numbered sections:

- **§1** What this brief is and is not — surgical write-execution, single bounded session, read-write on `capture.db`, read-only source tree.
- **§2** Why this work exists — one paragraph linking to DR-029 §2.1 close-with-known-debt-named and Fix 7 design report findings.
- **§3** Pre-reads — 4 required, 3 reference-only.
- **§4** System access — VPS, read-write DB, read-only source, no service touch, merge script outside source tree at `/root/fix_8_merge_execution.py`.
- **§5** Pre-flight verification (5 sub-steps) — plan re-derivation if post-23:30, baseline cross-tabs captured to JSON, UNIQUE pre-check on 784 set, runner-key alignment spot-check, FK integrity baseline.
- **§6** Substantive scope — script anchor (§6.1), per-merge transactional sequence with 6 steps a-f (§6.2), three-row collision handling (§6.3), logging discipline (§6.4).
- **§7** Sequencing within session — pre-flight → schema discovery → dry-run → live run → post-flight → report.
- **§8** Empirical verification (post-flight) — 7 sub-steps including race-level + runner-level cross-tab deltas, FK integrity, per-merge log audit, bookmaker_snapshots integrity, sample 5 races.
- **§9** Hard limits — 14 explicit items (§9.1 single bounded session, §9.2 source tree read-only, §9.3 no service touch, §9.4 no schema changes, §9.5 no DR-029 named-debt remediation, §9.6 no mid-session escalation, §9.7 preserve fix_5c/6c JSONs, §9.8 no execution outside the 784 clean set, §9.9 no Racing API re-fetch, §9.10 no `has_subscription_sync` root-cause, §9.11 no bookmaker_snapshots re-keying, §9.12 dirty-tree state preserved, §9.13 no git operations, §9.14 single execution).
- **§10** What happens after — operator-Claude triages the report; if material failure surface (>30 failures or any FK violations), pivot to operator-decision.
- **§11** Cross-references — DR anchors, prior reports, parking-lot exclusions.

### Calls made in brief, locked at hand-off

Per operator delegation ("Please make any data structure/architecture or other technical calls"), all technical calls were made silently and locked into the brief. Major calls:

1. **Per-merge transactional envelope.** `BEGIN ... COMMIT` per merge; 784 small commits. Rejected single-transaction-over-all-784 (rollback risk).
2. **Idempotency via orphan-row existence check.** Rejected `match_method = 'merged_via_fix_8'` marker (would overwrite meaningful matching provenance).
3. **Survivor = LC-side (target).** Adopted Fix 7 §C.5 recommendation. Per-merge action sequence: copy RA-side fields onto target via COALESCE → per-runner merge or re-point → re-point race-level dependents → DELETE orphan.
4. **Schema discovery before UPDATE construction.** Code reads `subscription/racing_api.py` and `storage/database.py` to derive authoritative subscription-sourced field lists for `races` and `runners`. Brief illustrative only on field names; the authoritative requirement is "every field the Racing API path populates and the live-capture path does not gets COALESCE-carried".
5. **Dry-run before live run.** Mandatory. Live run only proceeds if dry-run aggregate counts match Fix 7 §D.1 estimates within ±20%.
6. **Three-row collision handling.** Log to `/root/fix_8_three_row_log.json` for operator-Claude triage; do NOT auto-merge the third row.
7. **`has_subscription_sync = 1` written explicitly in step (b).** Closes anomaly §6a for the merged subset as side-effect; underlying bug deferred to proposed Fix 10.
8. **Runner-level UNIQUE conflict on dependent re-point handled by skip+log+continue.** Branch (c.3) — preserves transactional integrity, surfaces aggregate count in report.
9. **Adelaide-quiet window for execution.** Code's call on exact timing — post-jump pre-23:30, or post-23:30 with plan re-derivation. Either acceptable.
10. **Merge script lives outside source tree** at `/root/fix_8_merge_execution.py`. Source tree stays clean; dirty-tree baseline (11 modified + 7 untracked) structurally protected.

### Code hand-off prompt produced

Via `message_compose_v1` widget. Brief at canonical path, 4 pre-reads, key context (VPS, source-tree read-only, dirty-tree baseline, 784-merge target, transactional pattern, FK enforcement, Adelaide timestamps), 6-step execution shape, 9 hard limits highlighted, 30-45 min wall-clock estimate, report-only routing.

### High-level operator summary delivered

Plain-language closing per Cat 1. Four sub-sections: (a) what this fixes operationally — 784 races become analytically usable; (b) what it gets the operator — Strategy 1 cycle analysis on those races, ~1,957 runner rows gain finish positions, Harville calibration data widens; (c) what it doesn't fix — 555 still-orphaned races, 2,081 already-merged races' Betfair-only runner state; (d) risk profile + post-Fix-8 arc state.

## Standing-instruction adherence check

- **Default to luddite-analyst-gambler brevity** — held. Triage handed back as three-finding-plus-three-anomaly framing. Operator-language summary delivered at hand-off without prompting.
- **Escalate to detail only when warranted** — held. No escalations needed; operator pre-delegated technical decisions.
- **Calendar-calibrated session open** — held. Same-workday case (+76 min after Session 48 close) → tight recap delivered.
- **V3 build picture rendered inline at session open — conditional** — held. Skipped silently (no stream state moved).
- **Drift-check the previous session's close-out** — held. (a)/(b)/(c) all clean.
- **Open-items delta — conditional** — held. Rendered (Fix 7 Code execution closed; Saturday probe + 23:30 verification flagged as within 24h).
- **Cat 2 pointer (orientation summary delivers recap + drift-check + conditional renders)** — held.
- **Operator review of artefacts is between-session work** — held. Fix 7 design report consumed at open; Fix 8 brief is the artefact for next session's Code execution between sessions.
- **Operator-confirmed forward routing** — held. Session 50 ordering confirmed via direct operator statement: Fix 8 triage primary, probe brief walk-through secondary.
- **Don't drift to alternatives when the operator has been clear about today's work** — held. Operator said "Do now" with explicit delegation → drafted, produced prompt, summarised, closing.

Other adherence:

- DR-021 timestamp anchor at open and close — clean.
- Required reads completed in order at open — clean.
- Pre-flight directory listing before substantive work — clean.
- DR-029 / DR-027 / DR-028 / DR-021 named in orientation — clean.
- Desktop Commander routing — clean. Single-file `Desktop Commander:write_file` call for the 485-line brief.
- REPL discipline — N/A this session (no Python work; all writes via `Desktop Commander:write_file`).
- Live database queries via Desktop Commander start_process with Python — N/A this session (all DB-touching work deferred to Code's execution; Chat-side reads were file-only).
- Verify empirically — held. Fix 6c JSON path + structure verified before brief drafting; would have caught a path drift early.
- Operator-Claude division of labour — held. All software architecture decisions made by Claude per explicit operator delegation; only the close-out forward-routing question surfaced for operator decision (probe brief shape — answered "walk through one more time").

## Open items in

- **Phase 2 validation** — skills + opening prompts in parallel; Session 49 was fourth clean live run of all three skills (open + brief-drafting + close). Approaching evaluation point per `session_operations_proposal.md` §11.
- **WIP §1** — Fix 4 (cadence, needs probe) brief drafting still pending. Fix 8 brief locked this session.
- **WIP §13** — §2.10 carry, substantially fed by probe report §3.3 if probe runs clean Saturday.
- **WIP §16** — VPS in-flight work (11 modified, 7 untracked; +0 from Session 48 baseline; no edits this session — brief drafted Chat-side only).
- **WIP §17** — Saturday API observation probe runs tomorrow 2026-05-02 morning ACST. Brief at `dr029/2_1_race_data/api_probe_brief.md` (locked Session 39).
- **Pending architectural extension flagged Session 42** — "Betfair as canonical source" extending to all bet records. Lands in post-DR-029 documentation pass.
- **Fix 7 Code execution** — closed (executed during Session 48→49 gap, triaged Session 49).
- **NEW — Fix 8 Code execution pending** — operator runs Code out-of-session against locked brief; Session 50 (or wherever Fix 8 triage lands) reads execution report.
- **NEW — Fix 9 (Racing API re-fetch for 2,081 already-merged race-rows' runners)** — proposed in Fix 7 §6f and Fix 8 brief §10. Independent of Fix 8, can run in parallel post-Fix-8. Brief drafting deferred.
- **NEW — Fix 10 (`has_subscription_sync` flag desync root-cause diagnostic)** — proposed in Fix 7 §6a and Fix 8 brief §10. Anomaly's symptom closed for merged subset by Fix 8 step (b); underlying bug needs separate investigation.
- **NEW — Three-row collision per-row triage** — Fix 8 will surface count + state distribution to `/root/fix_8_three_row_log.json`. Operator-Claude triage post-Fix-8.
- **NEW — Low-confidence match review** (`time_proximity_only` cases) — flagged in Fix 7 §6g. Non-gating quality work.
- **23:30 ACST nightly metadata-backfill verification** — operator-Claude runs cheap read-only probe at Session 50 pre-flight to confirm tonight's run was clean.

## Open items out

- **Fix 7 Code execution** — closed.
- **Fix 7 design report triage** — closed.
- **Fix 5 §7b runner-level convergence finding** — closed mechanistically (Racing API empty runners arrays); the symptomatic gap will be closed for the 784-race subset by Fix 8.

## Session close state

- Rebuild folder root: 12 .md (unchanged this session).
- `dr029/2_1_race_data/`: gained `surgical_fix_7_design_report.md` (between Session 48 close and Session 49 open) and `surgical_fix_8_brief.md` (this session).
- `skills/`: unchanged (3 skill folders).
- WIP unchanged this session — open items rotate through `current_state.md` only.
- `.close_out_backups/`: contains `SESSION_50_opening_prompt.md` after this close (Session 49 opening prompt swept).
- Sessions: SESSION_49.md added.
- Standing instructions: unchanged (no new instructions surfaced this session).
- v3_build_picture: unchanged this close — Fix 7 design triage / Fix 8 brief authoring is within the §2.1 stream which remains `in flight` with the same next-milestone shape (Code execution pending). No stream state moved.
- Claude Project `bethub-rebuild` operational.

## Forward routing — confirmed with operator

**Session 50 primary path:** triage Code's Fix 8 execution report (assuming Code execution lands before Session 50 opens). Then walk the Saturday API observation probe brief one final time to confirm approach before the probe runs.

Required reads:
1. `current_state.md`.
2. `standing_instructions.md` in full.
3. `project_context.md`.
4. `sessions/SESSION_49.md`.

**Branch-specific (Fix 8 execution report triage):**
5. `dr029/2_1_race_data/surgical_fix_8_report.md` — Code's execution output.
6. `dr029/2_1_race_data/surgical_fix_8_brief.md` — for cross-reference.

**Branch-specific (probe brief final walk-through):**
7. `dr029/2_1_race_data/api_probe_brief.md` — Session 39 locked probe brief.

**Pre-flight verification at next session open:** B1 cross-tab on `races` table to confirm 23:30 nightly metadata-backfill ran clean overnight. If Fix 8 has executed before Session 50 opens, also confirm the post-Fix-8 cross-tab deltas match Code's report.

**Triage shape (Fix 8 path):** read headline (race-level + runner-level deltas, failure count); read §D live execution outcomes; read §E post-flight verification; read §6 anomalies (three-row collisions, FK violations if any, runner-level UNIQUE conflicts); read §8 proposed follow-ups. Decisions: confirm expected deltas landed; if material failure surface (>30 failures or any FK violations), pivot to operator-decision; if everything clean, walk probe brief next.

**Probe brief walk-through shape:** one final review of `api_probe_brief.md` per Session 39's locked content. Confirm: (a) probe scope still appropriate (5 questions, 4 races, parallel Racing API capture); (b) operator-side action prep clear (probe execution timing, output destination); (c) any redirection needed before probe runs Saturday morning. Probe brief is locked — review is verification, not amendment, unless something genuinely needs to shift.

Twenty-fourth consecutive non-early-close session.
