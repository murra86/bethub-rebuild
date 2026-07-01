# Session 208 — Brief 2 re-drafted vs DR-034, reviewed, and LOCKED; two operator requirements written in; commissioned to Code (out-of-session) → S209 triages

**Opened:** 2026-06-30 13:33 ACST (runner fast-path open, HOLD)
**Closed:** 2026-06-30 14:21 ACST
**Tool routing:** Chat throughout (brief review, operator decisions, brief-lock edits, governance). No Code commissioned in-session — Brief 2 hands off to Code out-of-session at operator initiative. Filesystem read-write scoped to the brief artefact only; no DB queried this session.
**Governing DRs invoked:** DR-034 (canonical race-identity model, locked S206 — the load-bearing input to the brief), DR-028 (single integration boundary), DR-032 (Betfair market required at logging), DR-033 (placings analytical / settlement Betfair-only), DR-021 (Adelaide anchors).

---

## Anchor

- Open (runner): `2026-06-30 13:33 ACST` — fast-path, runner result `SESSION_208_opening_prompt_result.md` (ran 13:33:27).
- Close: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-06-30 14:21 ACST`.

Same-workday continuation of S207 (closed 13:24 ACST). ~48 min active. No split trigger fired (well under 3h, no day-rollover, clean scope — the planned brief-lock).

## Pre-flight checks

Runner fast-path presented a FRESH open result (run stamp 13:33:27 > S207 close 13:24, session number matched) and was surfaced straight per Step 0. Drift-check (in the runner result) was clean: `current_state.md` last-updated == 13:24; `SESSION_207.md` present + non-empty; `v3_build_picture.md` current. Close-side pre-flight directory listing clean — no `STATUS.md`/`CLAUDE.md`/`system_snapshot.md`. `.close_out_backups/` held only the consumed `SESSION_208_opening_prompt.md` (swept this close). Root carries the full data-foundation-arc brief/report set (legitimate, not phantoms).

## Session shape

A runner-opened HOLD that released in-session into a brief-lock. The Step-12 runner opened S208 at 13:33 and re-drafted Brief 2 (`vps_client_api_rewrite_brief.md`) against the now-locked DR-034 identity model, holding it as a DRAFT pending operator review of the four §12 calls. The session was operator-facing decision resolution off that hold: the operator accepted all four recommendations, asked what later work / dependencies they create (answered in plain language), and instructed lock with two small additions written in. Chat then locked the brief — resolved §12, wrote the two requirements into the body, flipped DRAFT→LOCKED, computed the sha — and produced the ready-to-paste Code prompt. No build, no Code commissioned in-session; bet-safe throughout (analytical/read-path + launcher brief only, no settlement/money-path touch).

## What was delivered

1. **Brief 2 LOCKED.** `vps_client_api_rewrite_brief.md` — the Mac `vps_client` lookup-trio + results rewrite (read the canonical store over the 8400 tunnel instead of the never-provisioned local `capture.db`) + the DR-034 read-time fragment-collapse + three launcher fixes (F9 back-off persistence, F10 single-session lock, rebuild-on-source-newer). Final: **601 lines, 31,633 bytes, sha256 `f7f5e7e3d1287c3975dc7d015ebabb6a672ddb094fe030d5f7fc040386c5ae28`** (prefix `f7f5e7e3`). Supersedes the S205 pre-DR-034 draft and the S208 held draft in place.

2. **§12 — all four operator calls RESOLVED at lock.** (1) **Collapse location → client-side; ship Brief 2 standalone, now** — no further VPS work; the broken `by-market` results route left in place but unused (tracked follow-up). (2) **No-Betfair-market races → drop from the picker.** (3) **Rewrite scope → lookup trio + results only** — other four `vps_client` surfaces stay a flagged follow-up. (4) **Tunnel → stays operator-managed**; tunnel-down → 503 gracefully; auto-start/health-check a flagged follow-up, not this pass.

3. **Two operator-added requirements written into the brief body.** (a) **Pinned VPS-completeness dependency (§5.2):** client-side collapse leans on the VPS enrichment fields (`n_runners`, `state`, results-present) staying intact; recorded as a standing assumption with the failure mode (silent degrade back to the row-order bug) and the existing guards (drop-counter + the mandatory §7 collapse test) named. No new runtime behaviour. (b) **Drop-counter (§5.2 step 3 / §8 §3):** the lookup counts dropped/empty-collapsed rows per call onto its structured log line; expected to track the ~0.3–1.9% ghost floor, so a count above floor is an early data-regression signal rather than a silent swallow. Observability only.

4. **Ready-to-paste Code prompt handed to operator.** A commissioning wrapper, not new scope: read the locked brief end-to-end then the §3 pre-reads in order (DR-034 first); confirm the four §3 Mac source anchors present before editing (STOP on drift); read-write scoped to §5 named anchors only; bet-safe (no settlement/money/capture.db copy/VPS change); single bounded session (over-budget → stop + report); output = the single named report `vps_client_api_rewrite_report.md` per §8.

## Standing-instruction adherence check

- **DR-021 anchors** — open 13:33 (runner) + close 14:21. ✓
- **Tool routing stated explicitly (Cat 1)** — Chat for brief review + lock; Code out-of-session for execution; S209 triage = Chat. Named on every routing point. ✓
- **Brief-drafting skill (Cat) exercised** — the lock path run per skill Step 5–7: explicit calls surfaced to operator, body edited to reflect resolutions, post-write verified (line/byte/sha captured here). ✓
- **Surface operator-relevant decisions only; handle technical detail autonomously** — the four §12 calls + the two added requirements framed for the operator's call; SQL/section-anchor detail handled inside the edits. ✓
- **Plain-language for operator** — delivered the "dumb-person-speak" dependency summary on request without drifting the underlying facts. ✓
- **DB reads** — none this session (no `capture.db`/VPS query); pure brief edit + filesystem. No DB-read discipline invoked.
- **Standing-instruction sweep** — no standing instruction authored or edited this session → close Step 7 skipped.

## Open items

Pointer-only — full list in `current_state.md`. New/changed this session:

- **Brief 2 — LOCKED + commissioned to Code (out-of-session)** (was: unblocked, to-be-drafted). Awaiting Code execution against the locked brief; `vps_client_api_rewrite_report.md` is the expected output. S209 triages it.
- **NEW follow-up — broken `by-market` results route** left in place but unused (consequence of the client-side collapse call). Tracked, not urgent; revisit if/when the VPS results path is next touched.
- **NEW standing assumption — VPS-completeness dependency** (pinned §5.2): any future VPS list-payload schema change (`n_runners`/`state`/results-present) must be checked against the lookup's completeness ordering before it ships.
- **(carry) Stall-alert threshold** — re-measure floor after first material burn (pair with 1 Jul daily check).
- **(carry) DR-034 stance-4 collapse remediation** — PARKED; downstream of burn, not a blocker.
- **(carry) Nightly throughput cap** — `BACKLOG_MAX_ATTEMPTS = 20` flagged as likely real burn-rate limiter; assess at 1 Jul.
- **(carry) Racing-API rate-tier reply** — awaited from `support@theracingapi.com`; fold into `BETHUB_DATA_REFERENCE.md` §G when it lands.

## Open items out (closed this session)

- Brief 2 drafting + lock (the S208 confirmed first action) — DONE; locked with two operator requirements written in. ✅

## Session close state

- Rebuild folder root: clean, no phantom files. `SESSION_208.md` written. `current_state.md` rotated to the 14:21 close. `v3_build_picture.md` updated (Brief 2 / Log-Past-Bet stream moved drafting-held → locked-and-commissioned; "Last updated" → 14:21).
- WIP: none in flight.
- `.close_out_backups/`: `SESSION_209_opening_prompt.md` staged (S208's consumed `SESSION_208_opening_prompt.md` swept).
- `sessions/`: SESSION_208.md present.
- `standing_instructions.md`: untouched (no edits this session).
- Bet-safety: CLEAN — analytical/read-path + launcher-brief authoring only; no v3 / settlement / money-path / v2 touch.

## Forward routing — CONFIRMED WITH OPERATOR

**S209 first action (CONFIRMED, GATED): triage the Brief 2 Code report.** IF `vps_client_api_rewrite_report.md` exists on disk AND post-dates this close (Code has run Brief 2) → triage it per the brief §8/§10 (did the DR-034 collapse return the most-complete fragment? did the transport-down → 503 wrap hold? launcher fixes verified? drop-counter at the ghost floor?), then either route a follow-up or mark Log Past Bet **live-proven**. ELSE (report absent) → **HOLD**: surface that Code hasn't yet run Brief 2 and await the operator, do not triage a non-existent file. Operator confirmed "triage on 209 open."

Then, in order: Log-Past-Bet live-proof → cash-modal blank fix (small frontend, must-fix) → settlement-worker brief (IOU + manual-match-to-lay) → promo-seed → W16 cutover. The Data Foundation harvest sits parallel and does NOT gate this line. Recovery monitoring continues (1 Jul first clean daily burndown check + the 20/night-cap assessment); Racing-API rate-tier reply awaited.
