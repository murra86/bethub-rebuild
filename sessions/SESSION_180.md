# Session 180 — Build 1 brief (promo-attach foundation) drafted, locked + handed to Code; Code's read-and-confirm gate triaged + released; DR-032 amended

**Opened:** 2026-06-23 17:48 ACST
**Closed:** 2026-06-23 18:54 ACST
**Duration:** ~1h06m, single calendar day. Same-workday continuation of
S179 (closed 17:37 ACST; S180 opened 17:48, 11 min later).
**Tool routing:** Claude Chat (brief drafting + Code-gate triage + the
DR-032 amendment) + Desktop Commander (governance reads/writes; two v3
read-only schema groundings — `bets` + `promo_template`; one v2 read-only
grounding — `promoPresets.js`). No DB access. One out-of-session Code
action (the read-and-confirm gate) was triaged this session; the build
itself runs out-of-session next.
**Governing DRs invoked:** DR-021 (anchors), DR-032 (**amended this
session** — the promo-on-bet link shifts to the kind-catalogue serial,
single-level), DR-030 (module layering — the new promos read route),
DR-031 (additive migration; Alembic stays deferred), DR-033 (placings =
operator manual flag, off Build 1's path), DR-027/028 (**not triggered** —
Build 1 is single-DB), DR-019 (P&L unaffected).

---

## Anchor

- Open: `2026-06-23 17:48 ACST` (session-open ritual; same-workday
  continuation of S179's 17:37 close).
- Close: `TZ="Australia/Adelaide" date` → `2026-06-23 18:54 ACST`.

## Pre-flight checks

Open ritual ran clean: drift-check passed (current_state ↔ SESSION_179 ↔
v3_build_picture all matched the 17:37 S179 close); `.close_out_backups/`
held only the S180 opening prompt; rebuild root clean. Required reads
completed in order (current_state, standing_instructions in full,
project_context, SESSION_179, plus the two session-specific reads — the
review report + review brief). Same-workday tight recap; build picture +
open-items delta skipped as ritual noise on an 11-min continuation.

## Session shape

Single deliverable with a Code-gate triage in the middle. The
`bethub-brief-drafting` skill fired for the Build 1 brief (promo-attach
foundation). Before drafting, grounded the two load-bearing anchors the
build rests on against the live v3 tree (the `bets` schema — no promo
field, additive pattern confirmed; the `promo_template` catalogue table —
no book/run-window, the right single-level home) and the v2 promo set
(`promoPresets.js` — the 10 promos to seed). One operator scope call was
taken mid-draft (catalogue is seed-from-v2 + later additions are data, not
code; no in-app management UI in Build 1 — the picker reads from the
catalogue so additions surface without a frontend change). Drafted the
brief end-to-end to disk (399 lines), surfaced the catalogue-driven-picker
interpretation + the DR-032 governance note, and provided the ready-to-paste
Code prompt. The operator then ran Code's read-and-confirm gate
out-of-session; triaged Code's restatement (faithful) + its three held
flags (all approved), and provided the release response. Closed with the
DR-032 amendment authored into `decisions.md` and the brief's anchors
folded to match the two extra files Code surfaced.

## What was delivered

1. **Build 1 brief drafted, locked + handed to Code.**
   `interface_triage/promo_attach_build1_brief.md` (414 lines after the
   close-fold edits). Eleven sections on the universal brief spine, six
   build pieces (§5.1–§5.6): structured terms on `promo_template`
   (refund_positions / return_type / return_pct / cap, typed, additive);
   serial + EV columns on `bets` (`promo_template_id` + `promo_ev_at_log`,
   additive, side/commission precedent); seed the catalogue from v2's 10
   promos + reconcile the two term reps (O3); catalogue-driven race-screen
   picker → serial on the bet; the same on Log Past Bet; tests +
   settlement-seam SHA proof. Read-write, single bounded session,
   dirty-tree discipline, additive-only, Build-1-only hard limits.

2. **Operator scope call locked — catalogue is extensible by data, not
   code.** The initial catalogue emulates v2's promo set. New promos are
   later work, added through the catalogue (the adapter CRUD stays intact)
   — **not** a code change. No in-app catalogue-management UI in Build 1;
   the picker reads from the catalogue so a later-added row appears in both
   entry paths with no frontend touch. The "scope open for additions"
   requirement is baked in as a §2/§9 design constraint.

3. **Code's read-and-confirm gate triaged + released.** Code's restatement
   of the six pieces, hard limits, and output spec was faithful, and it
   verified the load-bearing anchors against the live tree (settlement SHA
   matches `9e07a75d…`; the additive precedents; the persistence symbols).
   Three held flags, all approved as in-scope (not drift):
   - **`workflows/bet_entry/v1/orchestrator.py`** — where `SoftBookLogRequest`
     is *defined* (~:467; `racing.py:906` is only the construction site) +
     its `SoftBookRecordInputs` hand-off (~:1401). Required to thread the
     race path. Plus `SoftBookRecordInputs` (`record_builder.py` ~:169).
   - **`store/repositories/bets.py`** — the `BetRow` dataclass + the
     `write_bet_record` INSERT (~:553) / `read_bet_record` SELECT (~:692).
     Required for the §5.2 persistence round-trip.
   - **Adapter line-drift** — the template methods are at ~:277–330, not
     ~:336–403 (that's the promo-instance methods, left alone). Edit by
     symbol.
   Release response added two reinforcements: strictly additive +
   null-tolerant end-to-end (a no-promo bet round-trips exactly as today,
   both fields null); settlement seam byte-identical (both extra files are
   entry-side plumbing, nowhere near `settlement.py`).

4. **DR-032 amended** (`decisions.md`, dated 2026-06-23, appended as a note
   — DRs are immutable, changes ride as appended notes). Records that the
   bet's promo link is `bets.promo_template_id` (the kind-catalogue serial,
   single-level), not the documented-but-unbuilt per-instance `promo_id`;
   `promo_ev_at_log` persists alongside; the change reinforces (does not
   replace) the canonical-reference schema commitment, and is single-DB
   (no cross-DB / analytical join). Built by Build 1.

5. **Brief anchors folded to match the build.** Post-gate, the two
   authorised files (orchestrator.py, store/repositories/bets.py) were
   folded into §5.2/§5.4 as named edit targets, and the §5.1 adapter
   line-drift corrected — so the locked contract matches what Code builds
   (no "named anchors only" tension when those files appear in the diff).

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open 17:48 + close 18:54 ACST. ✓
- **Silent session-open (Cat 1):** steps 1–5 silent; same-workday tight
  recap; build picture + open-items delta skipped (11-min continuation). ✓
- **Brief-drafting skill fired (Cat 2):** the `bethub-brief-drafting` skill
  ran end-to-end — job named, pre-flight grounding of the load-bearing
  anchors, universal spine, hard limits, output spec, Code prompt at
  hand-off. ✓
- **Ground "already built" claims (Cat 4, S178):** the two foundation
  anchors (bets schema + promo_template) were re-read against the live tree
  before the brief locked against them. ✓
- **Empirical verification before editing governance (Cat 3):** DR-032 was
  re-read in full before the amendment was authored. ✓
- **Make-the-call / don't punt (Cat 5):** the dev-lead calls (column names,
  soft-reference no-FK, catalogue-driven picker, the bare-free-bet
  reconciliation routed to Code) were made, not punted. The one operational
  call (catalogue extensibility) surfaced to the operator. ✓
