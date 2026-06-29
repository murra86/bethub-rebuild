# Session 186 — account-ref triage + the format-class FIX brief (drafted, locked, handed)

**Opened:** 2026-06-25 08:08 ACST.
**Closed:** 2026-06-25 08:57 ACST.
**Tool routing:** Claude Chat only — review-of-review triage +
fix-brief drafting via Desktop Commander, with a live baseline
probe against the v3 repo. Code commissioned out-of-session
(the locked brief + the ready-to-paste prompt handed at close).
**Governing DRs:** DR-021 (Adelaide time); DR-030 (module
boundary — why the shared canonical type stays parked);
DR-027/028 (two-database); DR-032 (promo link); settlement
byte-identity (`9e07a75d…`).

---

## Anchor

- Open: `TZ="Australia/Adelaide" date` → 2026-06-25 08:08 ACST.
- Close: same command → 2026-06-25 08:57 ACST.
- Same-workday open (~48 min after the S185 close at 07:20);
  ~49 min active session. No split triggers.

## Pre-flight checks (S186 open)

Clean open, no anomalies. Drift-check passed: current_state,
SESSION_185, and v3_build_picture all carried the expected
S185-close stamps (current_state + SESSION_185 at 2026-06-25
07:20; build picture correctly at 2026-06-24 14:46, predating
the S185 close because S185 moved no stream). Folder root clean;
`.close_out_backups/` held only SESSION_186_opening_prompt.md
(the Phase-2 carry, not a stale artefact). Both conditional
renders fired and were folded into the open: workflow-map detour
recap + the account-ref report having landed.

## Session shape

The dev arc resumed after the S185 workflow-mapping detour. The
carried S186 primary — triage the read-only account-ref surface
review and, on a clean review, draft the FIX brief — ran
end-to-end in one short session. The operator added a holistic
instruction: cross-reference `operator_workflow_map.md` while
assembling the brief, to catch adjacent areas, data transfers,
or downstream impacts worth folding in now rather than fixing
later. No build executed this session (Chat-only); Code runs the
fix out-of-session.

## What was delivered

**1. Account-ref surface review — TRIAGED CLEAN.** Read Code's
read-only review report (`account_ref_surface_review_report.md`)
and confirmed it sound: the surface is complete and bounded
(three modules — cash_flow + adapter, balance_derivation,
racing `/log-context`; one root cause), the frontend trace is
concrete (sends hex verbatim → the fix is backend-only), and the
minimal-holistic altitude holds. All three escalation triggers
NO-HIT (frontend non-hex, schema dimension, shared-type-now).
The one structural finding — the cash_flow fix and the
balance-read fix are COUPLED through F2-seeded shared tests and
must land together — carried into the brief as a hard sequencing
rule.

