# Current state
**Last updated:** 2026-06-29 14:20 ACST (Session 197 close)

**Timezone:** DR-021 standard applies — Adelaide anchors, no
overrides active.

---

## Where we are

**S197 auto-triaged the S196 trickle fix (clean, but it exposed the
real blocker), commissioned + triaged a read-only diagnosis, and
landed a clock-stop. Net: the placings clock is STOPPED and the
surgical fix is fully scoped — the fix itself is S198's job.**

**The trickle fix was faithful** (built to spec, bet-safe, scope
held, unjam mechanism proven) **but exposed F1:** the Racing API
holds the placings, yet `sync_day()` isn't persisting them. And
**F2:** the now-unjammed strike logic would have retired
*recoverable* dates that only *look* resultless.

**Phase 0 — clock STOPPED.** Code landed a two-line guard
(`BACKLOG_FREEZE_RETIRE=True`) in the trickle anchor: dates still
accrue strikes but can never be retired/dropped while the bug is
open. Triple-verified (one live pass: `retired=[]`, selector held,
sidecar honest +1). Recoverable history is now safe; the freeze
flips off after the fix proves out and struck dates self-clear on
the first real fill.

**Phase 1 — the blocker is TWO bugs.**
- **RC-1 (dominant):** the oldest-first walk burns the daily
  Racing-API budget on the near-done early-March dates (stuck on
  genuine ~8% residue), so the recoverable tail (03-15→) is reached
  only after budget is spent — empty runner payloads, `upsert_runner`
  never reached, date mis-classed resultless. For the majority
  (Townsville, Swan Hill) the runner keys already match the API; the
  only thing missing is a budgeted fetch reaching the writer.
- **RC-2 (narrower, corrupting):** where the Betfair/live-capture
  path pre-filled a row with a *different* field under the same
  `N:<number>` keys (Dubbo: 6/8 different horses), a successful sync
  would COALESCE-overwrite the wrong horse. Latent only because RC-1
  starves the payload — fix RC-1 alone and this class corrupts.

**Fill-rate readout** (operator requirement, corrected): 20.0%
thoroughbred filled window-total since 2026-03-01; March is **54.4%**
(prior 21% was a blended all-runner figure); the big unfilled chunk
is **recoverable-but-blocked**, not abandoned.

## What's next

**S198 primary — AUTO-DRAFT the surgical sync-path fix brief
straight off the open ritual, NO confirmation gate** (operator
directive). Draft shape (diagnosis §6): **RC-2 guard first**
(reconcile API runners by horse identity, not saddlecloth number;
punctuation/venue-drift-robust per F-c) **then RC-1 fetch fix** (pace
`sync_day`'s per-meet calls; class empty "Results" payloads as
transient/no-strike; fix the starvation so the tail gets budget).
**Schema: none.** After the fix proves out, flip
`BACKLOG_FREEZE_RETIRE=False` → struck dates self-clear, **and
recovery begins** (the operator's "start the data recovery"
milestone).

Draft disciplines: **ground against live code first** (needs SSH key
loaded) before naming anchors; **walk section-by-section** — this is
the sensitive write-path with a real corruption risk, not a
lock-on-sight brief. Begin drafting on open without waiting for a go.
After lock, provide the Code prompt.

**Then, in order (pre-cutover queue):**
1. **Recovery run** once the fix proves out.
2. **Launcher capture-data provisioning** — capture.db link +
   carried F9/F10/F12 + rebuild-if-source-newer.
3. **Cash-modal back-stake blank** — pre-cutover must-fix (small
   frontend).
4. **Settlement-worker brief** — live caller for
   `run_settlement_pass`; deploy-before-settle IOU + manual-match-to-
   lay. Highest-risk surface; its own bet-safety framing.
5. **Promo-seed item** — seeds the live promo catalogue (also
   restores the empty race-page promo buttons).
6. **W16 cutover scoping.**

## Required reads for Session 198

In order:
1. `current_state.md` (this file).
2. `standing_instructions.md` — in full per Cat 2. (KB re-upload
   still pending.)
3. `project_context.md` — orientation primer.
4. `sessions/SESSION_197.md` — the S197 record.

Reference-only — read on demand (and the fix brief draws on these):
- `placings_landing_diagnosis_report.md` — RC-1/RC-2 root cause +
  the §6 proposed fix the S198 brief commissions. **Primary source
  for the draft.**
- `placings_landing_diagnosis_brief.md` — the diagnosis contract
  (the no-touch list, the Phase-0 guard now live).
- `placings_trickle_fix_report.md` / `placings_trickle_fix_brief.md`
  — the trickle fix + F1–F4 history.
- `data_sources.md` / `decisions.md` DR-033 — placings analytical,
  settlement Betfair-only.

## Pending operator-side actions

