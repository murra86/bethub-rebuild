# Session 172 — BetLog live-validation probe: stale-build fix, delete-anomaly investigation, audit-log decision

**Opened:** 2026-06-21 15:38 ACST
**Closed:** 2026-06-22 15:42 ACST (multi-calendar-day session — day-rollover during operator-away gap)
**Tool routing:** Claude Chat (planning / triage / investigation). No Code session commissioned. Read-only diagnostics via Desktop Commander `start_process` (uv run), all against live repo + DB without writes.
**Governing DRs invoked:** DR-021 (anchors), DR-013 (read-only DB discipline — `mode=ro`, throwaway temp DB for the delete probe, never copy live), DR-030/031 (read the v3 surfaces in place), DR-032 (Betfair-canonical clarified: settlement-state update, not record deletion).

---

## Anchor

- Open: `TZ="Australia/Adelaide" date` → `2026-06-21 15:38 ACST`
- Close: `TZ="Australia/Adelaide" date` → `2026-06-22 15:42 ACST`

## Pre-flight checks

Open-ritual drift-check was clean: `current_state.md` last-updated (2026-06-20 16:27) matched SESSION_171 close; SESSION_171.md present + non-empty; `v3_build_picture.md` updated at S171 close (BetLog built). Directory clean, no phantom files. `.close_out_backups/` held only `SESSION_172_opening_prompt.md` (expected, unconsumed — operator opened by command).

## Session shape

Opened intending to draft **brief 2 (manual entry)**, beginning with the capture.db retention check. It **pivoted entirely** into an unplanned probe-triage session: the operator reported BetLog wasn't reachable, and pursuing that surfaced a chain of findings about the BetLog surface that were worth running to ground before laying new work on top. No brief was drafted; the capture.db retention check was **not** run. Brief 2 carries to S173 unchanged. This was an investigation/governance session, not a build session — the value delivered is diagnostic certainty about the delete path plus a scoped, agreed plan for the audit log and the feed-robustness fix.

## What was delivered

1. **BetLog stale-build — diagnosed and resolved.** BetLog was absent from the v3 nav menu. Cause was not missing code: source `App.tsx` had the import, the nav `<Link to="/betlog">`, and the route, and `BetLog.tsx` was written 2026-06-20 15:51. The served bundle `ui/web/dist/` was dated 2026-06-17 — three days stale. The launcher (`BetHub.command`) only builds the frontend when `dist/index.html` is **absent**; it does not rebuild when source is newer. Operator ran `npm run build` (regenerated dist, new bundle confirmed to contain BetLog) and relaunched; after a hard refresh, BetLog appears. **Closes the S171 "validate BetLog live" pending action.** The recurring trap (every Code rebuild leaves a stale served bundle until manual rebuild) is reinforced as a launcher-hardening item — fold a "rebuild if source newer than dist" check into the F9/F10 launcher brief.

2. **Bets-feed robustness bug — confirmed, root cause unpinned.** The error the operator hit ("Failed to load bets: API 500 on GET /api/v1/bets") is the BetLog **list refresh** (react-query invalidation after a delete), not the delete itself. The feed serialises the whole page as a unit, so if a single row fails to construct server-side the **entire list 500s** and BetLog goes blank. Reproduced the GET in-process against the live DB → 200 on the now-empty table, so the read code is sound on clean data. Could not pin the exact triggering field: the offending rows are gone (no repro), the leg + required bet columns are all NOT NULL in schema (rules out a null-field serialization break), and `bet_net_pnl` is defensively coded (returns Decimal('0') on null stakes/prices/commissions — no obvious throw). **Fix is robustness, not a one-line patch:** isolate per-row construction so one bad row is skipped + flagged rather than killing the feed, and surface the real server error for diagnosis. **Folding into brief 2** (manual entry creates exactly the hand-made rows that can trip serialization, so it is the natural home).

3. **Delete-anomaly investigation — delete path exhaustively verified safe.** Operator reported deleting one of three same-runner test bets, then a 500 on attempting the second, and later all three were gone. Investigated the operator's cascade hypothesis (same runner / shared serial → all deleted together) and a later hypothesis (unfilled bets auto-removed by Betfair-canonical reconciliation). **Both ruled out by code, conclusively:**
   - Store `delete_bet` (`store/repositories/bets.py:1140`) deletes exactly one bet by primary key (`bet_id`), legs then bet, in one transaction, no `ON DELETE CASCADE`. It **blocks** (no-op + "blocked:" message) when any other bet shares the `cycle_id`, or when ops_events/promo_events reference it.
   - `bet_id` is the `bets` PRIMARY KEY; the only two `DELETE FROM` statements in the entire repo (excluding tests) are these two lines. Nothing else calls `delete_bet`. No background worker, sync, reconciliation, trigger, cascade, executescript, or canonical-rebuild removes bets. (`replace_bet` is the Betfair exchange cancel/replace order op, not a local delete; `consumer.py` "Betfair authoritative for settlement state" = an **update**, not a delete.)
   - Frontend: each row's Delete button calls `deleteBet(bet.bet_id)` — one bet per click; button disabled while its own delete is pending; mutation has no retry (queryClient sets `retry:false` on queries, no mutation override → react-query default 0); `apiDelete` is a single fetch; no `useEffect` fires a delete.
   - **Empirical proof:** an isolated throwaway-DB test using the real schema + real `delete_bet` — three bets on the identical runner (same market 1.234567 / selection 99999), different stakes/times — deleting one left the other two (3→2); with all three sharing a cycle, the delete **refused** and left all three. Zero writes to live data.
   - **Conclusion:** no code path removes a bet without the Delete button being invoked on that specific bet. Three bets gone ⇒ three DELETE requests reached the server. The click-level "how" of the third can't be reconstructed (no request log kept from that session). The honest residual ambiguity is precisely the argument for the audit log (item 5).

