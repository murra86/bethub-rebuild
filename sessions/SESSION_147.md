# Session 147 — M1 + W17 reports triaged clean; W17.1 brief LOCKED

**Opened:** 2026-06-13 10:21 ACST.
**Closed:** 2026-06-13 10:58 ACST.
**Tool routing:** Claude Chat (report triage + brief drafting +
lock). No code edits. New artefact:
`dr029/w17_racing_pages/w17_1_brief.md` (344 lines, LOCKED).
Code execution prompt handed to operator in-chat at close.
**Governing DRs invoked:** DR-021 (Adelaide anchors), DR-030
(module boundaries — §5.1 workflows layering + lint-imports
gate), DR-031 (tech stack — Alembic adoption CONFIRMED LANDED
via M1; `BETHUB_DB_URL` consistency carried into W17.1 §5.6),
DR-019 (derive-on-read — FB inventory effect of the deploy-event
fix), DR-025 + S139 amendment (commission from MBR — unchanged),
DR-027/028 (two-database split — W17.1 named operational-line
only), DR-032 (canonical bet record — idempotency fix touches
bet_id derivation only).

## Anchor

```
# Session-open:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-06-13 10:21 ACST

# Session-close:
TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-06-13 10:58 ACST
```

## Pre-flight checks

Open ritual ran silent per `bethub-session-open` (seventh
consecutive clean). Required reads completed (`current_state.md`,
`standing_instructions.md` in full, `project_context.md`,
`SESSION_146.md`, then both conditional reads — `m1_report.md`
(318 lines) and `w17_report.md` (725 lines) both present on
disk). Pre-flight directory listing clean: 13 root `.md` +
`openapi.json`, all directories present, `.close_out_backups/`
held only `SESSION_147_opening_prompt.md` (expected).

**Drift-check (Step 5): clean.**
- (a) `current_state.md` "Last updated" matched `SESSION_146.md`
  "Closed:" (2026-06-13 09:17 ACST).
- (b) `SESSION_146.md` present, non-empty (221 lines).
- (c) `v3_build_picture.md` updated at S146 close; render
  condition TRUE — build picture rendered at open.

Same-workday open (~64 min after S146 close) — tight recap.

## Session shape

