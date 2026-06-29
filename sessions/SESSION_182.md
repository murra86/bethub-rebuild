# Session 182 — Free-bet-restore report triaged clean; free-bet conversion grounded (lay+commission, not flat 0.65); Build 2 brief drafted, locked + handed to Code, gate released

**Opened:** 2026-06-23 20:55 ACST
**Closed:** 2026-06-23 22:01 ACST
**Duration:** ~1h6m, single calendar day. Same-workday continuation of
S181 (closed 20:42 ACST; S182 opened 20:55, 13 min later).
**Tool routing:** Claude Chat (free-bet-restore triage + free-bet
conversion grounding + Build 2 brief drafting + Code-gate triage) +
Desktop Commander (governance reads/writes; ~8 v3 read-only code
groundings — `evEngine.ts`, `commission.ts`, `bets` schema,
`fb_deployment.py`, `domain/promos` validator, `racing.py` cycle mint,
BetLog/LogPastBet surfaces, `promos.py`, settlement boundary; the Build 2
brief writes). One DC write-timeout episode mid-brief (recovered, §6–§8
re-appended clean). No DB access. One out-of-session Code action released
this session (Build 2 — runs out-of-session; triage routed to S183).
**Governing DRs invoked:** DR-021 (anchors), DR-032 (promo link =
`bets.promo_template_id`, amended S180 — Build 2's serial reference),
DR-030 (module layering — credit-in endpoint on `promos.py`), DR-031
(additive; Build 2 is a promo-*event* write, no bets-schema change).
DR-027/028 **not triggered** (single-DB; placings off the credit-in path).

---

## Anchor

- Open: `2026-06-23 20:55 ACST` (session-open ritual; same-workday
  continuation of S181's 20:42 close).
- Close: `TZ="Australia/Adelaide" date` → `2026-06-23 22:01 ACST`.

## Pre-flight checks

Open ritual ran clean: drift-check passed (current_state ↔ SESSION_181 ↔
v3_build_picture all matched the 20:42 S181 close); `.close_out_backups/`
held only the S182 opening prompt; rebuild root + `interface_triage/`
clean (no phantom files). Required reads completed in order
(current_state, standing_instructions in full, project_context,
SESSION_181, plus the S182 triage target — the free-bet-restore report).
Per operator's S181 instruction, S182's opening action was the
free-bet-restore triage run **automatically on open, no confirmation
prompt** — honoured. Same-workday tight recap; build-picture compressed
to the active stream (only interface-refinement moved, operator in flow).

## Session shape

Four strands. First, **triaged Code's free-bet-button-restore report**
(`free_bet_button_restore_report.md`, 181 lines) automatically on open:
clean on every gate — settlement byte-identical, Python 1166 unchanged,
vitest 103→109, working tree intact; the Free Bet pick drives the EV
column's conversion path (unit-proven); two flags (F1 inert config
controls, F2 partial F6 reversal) both Claude's-territory / already
parked. Second, the operator **challenged the conversion-rate framing**:
I'd said "0.65 rate"; the operator was right that the conversion must be
computed from the live Betfair lay + that race's commission, not a flat
estimate. Grounded `evEngine.ts` + `commission.ts`: `evFreeBet` computes
a true lay-hedge from `bfLay` + `getCommission(mbr)` — the flat 0.65
(`DEFAULT_FB_CONVERSION_RATE`) is **not** in that path at all (it's used
only in the insurance/bonus-winnings models, where a triggered free bet
is a future hypothetical). Corrected the misstatement; confirmed the
button does exactly what the operator wants. Caveat surfaced: no live lay
→ the column shows nothing rather than a flat guess.

Third, the **brief-drafting skill fired for Build 2** (credit-in + cycle
link). Grounded extensively against the live tree first (Cat 4 — don't
lock on memory, especially a money-write): confirmed Build 1's substrate
is in (`bets.promo_template_id` + `promo_ev_at_log` present; a new
read-only `promos.py` router serving the catalogue with structured terms
per serial), located the credit-write mirror (`record_free_bet_deployment`),
the `FreeBetCreditedPayload`/`PromoCashCreditedPayload` validators, the
`_coerce_uuid` O5 trap, the `racing.py` cycle mint, and the two confirm
surfaces. Drafted the brief in numbered sections; a Desktop Commander
write timed out mid-draft (§6–§8 append) — recovered per the partial-state
discipline (verified the file landed through §5.6, re-appended §6–§11
clean). Final brief: 308 lines, 11 sections, locked + stamped. Fourth,
**triaged Code's read-and-confirm gate** — faithful on every count (all
six scope pieces, anchors, hard limits, output spec, disciplines; the one
discretion item left to Code) — and **released Code** with the build
prompt.