**2. Workflow-map cross-check (operator's holistic ask).** Ran
the fix against `operator_workflow_map.md`. The live half
restores the §3 Log Bet account-context pull, the §4 conversion
hinge ("mark triggered → see the credited free bet held against
the account"), and the §5 end-of-day "use all the free bets"
cleanup. Confirmed the fix does NOT touch the EV column, the
odds-mirroring path, or settlement — the operator's highest risk
surface (map signals 3 & 4) is separate work. Operator confirmed
nothing missing from the Log Bet panel (select account +
account-at-book, confirm; stake pre-populates from the
race-screen promo selection — the F2-fixed promo→bet link), so
the brief stays tight to making the panel correct, no expansion.

**3. Live baseline probe (pre-flight grounding).** Before
drafting, re-confirmed the v3 repo hadn't moved since the review
(~18h earlier): HEAD `2329604`, 69 dirty entries, settlement SHA
`9e07a75d…` — all identical to the review's baseline. Spot-checked
the three live-defect anchors (racing.py:714, balance_derivation
.py:147, cash_flow_store_adapter.py:344) — all read exactly as
the review states. The line-number anchors are grounded-current.

**4. The FIX brief — DRAFTED + LOCKED + HANDED.**
`interface_triage/account_ref_format_class_fix_brief.md` (379
lines, 11 sections, surgical-fix shape per the S35/S36
precedent). Retype the three account refs UUID→str-verbatim at
every reviewed site (C1 cash_flow + adapter, C2
balance_derivation, C3 racing `/log-context`), flip the
F2-seeded dashed test fixtures to hex, add three mandatory FK-on
regression guards (incl. the operator's mark-triggered →
free-bet-credit → pool-shows-it scenario). A §5.0 baseline-drift
STOP gate is the one sanctioned mid-session stop. Hard limits:
settlement byte-identical, no schema change, spine-owned UUIDs
untouched, read-write only at named anchors, no git
state-changing ops, `uv run pytest`. The latent cash_flow sites
are retyped in the same pass (review §D condition 3 + the
operator's fix-once intent — the future transaction-import
writer would otherwise re-open the class).

**5. Code released.** Code's read-and-confirm gate came back
faithful — every site, the full spine-owned no-touch list, the
coupling, and the §5.0 stop gate restated accurately, no drift,
no misclassification. Brief stamped LOCKED + verified on disk;
the ready-to-paste Code prompt was provided.

## Standing-instruction adherence check

- **Cat 1 (lead with the call; plain language; escalate-to-
  detail flagged):** honoured — triage verdict led; the holistic
  cross-check was flagged "worth a bit of detail" before
  delivering.
- **Cat 1 (calls-made list at brief hand-off):** honoured — six
  calls surfaced as a numbered list for redirect.
- **Cat 2 (fenced-block ~60–70 char wraps):** honoured — brief +
  Code prompt hard-wrapped.
- **Cat 3 (Desktop Commander; verify every write; create_file
  banned; DB/anchor reads via start_process):** honoured — brief
  written chunked via DC write_file, verified on disk; baseline
  probe via start_process; line anchors confirmed.
- **Cat 4 (brief-drafting skill; ground "already built" claims;
  Code read-and-confirm gate):** honoured — skill ritual run;
  anchors grounded live; gate enforced before release.
- **Cat 5 (software calls are Claude's, made not punted):**
  honoured — combine-vs-split, latent-sites-in, guard design all
  made and stated; the one operator-call (panel completeness)
  surfaced and answered.

## Open items

Pointer-only — full detail in `current_state.md`.

**Closed in Session 186:**
- The account-ref surface review triage (S186 primary) — DONE,
  review confirmed sound. ✅
- The FIX brief — DRAFTED + LOCKED + HANDED, Code gate released.
  ✅

**New / promoted for Session 187:**
- **S187 primary: triage `account_ref_format_class_fix_report.md`
  — BUT only AFTER the operator confirms Code has finished its
  work** (operator directive at S186 close). S187 opens, runs the
  open ritual, then WAITS for that confirmation before triaging.
  Success = the ~10 known F-A read-path failures green, the three
  FK-on guards in place, settlement byte-identical, dirty list
  clean except named anchors.

**Carried to Session 187:**
- Pre-cutover live-validation sweep (operator-run) — after the
  account-ref class closes.
- Launcher brief (F9/F10 + F12 + rebuild-if-source-newer) —
  independent; parallel or after.
- Racing-API placings backfill + nightly results-sync fix — own
  brief; parallel, not a blocker.
- W16 cutover scoping (after the briefs land).
- Available secondary thread: `operator_workflow_map.md` redline
  + its §6 friction register driving a v2-refinement /
  next-iteration scoping pass.
- Parking-lot (unchanged): hedge-link on manual entry;
  bet-mutation-log viewer; Log Past Bet soft-books-only picker;
  in-app catalogue-management UI; `presets.ts` dead-code (F6);
  free-bet config-control cosmetics (F1); `…_instance_id`
  rename; partial free-bet draw-down; shared canonical
  account-ref type (post-cutover hardening, DR-030); Piece B
  (post-cutover).

**Carry-forward sensitivity flags:**
- **Bet-safety hard rule — CLEAN.** No code touched this session
  (Chat-only). The account-ref fix (when Code runs it) must hold
  the line: settlement byte-identical (`9e07a75d…`), no contact
  with `settlement.py` / `apply_manual_operator_resolution` /
  `provisional.py`; it only retypes promo-spine-adjacent +
  cash_flow + balance + racing reference fields. The brief's §9
  enforces this; the report must prove it.
- **finish-position gap does NOT touch live settlement** —
  confirmed S174, re-confirmed S179. Placings fix is analytics.
- **Manual entry + any capture.db read goes through `vps_client`**
  (DR-027/028); read-only.
- **v2 DB corruption** — confined to regenerable tables; betting
  data intact; jump-start-only to retirement.

## Session close state

- Rebuild folder root: clean, no phantom v2 files. New this
  session: `interface_triage/account_ref_format_class_fix_brief.md`
  (379 lines, LOCKED).
- current_state.md rotated to S186 close (2026-06-25 08:57 ACST).
- v3_build_picture.md UPDATED (the account-ref stream moved —
  review triaged → fix brief locked/handed); stamp bumped to
  2026-06-25 08:57 ACST. Interface-refinement row carries the
  S185-detour note + the S186 progression + the S187
  wait-then-triage next-milestone.
- standing_instructions.md unchanged this session (no new/edited
  instruction; the wait-for-confirm directive is session-specific
  forward routing, not a standing rule — lives in the opening
  prompt + current_state).
- .close_out_backups/: stale SESSION_186_opening_prompt.md
  removed; SESSION_187_opening_prompt.md written.

## Forward routing — CONFIRMED WITH OPERATOR

The operator's explicit close instruction: "On opening next
session, wait for my confirmation that Code has completed its
work, then triage the report." So S187 opens, runs the open
ritual, and then HOLDS — it does not assume the fix report
exists or that Code is done. Only on the operator's confirmation
does it triage `account_ref_format_class_fix_report.md`. On a
clean triage the account-reference format class CLOSES and the
promo-on-bet/credit-in arc is live-crediting-proven end-to-end,
clearing the run-up to the pre-cutover live-validation sweep →
launcher brief → W16 cutover scoping. The workflow-map redline +
friction-register design thread remains an available secondary.

---
*Session 186 record. Closed 2026-06-25 08:57 ACST.*
