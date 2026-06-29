# Session 178 — Brief 3 reframed: promo-on-bet gap surfaced; read-only review brief locked + handed to Code; design-lock governance lesson captured

**Opened:** 2026-06-23 14:58 ACST
**Closed:** 2026-06-23 16:19 ACST
**Duration:** ~1h21m, single calendar day. Same-workday continuation
of S177 (closed 14:49 ACST; S178 opened 14:58, 9 min later).
**Tool routing:** Claude Chat (planning + brief drafting) + Desktop
Commander (governance reads/writes; v3 + v2 source grounding via
`start_process` greps). No DB access. No Code session this session —
the review brief is handed to Code for an out-of-session run.
**Governing DRs invoked:** DR-021 (anchors), DR-032 (Betfair canonical
/ the `promo_instance_id`-on-bet link — documented-but-unbuilt, the
crux this session), DR-019 (derived P&L on read), DR-030 (module
layering), DR-027/028 (cross-DB boundary — the placings/capture.db
read in the settlement read-back), DR-033 (data-source roles —
placings come from the Racing API analytical line).

---

## Anchor

- Open: `2026-06-23 14:58 ACST` (session-open ritual; same-workday
  continuation of S177's 14:49 close).
- Close: `TZ="Australia/Adelaide" date` → `2026-06-23 16:19 ACST`.

## Pre-flight checks

Open ritual ran clean: drift-check passed (current_state ↔
SESSION_177 ↔ v3_build_picture all matched the 14:49 S177 close);
`.close_out_backups/` held only the S178 opening prompt; rebuild root
clean. Required reads completed in order (current_state,
standing_instructions in full, project_context, SESSION_177, the S168
`free_bet_credit_in_design.md`). Same-workday tight recap; build
picture + open-items delta skipped as ritual noise on a 9-min
continuation.

## Session shape

Opened to draft brief 3 (free-bet credit-in). The `bethub-brief-
drafting` skill fired and its Step 2 grounding pass turned the session
— instead of drafting straight off the locked S168 design, grounding
the design's anchors against the live v3 code surfaced that a
load-bearing premise was false. That reframed the whole piece: from
"draft a build brief" to "the design assumed a substrate that isn't
built — re-scope, then de-risk with a read-only review first." The
session became: surface the gap → settle the operator's routing →
draft + lock a read-only Code review brief → capture the governance
lesson. No build, no Code run this session.

## What was delivered

1. **The promo-on-bet gap surfaced (the crux).** The S168 design
   (`free_bet_credit_in_design.md`) assumes the qualifier is "logged
   with its promo attached — mostly already built." Grounding showed
   that's false. The race-screen promo buttons are **EV presets**
   (`ui/web/src/promos/presets.ts`, 10 presets ported from v2; drive
   the Promo EV column + pre-fill only). A logged bet persists
   `strategy_tag` (4-value) + one `promo_ev_at_log` number — **not**
   which specific promo (insured spots, FB-vs-cash, cap). The DR-032
   `bets.promo_instance_id` link is documented in `domain/promos`
   ("when present") but there is **no column on the bet and no
   persistence path**. So a triggered free-bet credit — whose payload
   requires `triggering_promo_instance_id` — has nothing to point at.

2. **Operator routing locked: full promo-on-bet build, single-level.**
   The operator rejected the minimal option (credit points at the
   qualifier bet only) on operational grounds — in a burst, you'd
   hand-check every settled qualifier to get its credit in, and the
   free bets are spent before you reconcile. The v2-proven pattern is
   to attach the promo's terms to each bet. **Single-level** model
   (operator's own framing, confirmed correct + simpler): one
   promo-type reference table, each row a serial with its terms; the
   bet stores the serial; settlement reads it back. The two-level
   "instance" idea collapsed — book is already on the bet, and promos
   mature at the event (no run-window to model). Changed terms = a
   different preset = a different type, handled at the type level.

3. **v2 = requirements reference, not code source.** v2 is read to
   lift the term-set + the "placed in the insured spots → refund this"
   rule that worked in production. Not to port engineering — escaping
   v2's bet-schema + promo-vocabulary debt is the whole point of v3.
   v2 answers *what*; v3 decides *how*. (Same path the presets took.)

4. **Read-only review brief drafted + LOCKED + handed to Code.**
   `interface_triage/promo_attach_credit_in_review_brief.md` (259
   lines). The BetLog de-risk pattern (S170): map what exists vs
   what's needed and size the build, building nothing, then draft the
   build off grounded findings. Seven review areas: (1) the promo
   reference table + whether the presets can seed it; (2) writing the
   promo onto the bet at log (both entry paths; the bet-schema touch);
   (3) reading it back at settlement (kept strictly off the
   bet-safety settlement path; leans on the placings backfill); (4)
   the credit-in write + cycle link (incl. what satisfies the
   `triggering_promo_instance_id` requirement under the single-level
   model); (5) the two "placed?" confirm surfaces (BetLog scaffold +
   Log Past Bet); (6) overall buildable read + one-vs-two split; (7)
   **open findings** — operator-requested latitude for Code to flag
   anything else worth attention. Ready-to-paste Code prompt provided
   (read-and-confirm gate, read-only discipline, stop condition).

5. **Governance lesson captured (new Cat 4 standing instruction).**
   The S168 design locked on "mostly already built" without grounding
   it against the code; the gap surfaced ~10 sessions later, at
   brief-draft, only because the brief skill forces grounding. New
   standing instruction: ground "already built" claims empirically
   *before* locking a design that leans on them. Added to
   `standing_instructions.md` Cat 4 (Governance discipline), tagged
   S178. The architecture side held — DR-032 named the field as a
   deliberate deferral; it's the design-lock gate that needed
   tightening, not the architecture.

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open 14:58 + close 16:19 ACST. ✓
- **Silent session-open (Cat 1):** steps 1–5 silent; same-workday
  tight recap; build picture + open-items delta skipped (9-min
  continuation, ritual noise). ✓
- **Pre-flight grounding before brief drafting (brief skill Step 2):**
  ran the v3/v2 source grounding that caught the promo-on-bet gap —
  the single highest-value act of the session. ✓
- **Make-the-call / don't punt (Cat 5):** offered minimal/pick/full
  with a recommendation; operator overrode on operational grounds —
  the division of labour working as designed. Own-the-miss recorded
  (minimal under-weighted bursts; "no screen" was imprecise). ✓
- **Plain-language / brevity / lead-with-the-call (Cat 1):** flagged
  "deserves a little detail" before the longer governance/scoping
  turns; otherwise tight. ✓
- **Code session prompt at hand-off (Cat 2, S163):** ready-to-paste
  Code prompt provided with the review brief. ✓
- **`create_file` banned / verify every write (Cat 3):** brief +
  session record + all close writes via `Desktop Commander:write_file`;
  brief verified (259 lines, 7 areas); close writes verified at Step
  11. ✓
- **Empirical verification before editing governance artefacts (Cat
  3):** re-read current_state / SESSION_177 / v3_build_picture /
  standing_instructions live before editing at close. ✓
- **NEW Cat 4 instruction authored this session:** ground "already
  built" claims before locking a design. Applied to
  `standing_instructions.md` during close per operator request;
  re-upload to the Project knowledge base flagged. Not a Cat 1/2 edit
  → no session-open/close skill review triggered.

## Open items

Pointer-only — full live list in `current_state.md`.

## Open items out (closed / resolved S178)

- **Draft brief 3 (free-bet credit-in)** — REFRAMED, not closed: the
  build brief is deferred behind a read-only review. The review brief
  is drafted + locked + handed to Code. ✅ (as reframed)
- **The S168 "mostly already built" premise** — RESOLVED: empirically
  false; promo-on-bet persistence is unbuilt; full build routed. ✅

## New items in (S178)

- **Run the Code review session** (operator-side) for
  `promo_attach_credit_in_review_brief.md` → produces
  `promo_attach_credit_in_review_report.md`.
- **Re-upload `standing_instructions.md`** to the bethub-rebuild
  Claude Project knowledge base (new Cat 4 instruction added).
- **S179 triages the review report + scopes the build** — confirm
  single-level promo table; decide one-build-vs-two (likely
  promo-attach foundation → credit-in + cycle link); sequence against
  the placings-backfill fix.

## Session close state

- **Rebuild root:** clean, no new files at root. No phantom files.
- **`interface_triage/`:** 1 new file —
  `promo_attach_credit_in_review_brief.md` (259 lines, locked S178;
  the read-only Code review brief, handed to Code).
- **`current_state.md`:** rotated to S178 close (16:19 ACST);
  Where-we-are = promo-on-bet gap surfaced, review brief locked +
  handed to Code; What's-next = S179 triages the review report +
  scopes the build.
- **`v3_build_picture.md`:** Interface-refinement stream next-milestone
  moved (audit-log "TRIAGED CLEAN" → "brief 3 reframed: promo-on-bet +
  credit-in read-only review brief LOCKED + handed to Code; build
  scoped next session off Code's findings"); updated + timestamp
  bumped.
- **`standing_instructions.md`:** EDITED — one new Cat 4 (Governance
  discipline) instruction added (ground "already built" claims before
  locking a design). Re-upload to Project KB flagged.
- **`.close_out_backups/`:** `SESSION_179_opening_prompt.md` written;
  stale `SESSION_178_opening_prompt.md` removed.
- **Operator-side actions flagged:** (a) run the Code review session;
  (b) re-upload `standing_instructions.md` to the Project KB; (c)
  carry-overs below.

## Forward routing (confirmed with operator)

Operator confirmed close and the forward path. **S179 triages Code's
`promo_attach_credit_in_review_report.md`** once the operator has run
the out-of-session Code review, then **scopes the build** off the
findings — confirm the single-level promo-type table, decide
one-build-vs-two (likely a promo-attach foundation brief, then a
credit-in + cycle-link brief), and sequence it against the
**Racing-API placings backfill + nightly results-sync fix** (its own
Code brief; DR-027/028 re-read trigger, VPS-side write) — that fix is
what actually lights up the burst relief (auto-surfacing earned
credits instead of hand-checking). Post-build sequence unchanged
behind it: launcher brief (F9/F10 + F12 + rebuild-if-source-newer) →
W16 cutover scoping. Forward routing confirmed.