## What was delivered

1. **Free-bet-restore report triaged clean (auto on open).**
   `free_bet_button_restore_report.md` inventory-triaged: frontend-only,
   settlement byte-identical, Python 1166 unchanged, vitest 103→109 (+6),
   tsc clean, HEAD/git unchanged, uncommitted Build 1 + betfair_client
   work intact. The Free Bet pick routes to `evFreeBet` (unit-proven,
   distinct from no-promo). Flags F1 (inert max-stake/return-type controls
   visible for the free-bet pick) + F2 (F6 dead code partially reversed by
   design) both Claude's-territory / already parked. No surgical fix, no
   blocker.

2. **Free-bet conversion grounded + misstatement corrected.** The
   race-screen Free Bet button computes the conversion as a true lay-hedge
   from the live Betfair lay price and that race's commission
   (`evFreeBet`, `evEngine.ts`) — **not** the flat 0.65. `getCommission`
   uses the race's MBR, 8% fallback. The 0.65 constant lives only in the
   insurance/bonus-winnings EV (future-hypothetical free bets). Caveat:
   no live lay → no conversion shown (specific calc or nothing). My
   earlier "0.65 rate" framing was wrong; corrected.

3. **Build 2 brief drafted, locked + handed to Code.**
   `interface_triage/promo_attach_build2_brief.md` (308 lines, 11
   sections). Commissions the production credit-in: a new
   `record_free_bet_credit` (mirrors the deploy write) that, on a confirmed
   settled-lost Safety Net qualifier with a promo attached, writes one
   promo event — FREE_BET_CREDITED or PROMO_CASH_CREDITED by the promo's
   `return_type` (cash in scope), `credit_source='triggered'`, real
   qualifier UUID as `triggering_bet_id` (O5 — raise, never the
   `_coerce_uuid` fresh fallback), the bet's `promo_template_id` as
   `triggering_promo_instance_id` (Option B, no validator relax), amount =
   stake × return_pct (no cap), status FINALISED (O7), via
   `append_event` — **off settlement**. Plus: a shared `POST
   /v1/promos/credit-in` endpoint on the new `promos.py`; the two confirm
   surfaces (BetLog scaffold enable + LogPastBet inline) → one write gated
   on `safety_net ∧ settled_lost ∧ promo_template_id IS NOT NULL`; a
   once-per-`triggering_bet_id` idempotency guard (O6); Piece A cycle
   inheritance (deployed free bet inherits its qualifier's cycle via the
   stamped trigger). Hard limits: settlement byte-identical, no
   manual-resolve/provisional hook, no validator relax, no bets-schema
   change, no cap, dirty-tree discipline. Locked + stamped
   2026-06-23 (S182), operator-approved. Code prompt provided.