4. **Unfilled-bet retention — confirmed met by architecture.** The three test bets were all unmatched (never filled). Clarified for the operator that this is *why they were in BetLog at all* — the tool already retains unfilled/partially-filled bets; they did not vanish for being unfilled, they were deleted. Data model supports partial fills natively (`match_status`, `matched_stake`, `unmatched_stake` are distinct columns). "Betfair canonical" = authoritative for **settlement state** (update), never deletion of local records. Spot-check that the placement path *writes* a never-matched bet correctly to be folded into brief 2 (evidence so far: it does — the operator saw them).

5. **Audit-log decision — queued as its own fenced brief, after manual entry.** Candid assessment delivered: worth building, because it is the safest category (append-only), it reuses an existing pattern (`ops_events` / operations log / cash-flow event log already in the system — not net-new plumbing), and it directly kills the investigation pain this session demonstrated. **Cardinal design constraint:** the audit write must be append-only and **decoupled** — never inside the bet-write/settlement transaction, never a trigger that could roll back a real bet. Scope minimal: record add/edit/delete events (timestamp, bet_id, source, before→after snapshot); no UI/analytics initially. **Not cutover-critical** — sequenced *after* brief 2 as its own small brief, not bolted on. Operator endorsed, with an explicit concern (shared by Claude) about not adding complexity that becomes its own bug surface — hence the hard fencing.

6. **Dark theme — parked.** Operator asked for an all-pages dark interface, then parked it "until the right time." Scoping note for whenever it lands: there is **no theme-token system** today — colours are hardcoded across ~13 CSS module files with no CSS custom properties. Doing dark properly means introducing a shared colour-variable layer and repointing the modules at it, then setting a dark palette — a bounded but real frontend refactor, Code's lane (a brief). Carried as an open item.

## Standing-instruction adherence check

- **Cat 1 (software calls are Claude's):** honoured — Claude made the fix-now/defer calls, investigated rather than punting, ran read-only diagnostics, and did not edit v3 code from Chat. Routed all code changes (feed-robustness, audit log, dark theme) to Code-brief territory.
- **Cat 1 (candour / push-back):** honoured — pushed back firmly on both the cascade and the unfilled-auto-removal hypotheses with evidence, rather than agreeing; gave a discriminating (not reflexive) yes on the audit log.
- **Cat 1 (brevity / lead with the call):** honoured.
- **Cat 1 (V3 build picture render at open — conditional):** rendered at S172 open (streams had moved at S171 close).
- **Cat 2 (DR-021 anchors):** honoured — open + close anchored.
- **Cat 2 (read-only DB discipline / DR-013):** honoured — `mode=ro` for live reads, throwaway temp DB for the delete probe, zero writes to live data or repo.
- **Cat 2 (session ritual):** open + close rituals run via skills.
- No new standing instruction authored this session → no `standing_instructions.md` sweep needed.

## Open items

Pointer-only — full live list in `current_state.md`.

## Open items out (closed this session)

- **Validate BetLog live** (S171 pending operator action) — done; root-caused the stale-build absence, operator rebuilt + relaunched, BetLog confirmed in the menu. ✅
- **The delete anomaly** — investigated to conclusion: delete path is provably single-row and fenced; no auto-removal path exists anywhere in the codebase. Closed as a finding (no fix needed on the delete side). ✅

## New items in (this session)

- **Bets-feed robustness fix** → folded into brief 2 (one bad row must not 500 the whole feed; surface real server error).
- **Bet-mutation audit log** → own fenced brief, after brief 2 (append-only, decoupled, reuses ops_events pattern, must never touch the bet-write path).
- **Dark theme** → parked; needs a theme-token refactor (Code brief) when the time is right.
- **Launcher: rebuild-if-source-newer** → reinforced into the F9/F10 launcher brief (stale-bundle trap).
- **Manual-entry write-path spot-check** (does a never-matched bet persist) → fold into brief 2.

## Session close state

- **Rebuild folder root:** clean, no phantom files.
- **WIP / `work_in_progress.md`:** untouched this session.
- **`.close_out_backups/`:** `SESSION_173_opening_prompt.md` written; stale `SESSION_172_opening_prompt.md` removed.
- **`sessions/`:** SESSION_172.md written (this file).
- **`v3_build_picture.md`:** untouched — no stream status or next-milestone label moved (BetLog was already marked built at S171 close; brief 2 remains Interface-refinement's next milestone).
- **Project knowledge base:** `standing_instructions.md` re-upload remains carried/outstanding (unchanged since S163).

## Forward routing — CONFIRMED WITH OPERATOR

Next session (S173) does **brief 2 — after-the-fact manual entry**, opening with the capture.db retention check (read-only, VPS via SSH tunnel, never copy; DR-027/028 re-read trigger). The bets-feed robustness guard and the manual-entry write-path spot-check fold into that brief. The **bet-mutation audit log** is queued as its own small fenced brief immediately after manual entry. **Dark theme** stays parked. Launcher brief (F9/F10 + rebuild-if-source-newer) remains pending/independent. Operator confirmed by closing the session on "we'll continue next session" after explicitly endorsing this plan.
