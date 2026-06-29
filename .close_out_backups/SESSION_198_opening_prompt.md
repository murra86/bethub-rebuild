# Session 198 — opening prompt

**Drafted:** 2026-06-29 14:20 ACST (S197 close). Paste into a fresh
chat in the `bethub-rebuild` Project to open Session 198.

---

Open the session: re-run the timestamp anchor (`TZ="Australia/
Adelaide" date "+%Y-%m-%d %H:%M %Z"`) per DR-021, then the
pre-flight directory listing of the rebuild folder root after the
named reads. Run the open ritual silently (no step-header narration
in operator-facing text — this leaked S193/195/196/197; watch it).

**Calendar-calibrated open:** compare current ACST against this
close (2026-06-29 14:20). Same-workday → tight recap; new-workday →
longer.

**Drift-check:** (a) `current_state.md` last-updated = 2026-06-29
14:20; (b) `sessions/SESSION_197.md` exists + non-empty; (c)
`v3_build_picture.md` untouched at S197 close (no stream moved) —
its stamp predating this close is correct, not drift.

**Primary deliverable — AUTO-DRAFT the surgical sync-path fix brief
straight off the open ritual, NO confirmation gate** (operator
directive S197). Begin drafting on open without waiting for a go.
Draft shape (from `placings_landing_diagnosis_report.md` §6): **RC-2
guard first** — reconcile API runners by horse identity, not
saddlecloth number, so recovering the tail can't COALESCE-overwrite
cross-sourced Betfair-path rows (punctuation/venue-drift-robust per
F-c) — **then RC-1 fetch fix** — pace `sync_day`'s per-meet calls;
class empty "Results" payloads as transient/no-strike; fix the
starvation so the recoverable tail gets live budget. **Schema:
none.** After it proves out, flip `BACKLOG_FREEZE_RETIRE=False` →
struck dates self-clear and **recovery begins** (the operator's
"start the data recovery" milestone).

**Draft disciplines (load-bearing):** this is the SENSITIVE one — it
edits the live capture write-path (`sync_day`,
`_sync_single_runner`, `storage/database.py`) with a real
data-corruption risk (RC-2). (1) **Ground against live code first** —
the operator should `ssh-add` the VPS key; read the actual functions
before naming anchors (SSH-from-Chat failed S197, key not loaded).
(2) **Walk the brief section-by-section** — not a lock-on-sight
brief. (3) Bet-safety framing explicit: write-path, but capture-side
analytical (DR-033), no v3/settlement/money/Betfair-scraper. (4)
After lock, **provide the ready-to-paste Code prompt** (Cat 2). Use
the `bethub-brief-drafting` skill.

**Required reads (in order):**
1. `current_state.md`
2. `standing_instructions.md` — in full (Cat 2). KB re-upload
   pending.
3. `project_context.md`
4. `sessions/SESSION_197.md`

**Reference-only (the draft draws on these):**
- `placings_landing_diagnosis_report.md` — **primary source** for
  the draft (RC-1/RC-2 root cause + §6 proposed fix).
- `placings_landing_diagnosis_brief.md` — the diagnosis contract +
  the live Phase-0 guard.
- `placings_trickle_fix_report.md` — F1–F4 history.
- `decisions.md` DR-033 — placings analytical, settlement
  Betfair-only.

**Pre-flight verification:** confirm `placings_landing_diagnosis_
report.md` present at root; confirm `.close_out_backups/` holds only
this prompt.

**Pending operator-side actions:**
- `ssh-add` the VPS key (so Chat can ground the brief).
- Run the Code session against the fix brief once drafted + locked.
- Re-upload `decisions.md` + `standing_instructions.md` to the
  Project KB (carryover).
- Manage any live unmatched lays (S164).
- v2: jump-start-only.

**Open items in:** surgical fix brief (auto-draft) → recovery;
launcher capture-data provisioning; cash-modal back-stake blank;
settlement-worker brief; promo-seed; W16 cutover; parking-lot.

**Open items out (S197):** auto-triage of the trickle-fix report;
diagnosis commissioned + triaged; clock stopped. Daily trickle
check-up cadence SUPERSEDED (moot until the fix lands — don't kick it
off).

**Filesystem note:** Desktop Commander is the default tool;
`bash_tool` is non-functional. Multi-line Python → write to `/tmp`
then `start_process`, not REPL paste. Live DB reads `mode=ro`, never
copy. Verify every governance-artefact write via `read_file`/
`list_directory`.

**Expected state of rebuild folder root at open:** as S197 close
left it — `placings_landing_diagnosis_brief.md` +
`placings_landing_diagnosis_report.md` present;
`v3_build_picture.md` untouched; no phantom files.

**Governing DRs:** DR-021 (always); DR-033 (the bet-safety ground
for the fix); DR-027/028 (capture-side boundary); re-read DR-027/028
at W16 cutover scoping.