Report-triage-plus-follow-up-brief session, exactly the shape
`current_state.md` named. Both Code reports existed at open
(operator ran M1 then W17 between sessions). Inventory-first
triage of both; operator-relevant findings surfaced in the open
output; operator confirmed the proposed W17.1 routing ("Yes go
ahead please"); grounding pass against the live v3 repo; W17.1
brief drafted end-to-end per `bethub-brief-drafting` with
call-driven surfacing (two visibility calls at hand-off); the
operator's lock condition ("high-risk items mitigated") drove
one substantive addition (the liability guard) before LOCK.

## What was delivered

**1. M1 report triaged — CLEAN CLOSE.** All seven items
delivered; pytest 896/0 at M1 close; lint-imports 5/0; mypy 0 on
`betfair_adapter.py`; Alembic adopted with empty `sqlite_master`
diff (35/35 identical) and the operator stamp path documented —
**DR-031's migration-framework deferral is CLOSED.** Four
findings (f#1–f#4), all technical, all accepted as Claude's
calls: f#1 three identical autouse clock-freeze fixtures accepted
as-is (consolidate only if a fourth appears); f#2 broken
`_COMMISSION_TABLE` pointer correctly updated in the rewrite;
f#3 repository-side row-factory pattern left untouched
(internally consistent; not the W15 f#2 surface); f#4 the
re-use-the-schema-helpers Alembic baseline accepted as the
going-forward revision pattern.

**2. W17 report triaged — FULL DELIVERY, no checkpoint stop.**
All eleven §5 sub-sections delivered with tests; pytest 917/0
(new standing baseline); vitest 77/0; tsc + build clean. W17
report F1 (baseline mismatch) explained benignly: M1 ran first,
so the brief's expected 894/2 was already 896/0. Findings F2,
F5, F6, F7-partial, F8, F9 routed into W17.1; F3 (sparkline) and
F4 (promo→book quick-tap) deferred to post-live-use; F7 tail
(liquidity indicator, handicap composite) deferred to
refine-in-use.

**3. W17.1 brief — drafted, grounded, LOCKED.**
`dr029/w17_racing_pages/w17_1_brief.md`, 344 lines, 11 sections.
Anchors grounded against the live repo (promo adapter
`append_event` surface + `free_bet_deployed` enum location;
`_translation.py` sibling-translator pattern; empty
`ui/api/dependencies/` package as the composition-root home).
Six items: FB deploy-event write (F2), idempotency threading
(F5), Betfair AAB selector (F6), HedgeModal safety slice (F7
partial: $50 BW-cash default, $5 FB rounding, 500 ms in-modal
lay refresh, liability guard), §9.9 translation wiring (F8),
production composition root with MOCK_BETFAIR dry-run mode (F9).
Report spec includes a plain-language operator go-live runbook.

**4. Liability guard added on operator's lock condition.** The
operator locked W17.1 conditional on high-money-loss risks being
mitigated. Gap identified: no fat-finger protection on lay
placement (a mistyped lay price of 44 vs 4.4 ≈ 43× liability).
Added to §5.4: explicit confirm when computed lay liability
exceeds `MAX_LIABILITY_SOFT_CAP` (default $500, tunable) OR the
entered lay price diverges > 10 ticks from live best lay. Guard
not disableable in code; only the cap value is tunable. This
joins the never-profit-target-lay rule and the $50 BW-cash
default as the third named bet-safety behaviour on the page.

**5. Code execution prompt** for W17.1 handed to the operator
in-chat at close (reproduced in the S148 opening prompt).

## Standing-instruction adherence check

- **Cat 1 silent open-ritual — CLEAN** (seventh consecutive,
  S141–S147). Single combined output, zero step narration.
- **Cat 1 calendar-calibrated recap** — honoured (same-workday,
  tight; headline-first since both reports were good news).
- **Cat 1 build-picture conditional render** — honoured
  (rendered; streams moved at S146 close). 27 consecutive clean.
- **Cat 1 open-items delta** — honoured (rendered).
- **Cat 1 inventory-first cadence** — honoured on both reports:
  13 findings inventoried (4 M1 + 9 W17), classified on
  operational impact; 5 surfaced to operator in plain gambling
  language (FB shows twice, double-log risk, UUID paste
  friction, missing $50 default, live-wiring gap), 8 handled as
  Claude's territory.
- **Cat 1 plain language** — honoured (no schema names in
  operator-facing triage; DRs bracket-reminded).
- **Cat 2 anchors / reads / pre-flight / drift-check** —
  honoured.
- **Cat 3 Desktop Commander discipline** — honoured; chunked
  brief writes (≤30 lines/call after one performance tip),
  verify-after-write (wc -l + section greps), one surgical
  edit_block for the §5.5 event-type-id correction and one for
  the liability guard, both verified in returned context.
- **Cat 3 empirical verification** — honoured: W17.1 anchors
  grounded against the live repo (greps on the promo adapter,
  translation layer, dependencies package, component paths)
  before being named in the brief.
- **Cat 5 make-software-calls-don't-punt** — honoured: M1
  findings f#1/f#3/f#4 all accepted as Claude's calls with
  one-line visibility; idempotency mechanism shape, deploy-event
  layering, selector placement all called in the brief.
- **Operator-confirmed forward routing** — honoured ("Close it
  out please. I will provide Code the prompt now").

## Open items in (carry to S148)

- **W17.1 — awaiting-code-execution.** Operator runs the W17.1
  Code session against the locked brief. S148 triages
  `dr029/w17_racing_pages/w17_1_report.md`. Coherent stop line
  if Code overruns: after item 4 (live-wirable + ledger-safe);
  AAB selector + HedgeModal slice would carry as findings.
- **Operator go-live sequence (post-W17.1, gates W16):** mock
  dry run → live read-only smoke on one race → one small real
  ⚡ lay. The report's runbook section walks it.
- **F3 sparkline + F4 promo→book quick-tap + F7 tail** —
  deferred to post-live-use refinement; operator's first-use
  friction verdict sizes them.
- Parking-lot carries unchanged: calculator rethink;
  cross-account spot-check view; settings-area cadence
  follow-up brief (now also FW11's price-window UI); greyhound
  operational constraint verification;
  `cascaded_at_settlement_state` closed-enum revisit (W8);
  §2.4 Fix 4 cadence design dependency; optional live
  `get_account_funds()` probe; Betfair API membership tier
  investigation (awaiting BetWatch).

## Open items out (closed/advanced S147)

- **M1 — ✅ CLOSED CLEAN.** Pytest standing baseline is now
  **917/0** (post-W17). Alembic adopted; DR-031 deferral closed.
- **W17 Code execution — ✅ DELIVERED in full**; triage clean;
  follow-ups consolidated into W17.1 (no separate routing
  needed).
- W17 report F1 — explained (M1-first ordering), no action.

## Session close state

- **`dr029/w17_racing_pages/`** — `scope_settlement.md`,
  `w17_brief.md`, `w17_report.md` (carried), `w17_1_brief.md`
  (NEW, 344 lines, LOCKED).
- **`dr029/m1_maintenance/`** — `m1_brief.md`, `m1_report.md`
  (both carried; arc closed).
- **v2 + v3 codebases** — untouched by Chat (grounding greps
  only, read-only).
- **`current_state.md`** — rotated to S147 close.
- **`v3_build_picture.md`** — updated (M1 → done one-session
  carry; W17 → blocked-on-W17.1; W17.1 row added
  awaiting-code-execution; current-session detail rewritten).
- **`.close_out_backups/`** — `SESSION_148_opening_prompt.md`
  written; stale `SESSION_147_opening_prompt.md` swept.
- **No edits** to `decisions.md`, `standing_instructions.md`,
  or other canonical truth.

## Forward routing

**Confirmed with operator** ("Close it out please. I will
provide Code the prompt now."). Between sessions: operator runs
W17.1 in Code using the prompt provided (carried in the S148
opening prompt). S148 opens on W17.1 report triage; on a clean
close the operator runs the go-live runbook (dry run → live
smoke → small ⚡), and W16 cutover unblocks behind the
operator's live validation.

## Close-out notes

Short, clean session (~37 min) — the payoff shape of the S145/
S146 discipline: both reports arrived clean enough that triage
plus the follow-up brief fit one tight session. The operator's
lock condition ("high-risk items mitigated") earned its keep:
the liability-guard gap (fat-finger lay price) was real, named,
and closed in the brief before lock rather than discovered live.
W16 cutover is now exactly two steps away: W17.1 execution, then
the operator's first live ⚡.