4. **Code's read-and-confirm gate triaged + released.** Code's
   restatement faithful (six scope pieces, hard limits, output spec,
   disciplines; anchors `fb_deployment.py:82`, `BetLog.tsx:510`,
   `racing.py` ~:897/~:936 all correct; the new-module-vs-alongside
   discretion was Code's to make; the added "verify Build 1 substrate live
   at start" pre-check is sound, not a deviation). Released with the build
   prompt. Code builds out-of-session; report routed to S183.

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open 20:55 + close 22:01 ACST. ✓
- **Silent session-open (Cat 1):** steps 1–5 silent; same-workday tight
  recap; auto-triage on open per operator (no confirm). ✓
- **Inventory-first on long reports (Cat 1):** free-bet-restore report
  triaged inventory-first; classified by impact; surfaced the bet-safety
  verdict + the one operational confirmation. ✓
- **Verify empirically / ground "already built" (Cat 3, Cat 4 S178):**
  the conversion-rate challenge resolved by reading the live `evEngine.ts`
  (not trusting the report's wording or my own summary); Build 2 grounded
  against the live tree before locking. ✓
- **Own mistakes (responding-to-mistakes):** corrected the "0.65 rate"
  misstatement cleanly when the operator pushed. ✓
- **Make-the-call / don't punt (Cat 5):** Build 2 endpoint placement,
  idempotency key, module choice all made as dev-lead calls; only the
  operational ones (cash-in scope, O5 phantom-id consequence) surfaced. ✓
- **Don't surface dev-lead calls by default (Cat 1, S163):** hand-off kept
  tight — two operator-relevant flags, not the full call list. ✓
- **Brief-drafting skill fired (Cat 2):** ran end-to-end — job named,
  pre-flight grounding, universal spine, hard limits, output spec, Code
  prompt. ✓
- **Always provide the Code prompt at hand-off (Cat 2, S163):** provided
  at lock + the release prompt at gate-clear, both unprompted. ✓
- **Pre-execution risk advisory + partial-state recovery (Cat 3, S126):**
  chunked writes; on the DC timeout, verified state and recovered without
  duplication. ✓
- **`create_file` banned (Cat 3):** all writes via
  `Desktop Commander:write_file`. ✓

## Open items

Pointer-only — full live list in `current_state.md`.

## Open items out (closed / resolved S182)

- **Triage the free-bet-button-restore report** — DONE; clean on every
  gate. ✅
- **Free-bet conversion-rate question** — RESOLVED; grounded as live
  lay+commission, not flat 0.65; misstatement corrected. ✅
- **Draft the Build 2 brief** — DONE; locked + handed to Code. ✅
- **Build 2 read-and-confirm gate** — DONE; faithful, released. ✅

## New items in (S182)

- **Triage the Build 2 build report** — S183 primary; auto-run on open per
  operator (no confirmation prompt). On a clean triage → the promo-on-bet
  + credit-in arc closes; sequence moves to launcher brief → W16 cutover.

## Session close state

- **Rebuild root + `interface_triage/`:** clean, no phantom files.
- **`interface_triage/promo_attach_build2_brief.md`:** written (308
  lines), LOCKED + stamped 2026-06-23 (S182), operator-approved.
- **`interface_triage/promo_attach_build2_report.md`:** not yet present
  (Code runs out-of-session) — S183 triage target.
- **`current_state.md`:** rotated to S182 close (22:01 ACST).
- **`v3_build_picture.md`:** interface-refinement stream next-milestone
  advanced (S182: free-bet-restore triaged clean; conversion grounded;
  Build 2 brief locked + handed + gate released; S183 triages the report);
  timestamp bumped.
- **`standing_instructions.md`:** not edited (no new instruction surfaced).
  S178's + S180's pending KB re-uploads still stand.
- **`decisions.md`:** not edited this session (DR-032 amendment was S180;
  its Project-KB re-upload remains pending).
- **`.close_out_backups/`:** `SESSION_183_opening_prompt.md` written;
  stale `SESSION_182_opening_prompt.md` removed.

## Forward routing (confirmed with operator)

Operator confirmed close after releasing Code on Build 2. **S183's opening
action is to triage Code's Build 2 build report**
(`promo_attach_build2_report.md`) — **run automatically on open, no
operator confirmation prompt** (operator's explicit instruction this
close, mirroring the S182 free-bet-restore pattern). Inventory pass;
confirm the bet-safety gate (settlement SHA byte-identical); confirm the
round-trip (a qualifying settled-lost safety-net loss credits once, a
repeat doesn't); confirm the deployed free bet inherits its qualifier's
cycle; surface any findings. On a clean triage, the promo-on-bet +
credit-in arc is **complete** — the sequence then is the launcher brief
(F9/F10 + F12 + rebuild-if-source-newer) → W16 cutover scoping. The
Racing-API placings backfill remains its own parallel brief (not a
blocker). Forward routing confirmed.
