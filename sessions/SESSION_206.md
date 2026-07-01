# SESSION 206

**Title:** DR-034 (canonical race-identity model) LOCKED from the §B
draft after an operator-requested cross-check against the placings
backfill; the fragment-floor measurement brief drafted + locked for
Code. Data Foundation arc advances; Brief 2 still gated.
**Opened:** 2026-06-30 11:38 ACST (headless runner; fast-path open —
runner developed §B + drafted DR-034, held for review).
**Closed:** 2026-06-30 12:10 ACST.
**Tool routing:** Chat throughout — governance writes (`decisions.md`
DR-034, `BETHUB_DATA_REFERENCE.md` §B flip) and brief authoring
(`placings_deficit_fragment_floor_brief.md`). Code commissioned
out-of-session for the fragment-floor measurement (not yet run).
**Governing DRs:** DR-034 (locked this session), DR-032 (Betfair
canonical reference), DR-033 (source-role split), DR-027/028 (two-DB +
single boundary), DR-021 (Adelaide anchors).

---

## Anchor
- Open (runner fast-path): 2026-06-30 11:38 ACST (runner result ran
  11:38:41, fresh vs S205 close 11:33). Close:
  `TZ="Australia/Adelaide" date` → 2026-06-30 12:10 ACST.
- Same-workday continuation of S205.

## Pre-flight checks
- Fast-path open: the S206 runner result was fresh (ran 11:38 > S205
  close 11:33); presented straight. Drift-check inherited clean.
- Close pre-flight: rebuild root clean; `.close_out_backups/` held only
  the consumed S206 prompt; the known `SESSION_9001` watcher-test
  artefact remains in `~/.bethub-cycle/results/` (operator-side delete,
  unchanged).

---

## Session shape

A governance-lock session. The runner opened S206 on its fast-path,
having already developed §B of `BETHUB_DATA_REFERENCE.md` and drafted
DR-034, held for operator review. The session was three strands: a
non-technical review of DR-034 for the operator; an operator-requested
cross-check of DR-034 against the recent VPS/backfill work (which
surfaced two real implications and produced one DR edit); and the lock
itself plus a follow-on measurement brief for Code. No code touched in
Chat; bet-safety clean throughout (read-only analytical / governance;
the live v2 earning path untouched).

## What was delivered

1. **DR-034 reviewed in plain language + approved.** Walked the operator
   through the five locked stances non-technically (Betfair WIN market =
   the race's true name; row-id banned as identity; completeness beats
   row-id; no-market races get a second-class analytics-only name;
   definition-not-build). Surfaced the one honest caveat: locking the DR
   does not itself clean up the 87% duplication — the collapse
   remediation is named roadmap, executed under its own future brief.

