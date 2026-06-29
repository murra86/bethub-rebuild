# Session 181 — Build 1 report triaged clean; Free Bet button restore brief drafted, locked + handed to Code, gate released; Code built it (report landed, S182 triages)

**Opened:** 2026-06-23 19:21 ACST
**Closed:** 2026-06-23 20:42 ACST
**Duration:** ~1h21m, single calendar day. Same-workday continuation
of S180 (closed 18:54 ACST; S181 opened 19:21, 27 min later).
**Tool routing:** Claude Chat (Build 1 report triage + free-bet-restore
brief drafting + two Code-gate triages) + Desktop Commander (governance
reads/writes; five v3 read-only groundings — `presets.ts`,
`evEngine.ts`, the `promo_template.kind` enum + CHECK, `seed_promos.py`,
`PromoBar.tsx` — plus live git state). No DB access. One out-of-session
Code build ran this session (the free-bet restore); its report landed
on disk but triage is routed to S182 per operator.
**Governing DRs invoked:** DR-021 (anchors), DR-032 (bet promo link =
`bets.promo_template_id` — referenced, **unaffected**: the free-bet pick
carries no serial), DR-030 (module layering — frontend picker), DR-031
(additive; this fix is frontend-only, no migration). DR-027/028 **not
triggered** (single-DB, frontend-only).

---

## Anchor

- Open: `2026-06-23 19:21 ACST` (session-open ritual; same-workday
  continuation of S180's 18:54 close).
- Close: `TZ="Australia/Adelaide" date` → `2026-06-23 20:42 ACST`.

## Pre-flight checks

Open ritual ran clean: drift-check passed (current_state ↔ SESSION_180
↔ v3_build_picture all matched the 18:54 S180 close); `.close_out_backups/`
held only the S181 opening prompt; rebuild root clean (accumulated
governance .md files — audit_landscape, data_sources,
external_api_resources, racing_api_field_catalogue — are known
additions, not phantom). Required reads completed in order
(current_state, standing_instructions in full, project_context,
SESSION_180, plus the S181 triage target — Code's Build 1 build report).
Same-workday tight recap; build-picture full-table render compressed to
its essence (only the interface-refinement stream moved, operator in
flow on this exact build) — a dev-lead ritual call to keep the triage
front-and-centre.

## Session shape

Three strands across two out-of-session Code actions. First, triaged
Code's **Build 1 build report** (`promo_attach_build1_report.md`, 404
lines): all six §5 pieces built, Python 1158→1166 (+8, 0 regressions),
frontend tsc clean + vitest 103/103, settlement seam byte-identical
(`9e07a75d…`), HEAD unchanged + dirty-tree discipline held — clean on
every gate. Surfaced the one operator-relevant finding (F1, the
bare-free-bet reconciliation call). Second, the operator **reversed
F1**: the Free Bet button goes back, because selecting it flips the
race-screen EV column into free-bet→cash conversion mode (the v2 tool
for spotting good conversions in the 65–70% band) — an operational
function Code's "just a deployment marker" read missed. Grounded the
restore against the live tree (the EV engine's `evFreeBet` branch is
intact; the `promo_template.kind` set is closed with no free-bet slot,
so a catalogue row would force a table rebuild). Third, the
**brief-drafting skill fired**: drafted + locked the free-bet-restore
brief (frontend-only, picker-button-not-catalogue-row), provided the
Code prompt, triaged Code's read-and-confirm gate (faithful, released
with the presetId-vs-null detail left to Code's discretion). Code then
built it out-of-session — report landed (181 lines), triage routed to
S182 per operator.

## What was delivered

1. **Build 1 build report triaged clean.**
   `promo_attach_build1_report.md` inventory-triaged: all six §5 pieces
   (catalogue terms, serial + EV on the bet, 9-row v2-reconciled seed,
   catalogue-driven race picker, same on Log Past Bet, tests) built and
   verified. Bet-safety gate held — `settlement.py` SHA byte-identical
   start→close (`9e07a75d…`); additive/null-tolerant proven (a no-promo
   bet round-trips both fields null on both entry paths); Python
   1158→1166 (+8, 0 regressions); frontend tsc clean + vitest 103/103;
   HEAD `2329604` unchanged, 69→69 git entries, only
   `domain/bets/__init__.py` edited among tracked files (additive, 0
   deletions). Findings F2–F7 + self-assessment gaps all
   Claude's-territory / clean.

2. **F1 reversed (operator call).** The bare "Free Bet" — excluded from
   the catalogue by Code's F1 — is restored, because the button drives
   the EV column's free-bet→cash conversion display (the 65% conversion
   tool the operator uses every burst to spot good conversions). Code's
   exclusion was right that it's not a promo *offering*, but missed that
   it's an EV-display mode the operator depends on.

3. **Free-bet-restore brief drafted, locked + handed to Code.**
   `interface_triage/free_bet_button_restore_brief.md` (233 lines, 11
   sections). Frontend-only surgical fix: restore a fixed "Free Bet"
   button on the promo bar (`PromoBar.tsx`) that sets
   `promo_type: 'free_bet'` (terms null, no serial), reaching the intact
   `evFreeBet` branch (`evEngine.ts`, 0.65 rate) so the EV column shows
   the conversion. Design call: **picker button, not a catalogue row** —
   the `promo_template.kind` CHECK is a closed set
   (insurance/bonus_winnings/price_boost/ew_cashback/other) with no
   free-bet slot, and altering it means a table rebuild Build 1 avoided;
   the free bet is genuinely an EV-display affordance, not a catalogue
   offering, so the button is the faithful v2 shape. Hard limits: no
   backend/schema/seed/catalogue change, no `is_free_bet`-path touch, no
   `evEngine.ts` edit, settlement byte-identical, dirty-tree discipline
   (protects the uncommitted Build 1 + in-flight betfair_client work).
   Provided the ready-to-paste Code prompt.

