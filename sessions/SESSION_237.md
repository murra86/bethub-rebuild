# SESSION 237 — the burst-flow auto-build landed, then a four-day arc: race-page + WHOLE-APP clean pass (operator-led UX loop), settled-bet edits unlocked, and the VPS saga — disk-full found and fixed, then the Racing-API rate-limit change AND a months-old upsert bug root-caused and fixed on the VPS, three outage days re-synced, VPS health checks made standing

**Opened:** 2026-07-09 18:44 ACST ("Open session 237" while the S236-close runner was mid-build; session held rather than duplicating the auto first action).
**Closed:** 2026-07-12 10:02 ACST (multi-day session per Cat 2 — paused/resumed across 9→12 Jul; operator travelling, Port Lincoln from 11 Jul).
**Tool routing:** single Claude Code session end-to-end; headless runner delivered the first action (burst-flow build) independently.
**Bet-safety:** NO bets, NO Betfair placements, NO money-path code edits by Claude. `place_lay`, settlement resolvers, reconciliation, credit maths untouched across every commit. The one money-adjacent change (settled-bet edit fence, operator-directed) is store/router edit-scope only, P&L stays derive-on-read (DR-019). VPS work was capture-side (analytical line) only.
**Governing DRs:** DR-021 (Adelaide anchors); DR-019 (derive-on-read — the settled-edit unlock leans on it); DR-028 (cited and respected twice: picker latency fix stores nothing, day-catalogue is an on-demand read through the single vps_client boundary; no new integration points); DR-030 (day-catalogue endpoint is a thin composition); DR-034 (fragment collapse — central to the VPS upsert-bug diagnosis).

---

## Arc 1 — burst-flow redesign (runner-built, S236's confirmed AUTO action)
Runner built it unattended in ~23 min: §1 selection stack (person/book chips with balances, day-frozen activity order) + §2 single-pass ⚡ lay→back (modal becomes the back-log card, preselected context, skip never blocks) + 422 plain wording. `7885535`→`402e5bd`, suites 1441/183, dist swapped app-down. Report `burst_flow_build_report.md`. Operator triage closed its one question: insurance-armed ⚡ correctly defaults to free-bet (operator never hedges insurance — commission eats the EV); no change.

## Arc 2 — race-page clean pass (mock-first UX loop, operator-approved)
Operator: "make it clean." Review found the app running three visual languages; race page recut in the Money-page token system: one warm sheet promoted app-wide (`index.css` vars), navy BACK / rose LAY (Betfair convention), one green/red/amber each with one job, mono figures, 10 runners + 12 races dense, race-type filters (Thoro default; colour-coded T/H/G letters), label-left top-bar grid. Mock `race_page_clean_mock.html` (v2 after operator feedback: denser, filters, tighter bar). `431890d`, 186 frontend tests, dist swapped app-down (operator closed it on request).

## Arc 3 — whole-app clean pass + settled-bet edits (operator-directed)
Full-app UX review (subagent inventory) → all-pages mock (`app_pages_clean_mock.html`, clickable nav) → approved → built same session (`6d35480`):
- **Settled soft-book bets now editable** (account/book/stake/odds) — store fence loosened to terminal states (provisional stays blocked — worker's lane); settled BETFAIR bets refused at the router (exchange's own record); promo-attached moves still refused; amber promo-credit caution in the UI (credits do NOT recompute). Grounded on DR-019 before building: everything re-derives, nothing stored goes stale.
- BetLog: chip filters (person/book/state/free-cash; UUID aab dropdown deleted), side tags, status colours, ALL browser confirms → inline amber strips (settle/delete/Placed?/reverse/archive — Accounts archive had NO confirm at all).
- Accounts (chips + registered-ticked-faded registration pick), LogPastBet (person/book/side/outcome chips), Manual queue + bet card (void purple retired), Burst review (onto tokens, coloured settle buttons), Health, nav active-state.
Suites 1443/188 (settled-edit paths re-pinned both sides). Report `app_clean_pass_report.md`.

## Arc 4 — Betfair auth cool-off incident (11 Jul, Port Lincoln)
Live prices dead on the operator's travel morning: app started before hotel wifi resolved DNS → one failed login → 30-min cool-off (the S222 throttle working as designed but blunt). Network was fine; app relaunched (single-instance lock lesson: Claude's background launch held the launcher lock → operator's double-click "Process completed"; killed Claude's copy, operator relaunched normally). **Named for triage: the throttle should distinguish "no internet" from "Betfair refused" and retry sooner; the launcher's already-running refusal needs a louder message.**

