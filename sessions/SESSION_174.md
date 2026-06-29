# Session 174 — finish-position pipeline diagnosed; data-source roles locked (DR-033)

**Opened:** 2026-06-22 17:40 ACST
**Closed:** 2026-06-22 19:22 ACST
**Duration:** ~1h40m active, single workday, no day-rollover.
**Tool routing:** Claude Chat (planning / triage / governance) + Desktop Commander (governance reads/writes, local jq/python, read-only VPS SSH probe of capture.db, v3 codebase reads). No Code session.
**Governing DRs invoked:** DR-021 (anchoring), DR-027/028 (two-database boundary — re-read trigger fired on the `settlement.py` read), DR-029 (data-layer fit — results-coverage assumption examined), DR-032 (Betfair canonical reference; Racing API thoroughbred coverage), and the NEW **DR-033** (data-source roles, locked this session).

---

## Anchor

- **Open:** `2026-06-22 17:40 ACST` (session-open ritual).
- **Close:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-06-22 19:22 ACST`.
- S173 closed 17:21 ACST; S174 opened 19 min later — straight same-workday continuation.

## Pre-flight checks

- Open ritual ran clean: drift-check passed (current_state ↔ SESSION_173 ↔ v3_build_picture all matched the 17:21 S173 close); `.close_out_backups/` held only the S174 opening prompt; rebuild root clean.
- Required reads completed in order (current_state, standing_instructions in full, project_context, SESSION_173, betlog_scope).

## Session shape

A single-thread session that started as the S174 strand-1/strand-2 diagnostic and broadened into a governance lock. The operator opened by reframing: since Safety Net refunds are manually triggered, the finish-position gap is not a live-settlement scramble but a "why did the placings stop, and can we get them back for analytics" question. The diagnostic ran read-only against the live VPS (capture.db + the racing-data-capture code + systemd timers) and the v3 codebase, found the root cause, then pivoted — at the operator's lead — into resolving the recurring Betfair-vs-Racing-API "which does what" confusion by writing a capability/role reference doc, locking the roles as a numbered DR, and generating a field-level Racing API catalogue. Closed with the data layer understood and the role split locked.

## What was delivered

1. **Root cause of the finish-position gap — found.** Placings have only ever come from the Racing API (the "subscription" source); Betfair never supplies a finishing position (`fp_betfair` = 0 every month). The fill faded — ~80% Nov–Feb → ~20% Mar → ~6% Apr → ~0.1% May → ~0 Jun — coinciding exactly with the **March 2** `subscription/` module rework (dir dated Mar 2, `racing_api.py` Mar 4), which tripled coverage but starved the results write-back. Mechanism: `sync_day()` (which writes `finish_position` from the API's `position` field) is only ever called by the backfill scripts, driven by `racing-metadata-backfill.timer`. That nightly job runs `backfill_race_metadata.py` with no args → `get_unsynced_dates()` → only dates where `subscription_synced_at IS NULL`. So each date is synced **once**, at night, **before** results publish, then never re-pulled. Form lands; results don't. The feed is otherwise healthy (metadata syncing to present).

2. **Backfill confirmed feasible.** `sync_day()` is idempotent (upsert + `finish_position = COALESCE(?, finish_position)` — fills blanks, never clobbers). Re-running it for the now-resulted gap dates pulls `position` for every runner. AU data comes via `/v1/australia/meets` + `/v1/australia/meets/{id}/races`; the gap (Mar–Jun) sits inside the 12-month window. No paid history add-on needed.

3. **Live settlement confirmed Betfair-only.** v3 `workflows/bet_entry/v1/settlement.py` settles purely off the leg's `betfair_market_id` + `betfair_selection_id` (WINNER→SETTLED_WON, LOSER→SETTLED_LOST); greps for `finish_position` / `capture` / `vps_client` returned nothing. So the gap never touched live settlement, and place refunds are a manual flag regardless.

4. **Data-source role confusion resolved + documented.** Wrote `data_sources.md` (rebuild root): Part 1 capability (what each source *can* provide), Part 2 assigned role (what we *use* each for — DR-locked), Part 3 deferred/open. Capability and role kept deliberately separate so future moves are decided against a known menu, not rediscovered. On-demand reference — NOT a session-open read (keeps the recurring-load footprint to the DR alone).

5. **DR-033 locked** (`decisions.md`): Betfair = operational (pricing, placement, win/lose settlement, identity, sports settlement); Racing API = analytical/enrichment (racing only); place/ordinal settlement stays manual; sports enrichment = future separate subscription. Rule: *Betfair settles + operates; the Racing API enriches + feeds analytics; overlap is capability, not shared duty.* Sits on top of DR-027/028 + DR-032 without altering them. Deferred items named (auto-settle place refunds, sports-enrichment subscription, analytics spec).

6. **Racing API field catalogue generated.** `racing_api_field_catalogue.md` (58 endpoints with plan tiers + rate limits; 124 schemas field-by-field with types) via committed generator `gen_racing_api_catalogue.py` — one-command refresh, no hand-maintenance/rot. Pointers wired into `data_sources.md` (Racing API → the catalogue; Betfair → its captured Confluence pages, since it has no local machine spec).

7. **Tier correction surfaced by the catalogue.** The AU endpoints we use sit on the **"Australia regional add-on"** tier, not "Standard" (that's the UK/IRE `/v1/results` path). So the ~$100/mo is essentially the AU add-on — the exact feed delivering placings + enrichment. Reinforces: do not cancel the Racing API. Corrected in `data_sources.md`.

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open 17:40 + close 19:22 ACST. ✓
- **DB read discipline (mode=ro, never copy):** capture.db opened read-only via URI over SSH; only schema/aggregates/samples returned; no copy to local disk. ✓
- **DR-027/028 re-read trigger (Cat 1 / sensitivity):** fired on the `settlement.py` read; settlement confirmed Betfair-only with no cross-DB read in the live path. The direct capture.db probe was the sanctioned Chat-side read-only governance exception (DR-028 blesses unlimited reads). ✓
- **`create_file` banned / verify every write (Cat 3):** all writes via `Desktop Commander:write_file` / `edit_block`; each governance write verified via read/grep (DR-033 grep'd at line 1282; data_sources.md re-read after each edit). ✓
- **Empirical verification before editing governance artefacts (Cat 3):** re-read `decisions.md` tail (DR format + next number = 033, separator style) before appending. ✓
- **REPL / script discipline (Cat 3):** probe scripts written to `/tmp` then run via `start_process`; generator written to disk then run; no multi-line REPL paste. ✓
- **Make-the-call / don't punt (Cat 5):** doc-shape + DR-proportionality + generate-don't-transcribe were Claude's calls; role split, manual-flag, and doc/DR location were surfaced as operator calls. ✓
- **Plain-language / decision-maker framing / brevity (Cat 1):** maintained; operator confirmed understanding at each step. ✓
- No standing instruction authored or edited this session.

## Open items in (carried / new for S175)

- **NEW — backfill the Mar–Jun placings.** Re-pull the Racing API for the gap dates (`sync_day` for resulted dates; idempotent; AU add-on tier; inside 12-mo window). VPS **write** — needs operator greenlight; safe one-day test first.
- **NEW — fix the nightly results-sync.** The `get_unsynced_dates` one-shot-before-results logic must gain a re-sync-after-results pass (e.g. re-pull recent N days regardless of synced flag, or split pre-race form sync from post-race results sync). VPS code change — Code brief.
- **NEW — operator-side: re-upload `decisions.md`** to the bethub-rebuild Project knowledge base (DR-033 added). `data_sources.md` + catalogue are on-demand disk references; upload optional, not required for session-open.
- **Brief 2 (manual entry)** — now UNBLOCKED on the operational path: win/lose settles off Betfair, place refunds are a manual flag (DR-033). The placings backfill is analytics, not a brief-2 blocker. Re-scope/draft.
- **Carried:** bet-mutation audit log brief (after brief 2); bets-feed robustness guard (into brief 2); launcher brief (F9/F10 + rebuild-if-source-newer); brief 3 free-bet credit-in; dark theme (parked); full parking lot per `current_state.md`.

## Open items out (closed / resolved S174)

- **Finish-position gap root cause — DIAGNOSED.** One-shot-before-results nightly sync from the March 2 rework. ✓
- **Live-settlement exposure question — RESOLVED.** Betfair-only; the gap never touched it. ✓
- **Data-source role confusion — RESOLVED + LOCKED.** DR-033 + `data_sources.md`. ✓
- **"Why did the placings stop / what does the Racing API hold" — ANSWERED + DOCUMENTED.** Diagnosis + field catalogue. ✓
- **Racing API keep-or-cancel — resolved toward KEEP.** The AU add-on is the placings/enrichment feed; cancelling cuts exactly that. (Formal close of the parked question — operator may still elect otherwise.)

## Session close state

- **Rebuild root:** 3 new files — `data_sources.md`, `racing_api_field_catalogue.md` (generated), `gen_racing_api_catalogue.py` (generator). `decisions.md` +DR-033 (now 1310 lines). Clean, no phantom files.
- **`current_state.md`:** rotated to S174 close (19:22 ACST); Where-we-are = the diagnosis + the role lock; What's-next = backfill + nightly-fix + brief 2 re-scope.
- **`v3_build_picture.md`:** Interface-refinement stream moved (brief 2 was `blocked-on place-result source` → unblocked: operational path resolved via DR-033, placings backfill is analytics-only); updated + timestamp bumped.
- **`standing_instructions.md`:** untouched (no edits this session).
- **`.close_out_backups/`:** `SESSION_175_opening_prompt.md` written; stale `SESSION_174_opening_prompt.md` removed.
- **Operator-side action flagged:** re-upload `decisions.md` to the Project knowledge base.

## Forward routing (confirmed with operator)

Operator said "Close it up" after accepting the close framing — carry the two operational follow-ups forward, then back to the brief sequence toward cutover. Forward routing confirmed.

**S175 — operator's choice at open, two ready strands (recommendation: keep cutover momentum):**

1. **Resume brief 2 (manual entry)** — now unblocked. Win/lose settles off Betfair; place refunds are a manual flag; the placings gap is analytics, not a brief-2 blocker. Re-scope/draft toward cutover. *(Recommended primary — protects cutover momentum.)*
2. **Racing-API backfill + nightly-fix** — a Code brief (and/or controlled backfill run) to recover the Mar–Jun placings and stop the gap reopening. Can run in parallel/out-of-session; not cutover-blocking.

Racing-API cancellation stays KEEP (the AU add-on is the placings/enrichment feed). DR-027/028 re-read trigger stands for any future move of place-settlement off manual, and for the nightly-fix Code brief (cross-DB write path).
