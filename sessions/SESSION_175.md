# Session 175 — Brief 2 (after-the-fact manual entry) drafted, locked, handed to Code

**Opened:** 2026-06-22 19:38 ACST
**Closed:** 2026-06-23 12:50 ACST
**Duration:** multi-calendar-day (day-rollover during the operator-away gap while the Code read-and-confirm checkpoint ran out-of-session). Active Chat work ~modest; single arc.
**Tool routing:** Claude Chat (planning / brief-drafting / triage) + Desktop Commander (governance reads/writes; read-only grounding of the live v3 repo). No VPS access this session — all grounding was local v3 repo reads. One out-of-session Code checkpoint (read-and-confirm only; no edits yet).
**Governing DRs invoked:** DR-021 (anchors), DR-033 (data-source roles — settle off Betfair, place refunds manual), DR-027/028 (two-database boundary — the new vps_client surface is read-only), DR-019 (derived P&L on read), DR-032 (Betfair canonical reference).

---

## Anchor

- Open: `2026-06-22 19:38 ACST` (session-open ritual; same-workday continuation of S174's 19:22 close).
- Close: `TZ="Australia/Adelaide" date` → `2026-06-23 12:50 ACST`.

## Pre-flight checks

Open ritual ran clean: drift-check passed (current_state ↔ SESSION_174 ↔ v3_build_picture all matched the 19:22 S174 close); `.close_out_backups/` held only the S175 opening prompt; rebuild root clean. Required reads completed in order (current_state, standing_instructions in full, project_context, SESSION_174). One minor flag raised: the `bethub-session-open` skill's expected-file/dir checklist is stale — it does not list `interface_triage/` (legitimate interface-stream brief/report folder), nor the S174-new root files (`data_sources.md`, `racing_api_field_catalogue.md`, `gen_racing_api_catalogue.py`) or `external_api_resources.md`. Skill-maintenance item, no operational impact.

## Session shape

A clean single-arc brief-drafting session. Opened on the operator's choice between the two S175 strands; operator picked **brief 2 (manual entry)** and confirmed the Racing-API backfill + nightly-fix stays on the roster (parallel/out-of-session, not cutover-blocking). The session then ran the brief-drafting ritual end-to-end: grounded the v3 anchors against the live repo, surfaced the one load-bearing finding (a new VPS-read surface is needed), resolved two operator calls, drafted + locked the brief, and handed off the Code prompt. Closed after the out-of-session Code read-and-confirm checkpoint came back faithful and was given the all-clear.

## What was delivered

1. **Brief 2 drafted, locked, on disk.** `interface_triage/manual_entry_build_brief.md` — 486 lines, 11 sections + 6 build sub-sections. A build brief on the BetLog-build pattern. Commissions Code to build after-the-fact manual bet entry end-to-end: a new VPS race-lookup read (§5.1), a create-bet endpoint (§5.2), settle-at-entry (§5.3), the bets-feed robustness guard (§5.4), the "Log Past Bet" screen (§5.5), and a write-path spot-check (§5.6). Operator-signed at close.

2. **The load-bearing grounding finding.** `vps_client/v1` exposes six read surfaces, all keyed on Betfair's own identifiers (event_id, or market_id+selection_id). None take human fields (date/venue/race) and return the Betfair identity. So brief 2 commissions a NEW read surface (cascading lookup → event_id + Win market_id + runner set), a backward-compatible addition per the contract's §10.3 (no version bump), read-only against capture.db. Picker is driven by the store's own values (no free-typed venue → sidesteps the venue-harmonisation gremlin). This is more than "wire the existing design in" — but downstream of it is just wiring.

3. **Two operator calls resolved.** (A) The manual-entry screen lives at its own nav tab labelled **"Log Past Bet"**, not inside BetLog — its own surface per the locked scope. (B) Brief 2 settles **won/lost/void only**; the promo-trigger / free-bet-credit question is built once at settlement in **brief 3** and wired to BOTH entry points (the live "Placed?" hook + this manual screen). No promo flag is added in brief 2 (it would be an orphan — nothing in v3 yet consumes it). Operator's framing: settle via the normal process, ask the promo question at settlement — which IS brief 3's job; brief 2 carries a §10 note that brief 3 must cover the manual path too.

4. **Settle-at-entry confirmed mechanically clean.** `SettlementState` already carries PENDING/SETTLED_WON/SETTLED_LOST/VOIDED and `BetRecord.settlement_state` exists — settle-at-entry is a usage of existing types at write time, no domain-schema edit. Live/near-time auto-settle is untouched (still PENDING → Betfair).

5. **Code read-and-confirm checkpoint — faithful, all-clear given.** Code's out-of-session restatement matched the brief across all six pieces, the hard limits, and the exclusions. It surfaced two correct findings that slightly reduce the work: `EntryPath.MANUAL_LOG` already exists (reuse, don't add) and §5.3 needs no domain-schema edit. Code's dirty-tree question resolved to **Option 1 (Proceed)**: the whole v3 build is coherently uncommitted (HEAD is a near-empty skeleton; domain/bets/__init__.py went empty→full, freshly authored, not a half-finished competing edit), which is the expected dirty substrate the brief anticipated — not the partial-edit-inside-an-anchor collision the stop-rule guards against. Operational git discipline applies (no add/commit/stash/restore/checkout/reset; diff after each edit; status at close unchanged bar intended edits) — same as the S171 BetLog build ran.

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open 19:38 + close 12:50 ACST. ✓
- **Brief-drafting ritual (skill):** job named, anchors grounded empirically (live v3 repo, read-only), shape chosen (build brief / BetLog precedent), drafted end-to-end, calls surfaced, operator-reviewed (operator delegated depth — "you're the dev lead, draft it up, highlights only"), locked on disk + verified. ✓
- **`create_file` banned / verify every write (Cat 3):** all writes via `Desktop Commander:write_file` / `edit_block`; brief verified post-write (line count, header grep, placeholder grep = 0, sha). ✓
- **Empirical verification before editing (Cat 3):** re-read each brief region before each edit_block. ✓
- **Make-the-call / don't punt (Cat 5):** technical shape (new vps_client surface, builder reuse, endpoint, robustness guard) was Claude's call; the two genuine non-technical calls (screen placement, promo-flag timing) surfaced to operator. ✓
- **Dev-lead calls not over-surfaced (Cat 1):** dev-lead choices folded into the brief, not enumerated for review; only the two operator-facing calls surfaced. ✓
- **Plain-language / brevity / lead-with-the-call (Cat 1):** maintained; operator asked for sharper/shorter mid-session and that was applied. ✓
- **Code session prompt at hand-off (Cat 2):** ready-to-paste prompt provided without being asked. ✓
- No standing instruction authored or edited this session → no `standing_instructions.md` sweep.

