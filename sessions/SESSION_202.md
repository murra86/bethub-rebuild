# Session 202 — launcher capture-data provisioning: investigated + locked

**Opened:** 2026-06-29 19:10 ACST (headless runner)
**Closed:** 2026-06-29 22:35 ACST
**Tool routing:** Chat (planning, decisions, governance, brief lock,
opening prompt). Claude Code (read-only investigation, out-of-session).
No Code build commissioned this session.
**Governing DRs:** DR-033 (placings analytical / settlement
Betfair-only), DR-027 / DR-028 (two-DB boundary + single integration
point — cross-DB seam touched), DR-021 (Adelaide anchors).

---

## Anchor

- **Open (runner):** 2026-06-29 19:10 ACST.
- **Close:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
  → `2026-06-29 22:35 ACST`.

## Pre-flight checks

- Runner opened S202 at 19:10 ACST; fresh against the S201 close
  (19:02) → the saved opening-prompt result was presented straight,
  no re-run of the open ritual.
- Pre-flight directory listing (close): rebuild root clean — no
  phantom files (`system_snapshot.md` / `STATUS.md` / `CLAUDE.md`
  correctly absent). Both S202 artefacts present.
- One anomaly surfaced + cleared: a `SESSION_9001_opening_prompt_
  result.md` in the runner results dir — read + confirmed a read-only
  watcher/plumbing test (no real session, nothing changed). Flagged
  harmless; operator to delete (Claude does not hard-delete).

## Session shape

A decision session: provisioning-path lock, driven by a read-only
Code investigation that overturned a premature call. The runner
opened S202, ran the two-part grounding, and drafted
`launcher_capture_provisioning_brief.md` (DRAFT). In-session, Chat
ran a read-only endpoint audit against the live `:8400` tunnel, drew
a (premature) "lock B, no interim" conclusion, then — at the
operator's request — commissioned a read-only Code investigation to
confirm understanding / limitations / gaps before any execution. The
investigation reshaped the path; the operator locked it; the
execution was split into two follow-on briefs deferred to S203 under
the session-close split discipline (late, deep close + a substantive
scope change).

## What was delivered

1. **Endpoint audit (read-only, live `:8400`).** 7 GET endpoints live
   + healthy; `/health` showed `collector_active:false`. Initial read
   ("lock B") was correct that the endpoints exist but missed the
   today-only limitation — caught by the investigation.

2. **Read-only Code investigation commissioned + triaged**
   (`launcher_capture_provisioning_investigation_report.md`, 380
   lines). Confirmed the S189 link gap end-to-end (missing
   `BETHUB_CAPTURE_DB_PATH` → unhandled `RuntimeError` → HTTP 500);
   found the API is **today-only** (no date param; date-aware variants
   404) → plain Option B regresses Log Past Bet to today's races;
   corrected the picker source (`/racing/races/{id}`, not the
   snapshot — snapshot carries no `betfair_selection_id`); flagged
   failure-must-map-to-503; confirmed the three launcher-fix anchors.

3. **Provisioning brief LOCKED + corrected**
   (`launcher_capture_provisioning_brief.md`). Path = **Option B +
   a date-aware VPS discovery endpoint**; A (SSHFS) and C (replica)
   rejected; two corrections folded in; F9 = back-off-timer-only,
   F12 = out; execution split into two briefs named in §6.

4. **Execution split defined (briefs deferred to S203):** Brief 1
   `vps_date_endpoint_brief.md` (VPS API, the small unblock) → Brief 2
   `vps_client_api_rewrite_brief.md` (Mac lookup-trio + results
   rewrite + the three launcher fixes).

## Standing-instruction adherence check

- **Tool routing stated explicitly** (Chat vs Code, with reason) —
  honoured throughout.
- **DB / system reads:** all read-only over the live tunnel /
  filesystem; no `capture.db` copy; GET-only on the API. Honoured.
- **Brief drafting — surface only operator-relevant decisions:**
  honoured (A-vs-B path, F9 kill-state policy, F12 surfaced; technical
  detail handled inside artefacts).
- **Session close — opening prompt always produced:** honoured
  (Step 8).
- **Fenced content narrow-wrap:** honoured (the Code investigation
  prompt was wrapped ~64 chars).
- **No standing-instruction edits this session** → no sweep, no
  Project-KB re-upload of `standing_instructions.md` required.

## Open items

Pointer — full live detail in `current_state.md`.

**New / changed in S202:**
- Provisioning path LOCKED (Option B + date-aware VPS endpoint);
  brief locked + corrected.
- Execution split into two S203 briefs (VPS date endpoint → Mac
  `vps_client` rewrite).
- F9 = back-off-timer-only; F12 = out (operator defaults).
- v2/v3 doc-hygiene note: the stored DB-read instruction points at a
  `bethub-v2` path while the active app is `bethub-v3` (all anchors
  resolved under v3). Left for operator confirmation; not actioned.

**Closed / done in S202:**
- Launcher capture-data provisioning — investigated + path locked. ✅
- Read-only Code investigation commissioned + triaged. ✅

**Carried to S203:**
- Draft Brief 1 (VPS date endpoint) → Brief 2 (Mac rewrite).
- Cash-modal back-stake blank (small frontend, must-fix).
- Settlement-worker brief. Promo-seed item. W16 cutover scoping.
- Recent-window placings-capture reliability (recovery monitoring).
- Parking-lot items (see `current_state.md`).

## Session close state

- `launcher_capture_provisioning_brief.md` — LOCKED (S202).
- `launcher_capture_provisioning_investigation_report.md` — present
  (Code, 380 lines).
- `sessions/SESSION_202.md` — this record.
- `current_state.md` — rotated to S202 (Last updated 22:35 ACST).
- `v3_build_picture.md` — updated (timestamp 22:35; S202 entry on the
  launcher-provisioning narrative).
- `.close_out_backups/SESSION_203_opening_prompt.md` — written.
- `SESSION_9001` watcher-test artefact in the runner results dir —
  flagged for operator deletion (harmless).

## Forward routing

**Confirmed with operator.** S203 first action = **provide a brief
overview of the two-brief execution plan and HOLD for operator
go-ahead** before drafting Brief 1 / commissioning any Code session.
Primary deliverable once go is given: draft Brief 1
(`vps_date_endpoint_brief.md`) then Brief 2
(`vps_client_api_rewrite_brief.md`). The runner launched at close
executes the first action (the overview + hold) automatically.