- **Don't surface dev-lead calls unless decision/operational angle (Cat 1,
  S163):** the hand-off surfaced only the catalogue-driven-picker
  (operational) + DR-032 (governance); pure dev-lead calls stayed in the
  brief. ✓
- **Always provide the Code prompt at hand-off (Cat 2, S163):** provided
  without being asked, plus the gate-release response. ✓
- **Pre-execution risk advisory (Cat 3, S126):** the DR-032 amendment was
  authored as a single insertion at a unique anchor (~18 lines content),
  kept under the ~30-line edit_block threshold. ✓
- **`create_file` banned / verify every write (Cat 3):** all writes via
  `Desktop Commander:write_file` / `edit_block`; verified on read-back. ✓
- **Plain-language / lead-with-the-call / brevity (Cat 1):** brief shape +
  calls delivered in plain gambling terms, one decision per round. ✓

## Open items

Pointer-only — full live list in `current_state.md`.

## Open items out (closed / resolved S180)

- **Draft the Build 1 brief (promo-attach foundation)** — DONE; locked +
  handed to Code (`promo_attach_build1_brief.md`). ✅
- **DR-032 amendment** — DONE; authored into `decisions.md`. ✅
- **Code's read-and-confirm gate** — DONE; triaged faithful, three flags
  approved, release response provided. ✅

## New items in (S180)

- **Run the Build 1 Code session (operator-side)** — paste the locked
  brief's Code prompt + the gate-release response; Code builds out-of-session
  and writes `interface_triage/promo_attach_build1_report.md`.
- **Triage the Build 1 build report** — S181 primary, once Code has run.
- **Re-upload `decisions.md` to the Project KB** — DR-032 was amended this
  session; the Project knowledge-base copy is now stale.

## Session close state

- **Rebuild root:** clean, no new files at root, no phantom files.
- **`decisions.md`:** DR-032 amendment appended (dated 2026-06-23); DR-033
  intact below it. Substantive edit this session, not a close-out edit.
- **`interface_triage/promo_attach_build1_brief.md`:** written (399 lines)
  + folded to 414 post-gate. Locked.
- **`current_state.md`:** rotated to S180 close (18:54 ACST).
- **`v3_build_picture.md`:** Interface-refinement stream next-milestone
  advanced (S180: Build 1 brief LOCKED + handed to Code; gate released;
  DR-032 amended; S181 triages the report); timestamp bumped.
- **`standing_instructions.md`:** not edited (no new instruction surfaced).
  S178's pending re-upload to the Project KB still stands.
- **`.close_out_backups/`:** `SESSION_181_opening_prompt.md` written; stale
  `SESSION_180_opening_prompt.md` removed.

## Forward routing (confirmed with operator)

Operator confirmed close after the Code-gate release response and the
DR-032 + brief-fold commitments. **S181 triages Code's Build 1 build
report** (`promo_attach_build1_report.md`) once the operator has run the
Code session — inventory pass, classify by operational impact, confirm the
bet-safety gate (settlement SHA byte-identical), surface the bare-free-bet
reconciliation call Code was asked to make, and on a clean triage **draft
the Build 2 brief** (credit-in + cycle link — carries O5 real-UUID stamp /
O6 idempotency / O7 FINALISED). Build 2 hard-depends on Build 1. The
**Racing-API placings backfill** runs as its own parallel brief (future
auto-surfacing, not a dependency). Post-build sequence unchanged: launcher
brief (F9/F10 + F12 + rebuild-if-source-newer) → W16 cutover scoping.
Forward routing confirmed.
