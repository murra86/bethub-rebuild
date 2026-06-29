# Session 177 — Bet-mutation audit-log build report triaged clean (no surgical fix); F2 brief-flaw deviation surfaced

**Opened:** 2026-06-23 14:35 ACST
**Closed:** 2026-06-23 14:49 ACST
**Duration:** ~14m, single calendar day. Same-workday continuation
of S176 (closed 14:23 ACST; S177 opened 14:35, 12 min later).
**Tool routing:** Claude Chat (triage) + Desktop Commander
(governance reads/writes; the build report read from disk). One
out-of-session Code build (the bet-mutation audit-log brief) ran
between S176 close and S177 open; its report was the triage target.
No VPS access.
**Governing DRs invoked:** DR-021 (anchors), DR-030 (module
layering — the audit-log spine), DR-032 (Betfair canonical /
bet-axis ids), DR-019 (derived P&L on read — the F3 editable-field
note), DR-025 (ops-log bet-axis precedent), DR-027/028 (which DB the
audit writes land in — the F2 co-location point: same operational
store as the bets).

---

## Anchor

- Open: `2026-06-23 14:35 ACST` (session-open ritual; same-workday
  continuation of S176's 14:23 close).
- Close: `TZ="Australia/Adelaide" date` → `2026-06-23 14:49 ACST`.

## Pre-flight checks

Open ritual ran clean: drift-check passed (current_state ↔
SESSION_176 ↔ v3_build_picture all matched the 14:23 S176 close);
`.close_out_backups/` held only the S177 opening prompt; rebuild
root clean. Required reads completed in order (current_state,
standing_instructions in full, project_context, SESSION_176, the
locked audit-log brief). At open the audit-log build report did not
yet exist in `interface_triage/` — surfaced to the operator as the
one routing fact (triage can't run without the report). The operator
then pasted Code's completion output, confirming the build had run,
and the report was read from disk.

## Session shape

A single tight arc: triage Code's bet-mutation audit-log build
report. The session opened, surfaced the report-not-yet-present
routing fact (the same pattern as the S176 open with Brief 2), the
operator pasted Code's completion output, and the report
(`bet_mutation_audit_log_report.md`, 414 lines) was read from disk
and inventory-triaged. Clean landing — no surgical fix, no blocker.
Operator then called the close.

## What was delivered

1. **Bet-mutation audit-log build report triaged — clean landing,
   no fix.** Read `bet_mutation_audit_log_report.md` (414 lines) from
   disk. All six §5 pieces built (domain types, schema/table,
   append-only repository, store adapter, three decoupled
   after-commit endpoint hooks, write-path spot-check). Tests
   1128→1158 (+30), 0 regressions. Live seams byte-identical by
   SHA-256: `clients/betfair_client/v1/settlement.py`,
   `workflows/bet_entry/v1/settlement.py`,
   `clients/betfair_client/v1/placement.py`; reconciliation worker
   not opened; bet-write transaction unchanged. lint-imports 5/5
   contracts kept (DR-030 layering holds). Dirty tree clean — no
   tracked file touched; the four intended additions plus the
   already-untracked `bets.py` edits + new tests.

2. **Bet-safety guarantee proven (the load-bearing thing).** The §9
   hard limit — an audit write can never roll back, block, or alter a
   real bet write — is proven three ways: the emit runs after the bet
   write commits, on its own separate connection (own transaction),
   and is caught-and-logged. Three decoupling tests inject a raising
   audit factory; edit / delete / create all still succeed and
   persist. Delete-survives-deletion proven at both store and
   endpoint layers (the audit row reads back from a DB with no `bets`
   table; the trail is readable after the bet row is gone).
   Append-only proven (source-scan + reflection: no UPDATE/DELETE SQL
   or methods). No FK to `bets` — `bet_id` stored as a value.

3. **F2 surfaced to the operator — the locked brief had a flaw, Code
   caught and reverted it.** The brief's §5.5 directed wiring the
   audit adapter via `composition.py` to a fixed DB path. Code found
   that harmful: a composition-fixed audit path diverges from the
   per-request injected bet storage, so audit writes would land in
   the *wrong* DB — and potentially pollute the production
   `data/bethub.db` during test runs (observed directly: happy-path
   tests read zero rows because writes went to the production path).
   Code reverted (`composition.py` byte-identical to session start —
   no net edit) and derives the audit connection from the injected
   bet storage's own path, co-locating the trail with the bets per
   §4. A deliberate deviation from a locked brief, correctly made;
   surfaced to the operator in plain language. No operator call
   needed (Code made the right software call per Cat 5); the live
   store was never actually at risk.

4. **Inventory triage of all 8 findings, classified by operational
   impact.** Surfaced: F2 (above). Offered as light notes, not
   dumped: **F3** — the editable field set is `strategy_tag` (always)
   + `requested_stake` / `matched_stake` / `matched_price`
   (PENDING-only); settlement-driving fields are structurally
   un-editable; the audit captures full before/after snapshots so the
   change is always reconstructable. **F5** — multi-leg bets capture
   only the primary leg's Betfair ids (snapshot reads `legs[0]`);
   near-zero impact today (racing is single-leg; Strategy 3 / SGM not
   live); parking-lot. Handled silently as Claude's territory: **F1**
   (the pre-read governance docs `architecture.md` / `decisions.md` /
   `audit_landscape.md` don't exist in the `bethub-v3` tree — they
   live in the rebuild governance folder, which Code wasn't scoped
   to; Code recovered fully from the code templates; a
   brief-drafting artifact to fix next time, not a defect), **F4**
   (snapshot fields primitive-typed by design — robust to bet-domain
   enum drift), **F6** (no `parent_event_id` — intentional
   brief-directed narrowing; supersession is the only relationship
   this log needs), **F7** (one read-only pre-read per edit/delete to
   capture the before/last-known snapshot, guarded so it can't affect
   the write — covered by the decoupling proof), **F8**
   (`occurred_at == recorded_at` for hand-touches; the bet's own
   `placed_at`, possibly days earlier for a Log Past Bet create, is
   preserved separately in the snapshot — no information lost).

**Triage verdict:** clean landing, no surgical fix, no blocker.
Forward route = brief 3 (free-bet credit-in). Operator called close.

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open 14:35 + close 14:49 ACST. ✓
- **Silent session-open (Cat 1):** steps 1–5 silent; the one
  surfaced item (report-not-yet-present) was a genuine routing fact,
  not narration. ✓
- **Inventory-first triage on a long report (Cat 1):** the 414-line
  report inventoried, all 8 findings classified by operational
  impact; only F2 surfaced as operator-facing, F3/F5 offered as light
  notes, F1/F4/F6/F7/F8 handled silently. ✓
- **Empirical verification before claims (Cat 3):** triage from the
  report read off disk, not memory. ✓
- **Make-the-call / don't punt (Cat 5):** F2 was Code's software call
  (which DB seam) — confirmed correct, not punted back to the
  operator. ✓
- **Dev-lead calls not over-surfaced (Cat 1/S163):** only F2
  (deviation from a locked brief + data-integrity angle) surfaced;
  the consequence-free technical findings handled silently. ✓
- **Plain-language / brevity / lead-with-the-call (Cat 1):** verdict
  led; F2 in plain real-world language. ✓
- **`create_file` banned / verify every write (Cat 3):** all close
  writes via `Desktop Commander:write_file` / `edit_block`; verified
  at Step 11. ✓
- **Code session prompt at hand-off (Cat 2):** N/A — no new Code
  brief handed off this session (next session drafts brief 3).
- No standing instruction authored or edited this session → no
  `standing_instructions.md` sweep.

## Open items

Pointer-only — full live list in `current_state.md`.

## Open items out (closed / resolved S177)

- **Run the Code session for the audit-log brief** (operator-side) —
  DONE: operator ran it out-of-session; the report landed. ✅
- **Triage Code's `bet_mutation_audit_log_report.md`** — DONE: clean
  landing, no surgical fix, no blocker; bet-safety proven; F2
  deviation surfaced and confirmed correct. ✅

## New items in (S177)

- **F5 parking-lot** — multi-leg bets capture only the primary leg's
  Betfair ids in the audit snapshot. Near-zero impact today (racing
  single-leg; Strategy 3 / SGM not live). Revisit only if SGM goes
  live and a multi-leg hand-edit/delete trail needs the non-primary
  leg ids.
- **F1 note for brief-drafting** — when a brief scopes Code to the
  `bethub-v3` repo, don't name rebuild-folder governance docs
  (`architecture.md`, `decisions.md`, `audit_landscape.md`) as
  pre-reads without a full path; they aren't in the v3 tree. Minor
  brief-hygiene item; Code recovered from the code templates.

## Session close state

- **Rebuild root:** clean, no new files at root. No phantom files.
- **`interface_triage/`:** 1 new file —
  `bet_mutation_audit_log_report.md` (414 lines, Code's build report;
  the S177 triage target, landed from the out-of-session Code run).
- **`current_state.md`:** rotated to S177 close (14:49 ACST);
  Where-we-are = audit-log build triaged clean; What's-next = S178
  drafts brief 3 (free-bet credit-in).
- **`v3_build_picture.md`:** Interface-refinement stream
  next-milestone moved (audit-log brief "LOCKED + handed to Code;
  awaiting build report" → "TRIAGED CLEAN — built, green, seams
  byte-identical, bet-safety proven; F2 brief-flaw caught + reverted
  by Code"); updated + timestamp bumped.
- **`standing_instructions.md`:** untouched (no edits this session).
- **`.close_out_backups/`:** `SESSION_178_opening_prompt.md` written;
  stale `SESSION_177_opening_prompt.md` removed.
- **Operator-side actions flagged:** live-validate "Log Past Bet" in
  the launched app (carry from the Brief 2 triage — still pending).
  The audit log has no viewer in v1, so nothing to validate there;
  it captures silently from now on.

## Forward routing (confirmed with operator)

Operator triaged the audit-log build clean and said to close and
**start fresh next session**. **S178 drafts brief 3 — free-bet
credit-in** (the S168 design; the promo "Placed?" / free-bet-credit
write lands in BetLog's inert scaffold). Load-bearing carry (LOCKED
S175 / Brief 2 §10): brief 3 must wire its promo-trigger /
free-bet-credit question to BOTH the live "Placed?" hook AND the Log
Past Bet manual settle-at-entry screen — one settlement-time
question, both entry paths. The `bethub-brief-drafting` skill fires
when that drafting starts. Post-brief-3 sequence: **launcher brief**
(F9 login back-off to disk + F10 port override + F12 +
rebuild-if-source-newer) → **W16 cutover** scoping. Separately on the
roster (parallel, not cutover-blocking): **Racing-API placings
backfill + nightly results-sync fix** — own Code brief, carrying the
DR-027/028 re-read trigger (VPS-side write). Forward routing
confirmed.