4. **Code's read-and-confirm gate triaged + released.** Code's
   restatement faithful (scope, hard limits, output spec correct; all
   anchors verified live — settlement SHA, HEAD/git, the picker +
   EV-engine line anchors; routing confirmed: `promo_type === 'free_bet'`
   → `evFreeBet`). Released with the one flagged detail (the reused
   preset's leftover `presetId` label) left to Code's discretion.

5. **Code built it out-of-session (report landed, S182 triages).**
   `free_bet_button_restore_report.md` (181 lines): all three §5 pieces
   built frontend-only; `FREE_BET_CONFIG` constant + Free Bet button +
   `selectFreeBet` toggle; verified `promo_type === 'free_bet'` routes to
   `evFreeBet`; new `PromoBar.test.tsx` (6 tests). tsc clean, vitest
   103→109 (+6, 0 regressions), Python 1166 unchanged, settlement
   byte-identical, HEAD/git unchanged. Code chose a dedicated
   `FREE_BET_CONFIG` over reviving `buildConfigFromPreset` (narrows the
   F6 reversal to the free-bet slice). Two flags (F1 inert config
   controls left visible; F2 F6 partial reversal by design) — both
   Claude's-territory, for S182 triage. **Triage routed to S182 per
   operator (auto-run on open, no confirmation).**

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open 19:21 + close 20:42 ACST. ✓
- **Silent session-open (Cat 1):** steps 1–5 silent; same-workday tight
  recap; build-picture full-table render compressed (dev-lead ritual
  call — only the active stream moved, operator in flow). ✓
- **Inventory-first on long reports (Cat 1):** Build 1 report triaged
  inventory-first; classified by operational impact; surfaced only F1
  (operator-relevant), held F2–F7 as Claude's territory. ✓
- **Lead-with-the-call / brevity (Cat 1):** triage led with the
  bet-safety verdict, then the one F1 decision. ✓
- **Make-the-call / don't punt (Cat 5):** the design call
  (picker-button-not-catalogue-row, grounded in the closed kind-set) was
  made, not punted; surfaced with its UX consequence. ✓
- **Ground "already built" claims (Cat 4, S178):** the restore was
  grounded against the live tree (EV engine branch intact; kind-set
  closed) before the brief locked. ✓
- **Brief-drafting skill fired (Cat 2):** ran end-to-end — job named,
  pre-flight grounding, universal spine, hard limits, output spec, Code
  prompt at hand-off. ✓
- **Always provide the Code prompt at hand-off (Cat 2, S163):** provided
  without being asked, plus the gate-release response. ✓
- **Write discipline / chunking (Cat 3):** brief + this record written in
  ~25-line chunks via `Desktop Commander:write_file`; verified on
  read-back. ✓
- **`create_file` banned (Cat 3):** all writes via
  `Desktop Commander:write_file`. ✓

## Open items

Pointer-only — full live list in `current_state.md`.

## Open items out (closed / resolved S181)

- **Triage the Build 1 build report** — DONE; clean on every gate. ✅
- **F1 bare-free-bet reconciliation call** — RESOLVED; operator reversed
  (Free Bet restored). ✅
- **Draft the free-bet-restore brief** — DONE; locked + handed to Code. ✅
- **Free-bet-restore read-and-confirm gate** — DONE; faithful, released. ✅

## New items in (S181)

- **Triage the free-bet-button-restore build report** — S182 primary;
  auto-run on open per operator (no confirmation prompt). On a clean
  triage → Build 2 brief.

## Session close state

- **Rebuild root:** clean, no new files at root, no phantom files.
- **`interface_triage/free_bet_button_restore_brief.md`:** written (233
  lines). Locked.
- **`interface_triage/free_bet_button_restore_report.md`:** Code's build
  report on disk (181 lines) — S182 triage target.
- **`current_state.md`:** rotated to S181 close (20:42 ACST).
- **`v3_build_picture.md`:** Interface-refinement stream next-milestone
  advanced (S181: Build 1 triaged clean; F1 reversed; free-bet-restore
  brief locked + handed + gate released + Code built it; S182 triages
  the report → Build 2); timestamp bumped.
- **`standing_instructions.md`:** not edited (no new instruction
  surfaced). S178's + S180's pending KB re-uploads still stand.
- **`decisions.md`:** not edited this session (DR-032 amendment was S180;
  its Project-KB re-upload remains pending).
- **`.close_out_backups/`:** `SESSION_182_opening_prompt.md` written;
  stale `SESSION_181_opening_prompt.md` removed.

## Forward routing (confirmed with operator)

Operator confirmed close after releasing Code on the free-bet-restore
build. **S182's opening action is to triage Code's
free-bet-button-restore build report** (`free_bet_button_restore_report.md`)
— **run automatically on open, no operator confirmation prompt required**
(operator's explicit instruction this close). Inventory pass; confirm
the bet-safety gate (settlement SHA byte-identical — trivially,
frontend-only); confirm the Free Bet pick drives the conversion EV; note
the two Code flags (F1 inert controls, F2 F6 partial reversal). On a
clean triage, **draft the Build 2 brief** (credit-in + cycle link —
carries O5 real-UUID stamp / O6 idempotency / O7 FINALISED; hard-depends
on Build 1). The Racing-API placings backfill runs as its own parallel
brief (not a dependency). Post-build sequence unchanged: launcher brief
(F9/F10 + F12 + rebuild-if-source-newer) → W16 cutover scoping. Forward
routing confirmed.