## Open items

Pointer-only — full live list in `current_state.md`.

## Open items out (closed / resolved S175)

- **Brief 2 (manual entry) drafting** — DONE: drafted, locked (486 lines), operator-signed, Code prompt handed off, Code checkpoint confirmed faithful + all-clear given. ✅
- **decisions.md re-upload** (S174 carry) — DONE (operator confirmed at open). ✅
- **The two brief-2 scope calls** (screen placement; promo-flag timing) — RESOLVED + locked into the brief. ✅

## New items in (S175)

- **Run the Code session for brief 2** (operator-side, out-of-session) — paste the provided prompt; answer the dirty-tree checkpoint with **Option 1 (Proceed)**.
- **Brief 3 must cover the manual settle-at-entry path** — carry-forward note locked in brief 2 §10 (promo-trigger question wired to both entry points).

## Session close state

- **Rebuild root:** 1 new file — `interface_triage/manual_entry_build_brief.md` (486 lines). Clean, no phantom files.
- **`current_state.md`:** rotated to S175 close (12:50 ACST); Where-we-are = brief 2 locked + handed to Code; What's-next = await Code report, then S176 triage.
- **`v3_build_picture.md`:** Interface-refinement stream next-milestone moved (brief 2 was "unblocked, re-scope/draft" → "brief 2 LOCKED + handed to Code; awaiting build report"); updated + timestamp bumped.
- **`standing_instructions.md`:** untouched (no edits this session).
- **`.close_out_backups/`:** `SESSION_176_opening_prompt.md` written; stale `SESSION_175_opening_prompt.md` removed.
- **Operator-side action flagged:** run the Code session (Option 1 on the dirty-tree checkpoint).

## Forward routing (confirmed with operator)

Operator gave the all-clear to Code and said to close out. **S176 triages Code's `manual_entry_build_report.md`** once the operator has run the Code session out-of-session — read the report, surface findings in plain operational language, route to the next brief (bet-mutation audit log) or a §5.x surgical fix if triage surfaces one. If Code's build lands clean, the post-brief-2 sequence is: audit-log brief → brief 3 (free-bet credit-in, covering the manual path per the §10 note) → launcher brief → W16 cutover scoping. The Racing-API placings backfill + nightly-fix stays on the roster as its own Code brief (DR-027/028 re-read trigger — VPS-side write). Forward routing confirmed.