**Between S197 → S198:**
- **`ssh-add` the VPS key next session** so Chat can ground the fix
  brief against the live sync code. (SSH-from-Chat failed this
  session — key not loaded.)
- **Run the Code session** against the surgical fix brief once S198
  drafts + locks it (prompt will be provided).
- **Re-upload `decisions.md`** to the bethub-rebuild Project KB
  (S191/S180 amendments; carryover).
- **Re-upload `standing_instructions.md`** to the Project KB (S189
  §4; carryover).
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** running; jump-start-only to retirement.

**Carried (parking-lot):** Deploy-before-settle / IOU free-bet credit
(settlement-worker). RC-1 follow-through note: the Phase-0 freeze
keeps early dates in the selector forever, so the RC-1 starvation fix
(advance past genuine residue) is what ultimately frees budget for
the tail (diagnosis §6.3 / F-d). Duplicate/unstable meet-ID question
(F-b: noise on a shared row, not the blocker — observe-only).
`venue_normalised` drift (F-c: live hazard for any name-based fix).
Older-month (~Nov–Feb) finish-position residual top-up. Finding-1
follow-up (post-cutover). Accounts-screen enhancement. Structural
anti-recurrence CI guard. Hedge-link on manual entry;
bet-mutation-log viewer; Log Past Bet soft-books-only picker; BetLog
promo-events delete-check; `presets.ts` dead-code; free-bet config
cosmetics; quick-lay modal error-reason; streaming-path F1 gap;
200-market over-subscription at startup; audit-sink durability (F8) +
place-then-commit window (F11); multi-leg audit snapshot (F5);
streaming hardening (F3/F5/F4); partial free-bet draw-down; in-app
catalogue-management UI; shared canonical account-ref type
(post-cutover, DR-030); Piece B (post-cutover).

## Open items

Pointer-only — full detail in `sessions/SESSION_197.md`.

**New / changed in S197:**
- **Diagnosis done → surgical fix scoped** (RC-2 then RC-1, no
  schema change). The fix brief is S198's auto-draft deliverable.
- **Placings clock STOPPED** (`BACKLOG_FREEZE_RETIRE=True` landed +
  verified). Freeze flips off after the fix proves out.
- **Daily trickle check-up cadence → SUPERSEDED** — moot until the
  fix lands (no climb until RC-1 fixed). Don't kick off the daily
  watch at S198; the fix is the path.

**Carried to S198:**
- Surgical sync-path fix brief (auto-draft on open) → then recovery.
- Launcher capture-data provisioning.
- Cash-modal back-stake blank.
- Settlement-worker brief.
- Promo-seed item.
- W16 cutover scoping.
- Parking-lot items (see above).

**Closed / done in S197:**
- Auto-triage of `placings_trickle_fix_report.md` — DONE. ✅
- Diagnosis commissioned + triaged; clock stopped. ✅

**Carry-forward sensitivity flags:**
- **Next (fix) brief is SENSITIVE** — live capture write-path
  (`sync_day`, `_sync_single_runner`, `storage/database.py`), real
  data-corruption risk (RC-2). Ground + section-by-section.
- **Bet-safety this session — CLEAN.** No money path; no code touched
  in Chat (the one VPS edit was Code's Phase-0 guard, capture-side,
  DR-033).
- **capture.db / DB reads are read-only** (mode=ro, never copy).
- **v2 is never modified.**
- **Cat 1 silent-open-ritual leak recurred at S197 open** (step
  headers in operator-facing text) — the next open watches for it.

**Carry-forward (unpromoted standing rules — operator-confirmed
S152):**
- Cluster/platform lists: no periodic review; research an unknown
  book at registration time.
- Future tool enhancement: bet-time warning when about to run hard on
  two books sharing an owner or risk engine.

## Active governing decision records

- **DR-021** (timestamp anchoring, Adelaide local) — every open +
  close.
- **DR-019** (derived state on read).
- **DR-022** (book / account / account-at-book vocab).
- **DR-025** (hedge-state classification / ops-log audit trail).
- **DR-026** (at-log market snapshot — narrow cross-DB durability
  exception).
- **DR-027 / DR-028** (two-database architecture + single integration
  boundary). Re-read trigger at W16 cutover scoping.
- **DR-029** (data-layer fit-for-purpose) — closed (S78); amended
  S191.
- **DR-030** (v3 repo layout / module boundaries).
- **DR-031** (v3 tech stack; SQLite WAL).
- **DR-032** (Betfair canonical reference layer) — amended S180.
- **DR-033** (data-source roles) — placings analytical, settlement
  Betfair-only; the controlling decision behind the placings work's
  analytical-only framing AND the fix's bet-safe-by-construction
  status.
- **DB read discipline** (mode=ro, never copy, `start_process`
  Python).

Full DR list in `decisions.md`.