2. **Backfill cross-check (operator-requested).** Reviewed DR-034
   against `placings_landing_fix_report.md` (RC-1/RC-2) and
   `recovery_run_report.md`. Findings:
   - **Consistent, no rework forced.** The RC-2 write-side guard's rule
     ("match a result to a horse by identity, never the bare saddlecloth
     number") is the runner-level instance of DR-034's governing
     principle (within-scope ordinals are not cross-scope identities).
     DR-034 ratifies the principle the VPS work already applied.
   - **Implication 1 (the one to watch):** the backfill lands finishing
     positions on natural-key fragments via the subscription path; many
     are not market-stamped, so a placing can land correctly yet sit on
     a different fragment from the Betfair spine. Two consequences —
     (a) those placings aren't spine-reachable until the fragment-
     collapse remediation runs; (b) a fragment-floor of permanently-NULL
     duplicate runners may inflate the recovery deficit and read as a
     stall when the race is in fact resulted on a sibling.
   - **Implication 2 (design continuity):** the eventual cross-source
     runner merge must reconcile Racing-API horses (name) against
     Betfair runners (selection_id) with no shared id — name-matching is
     the only bridge, and the landing fix's `robust_name_match_key` is
     already that bridge. Carried into §C/§D, no operator decision.

3. **DR-034 LOCKED.** Written to `decisions.md` as the canonical record
   (house format); `BETHUB_DATA_REFERENCE.md` §B flipped DRAFT→LIVE with
   every draft marker cleared (header, §B status blockquote, §B.8 header
   + body, doc-header governing-DR line, footer). The placings-backfill
   dependency from the cross-check folded into DR-034 stance 4 and the
   cross-references (landing-fix + recovery reports named). The
   `race_date_semantics` §H archive stays pending (also feeds §D, still
   scaffold) — correct per the supersede rule.

4. **Fragment-floor measurement brief DRAFTED + LOCKED** for Code
   (`placings_deficit_fragment_floor_brief.md`, rebuild root, 11
   sections, read-only). Decomposes the live recoverable deficit
   (~41,340) into **ghost** (race resulted on a sibling fragment —
   un-fillable) vs **genuine** (truly recoverable). Market-stamped
   regime precise (§5.3); no-market regime ranged with an explicit error
   bar (§5.4, Fix-5 build forbidden); cross-source-pattern confirmation
   (§5.5); decomposition must reconcile to the baseline. Hard limits:
   no fix / no collapse / no schema / no writes / no git / mode=ro /
   never copy the DB. The ready-to-paste Code prompt was provided to the
   operator. Operator delegated the brief review ("not technical") —
   locked on delegation per the Session 35/36 tightly-anchored-brief
   precedent.

## Standing-instruction adherence check

- **Tool routing stated explicitly** (Cat — every handoff named Chat vs
  Code with reason). ✅
- **DB reads** — none needed this session (governance + brief only); the
  brief itself mandates `mode=ro` + never-copy for Code. ✅
- **Brief drafting** — surfaced only the operator-facing strategic calls
  (regime precision split, measurement-only, recoverable-window target);
  technical detail (SQL shape, column anchors) handled inside the
  artefact. ✅
- **Fenced content** — narrow wraps held in the Code prompt block. ✅
- **Session close** — opening prompt produced for S207 with a confirmed
  (gated) first action. ✅
- **No new standing instruction surfaced** this session; no
  `standing_instructions.md` edit. Skill bodies unchanged.

---

## Open items

Pointer-only — full detail in `current_state.md`.

**New / changed in S206:**
- **DR-034 LOCKED** — canonical race-identity model in `decisions.md`;
  §B of `BETHUB_DATA_REFERENCE.md` LIVE. (Was: pending/drafted.)
- **Fragment-floor measurement brief** — locked, staged for Code
  (`placings_deficit_fragment_floor_brief.md`); report not yet produced.
- **Backfill ghost-deficit finding** — the recovery deficit may carry a
  permanent fragment-floor; quantified by the above brief; informs the
  burndown read + stall-alert threshold.

**Carried to S207:**
- Brief 2 (`vps_client_api_rewrite_brief.md`) — still HELD + GATED behind
  the identity decision; DR-034 now lands as its input (re-lock against
  the locked identity).
- The Data Foundation arc sequence after DR-034: §A.4 field harvest →
  §C/§D/§E (storage, ingest, fitness) → roadmap + supersede.
- The fragment-collapse remediation (DR-034 stance-4 read-time union /
  write-time enforcement) — a future brief, sized by the fragment-floor
  report.
- Cash-modal blank fix; settlement-worker; promo-seed; W16 cutover.
- Recovery monitoring (daily checks; first clean point 1 Jul).
- Parking-lot items (see `current_state.md`).

**Open items out (closed in S206):**
- DR-034 review + lock decision. ✅
- The backfill cross-check the operator requested. ✅

## Session close state
- Rebuild folder root: clean; DR-034 in `decisions.md`,
  `BETHUB_DATA_REFERENCE.md` §B LIVE, `placings_deficit_fragment_floor_
  brief.md` added (locked).
- `current_state.md`: rotated to S206 close.
- `v3_build_picture.md`: Data Foundation stream advanced (DR-034 locked);
  "Last updated" bumped to this close.
- `.close_out_backups/`: S207 opening prompt written; consumed S206
  prompt removed.
- `sessions/`: SESSION_206.md written.

## Forward routing

**Confirmed with operator.** S207 first action = **AUTO-TRIAGE the
fragment-floor report, GATED on Code being finished**: if
`placings_deficit_fragment_floor_report.md` exists and is complete →
auto-run triage on open (no confirmation gate); if it is missing or
partial → **HOLD**, do not triage, and tell the operator Code hasn't
finished. (Operator instruction this session: "triage as auto-action
unless Code is not finished yet.") After triage: digest the ghost-vs-
genuine split → decide whether the stall threshold / burndown read needs
adjusting → then the Data Foundation arc continues (§A.4 → §C/§D/§E) and
Brief 2 re-locks against DR-034.