## Arc 5 — the VPS saga (11–12 Jul) — the analytical line's worst week, fully closed
1. **Disk 100% full since 8 Jul**: nightly backup kept full 4GB copies of capture.db and pruned only AFTER a successful copy — first disk-full failure stopped all future pruning; 17 copies × 4GB filled 48GB; runner capture silently dead 3 days; Log Past Bet picker empty. Fixed: garbage + stale backups cleared (100%→35%), `scripts/backup_db.sh` rewritten (prune-FIRST, atomic tmp+mv, space guard, keep-2), proven live.
2. **`ops/vps_health` built + standing** (operator-directed: "schedule health checks of the VPS in future check ins"): 7 read-only checks (~15s) at every session open — SSH, disk (70/85), collector, db freshness, backup rotation, overnight-sweep progress, tunnel/runner coverage. Step 5b of the session-open skill; Cat 2 standing instruction; 14 unit tests.
3. **Picker latency** (operator-directed): the cascade re-fetched the ±1-day window (3 sequential tunnel GETs) at EVERY step. Fixed: window GETs parallelised + one `day-catalogue` read per date (DR-028 respected — nothing stored), venue/race picks now instant (live-measured 1.7s/step → 1.4s once). `048fcf0`, suites 1451/188.
4. **Overnight sweep dead since ~29 Jun — TWO root causes** (first theory "subscription lapsed" was WRONG — operator pushed back with proof; the 401s were plan-scope, this account uses `/australia/*` add-on endpoints):
   - **Provider rate limits tightened ~29 Jun**: old pacing (0.2–1s; recent pass UNPACED) got every fetch degraded to empty-200s. Fixed on VPS: BACKLOG_MIN_DELAY 0.2→5.0, recent pass paced per-meet, 429 Retry-After retry. 5s/meet empirically clean.
   - **`cursor.lastrowid` upsert bug (`storage/database.py`), live since ~March**: after ON CONFLICT DO UPDATE, sqlite3 reports the connection's last INSERTED rowid (a runners.id) → bulk syncs attached runners to phantom/wrong races (2,983 dangling rows; July horses glued onto an April race; the 38k positions deficit). Single-race writes worked (fresh connection → falsy lastrowid → correct SELECT fallback) — the maddening bulk-vs-single asymmetry that cracked it. Fixed: both upserts ALWAYS resolve ids by natural key; garbage deleted; racing-capture + racing-api restarted on fixed code.
5. **Outage days re-synced clean on fixed code**: 11 Jul 111 loggable races (was 55), 10 Jul 40 (was 0), 9 Jul 38 (was 1). Caveats: thoroughbred only (greys/harness in the dead window are unrecoverable — Betfair-live only; operator can name any missing dog bets for scripted logging); one 10-Jul meet 404s provider-side (sweep retries).
6. **Historic corruption heals automatically**: the fixed sweep re-syncing old dates COALESCE-overwrites the mis-filed values; deficit burn-down visible in the health check's sweep line.

## Standing-instruction adherence
Cat 1 brevity strained by the VPS narrative days — plain-language framing held. Cat 3 empirical verification carried the session: every VPS theory tested before acting (the wrong subscription theory caught by the operator's evidence — logged as the lesson: verify provider-side state against the OPERATOR's account facts, not just API responses); S223 one-pass sweep honoured (upsert bug: counted, classed, batched fix + cleanup + services + re-sync in one arc). Cat 5 make-the-call throughout; operator calls surfaced (backup deletion, settled-edit unlock, sweep-check action). S227 git autonomy: 6 commits pushed, green each. DR-028 cited by number at both touch points, discipline held (nothing stored, single boundary).

## Open items in (new)
- **S238 FIRST ACTION (operator-flagged): verify tonight's 05:34 sweep ran clean on fixed code** — health check sweep line (walled=0, net>0 expected) + deficit burn-down + picker serves 9–11 Jul; report; if walled again, re-diagnose on the VPS.
- Betfair login throttle: distinguish no-internet from refused-login (Arc 4); launcher already-running message.
- VPS disk tripwire in the v3 fault banner (durable build; health check is the interim).
- Historic capture corruption burn-down (watch via sweep line; full audit only if burn-down stalls).
- Operator: re-upload `standing_instructions.md` + `skills/bethub-session-open.zip` to the Project KB (both changed this session).
- Carried: dist-gate rule refinement; sports-bet accounting decision (PARKED); movement residuals R1–R4; S1 leg staleness; cycle-demotion build.

## Session close state
bethub-v3 HEAD `9de9c64` = origin/main, tree clean, suites 1455/188, dist current with HEAD (frontend unchanged since the 048fcf0 swap; ops-only commits after). VPS: disk 35%, both services healthy on fixed code, backups keep-2 proven, three outage days re-synced. v3 app: down (operator closed it 11 Jul for the dist swap; relaunch picks up everything). Rebuild root: this record; mocks ×3; reports (burst_flow_build, app_clean_pass); UX-lead instruction FOLDED into standing_instructions.md (proposal file retained as substrate); v3_build_picture.md + current_state.md updated at this close.

## Forward routing (operator-confirmed: "flag that as an action")
**S238 FIRST ACTION — AUTO (read-only, runner-safe):** run `ops/vps_health`, read the overnight sweep line and the backlog burn-down (`backlog_recovery.log` tail), verify the Log Past Bet picker serves 2026-07-09/10/11 through the day-catalogue endpoint if the app is up (else db-side counts), and report plainly. HOLD everything else: no builds, no VPS edits — if the sweep walled again, diagnose read-only and surface findings for the operator.
