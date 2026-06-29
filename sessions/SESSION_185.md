# Session 185 — operator workflow map (insurance + free-bet conversion); a break from dev work

**Opened:** 2026-06-24 14:58 ACST.
**Closed:** 2026-06-25 07:20 ACST (the session spanned a pause
across local midnight — a multi-day session per the Cat 2 rule;
close re-anchored on actual close time).
**Tool routing:** Claude Chat only — workflow elicitation
(operator-domain) + governance-artefact authoring via Desktop
Commander. No Claude Code commissioned this session.
**Governing DRs:** DR-021 (Adelaide time). The workflow content
rests on the four-strategy framing (Strategy 1 Safety Net) +
DR-033 (data-source roles — Betfair operational, Racing API
analytical, placings a manual flag), not a build DR.

---

## Anchor

- Open anchor: `TZ="Australia/Adelaide" date` → 2026-06-24
  14:58 ACST.
- Close anchor: same command → 2026-06-25 07:20 ACST.
- Same-workday open (12 min after the S184 close); the session
  then paused and resumed the next morning before close. Close
  re-anchored on real close time per the multi-day rule.

## Pre-flight checks (S185 open)

Clean open, no anomalies. Drift-check passed: current_state,
SESSION_184, and v3_build_picture all carried the 2026-06-24
14:46 ACST S184-close stamp. Folder root clean, no phantom
files. Both conditional renders (build picture, open-items
delta) skipped — nothing had moved in the 12 minutes since the
S184 close.

## Session shape

A deliberate break from dev work, operator-set. Rather than
triage or build, the session mapped the operator's actual
betting workflow at the activity level — the minutiae of what
the operator physically does on a bet day — to feed v2
refinement and next-iteration design. Pure elicitation +
governance-artefact authoring. The session opened on the
operator's verbatim workflow question (carried in from the S184
close), ran an extended back-and-forth to surface the real
operational detail and its corrections, then assembled the
result into a new governance artefact.

## What was delivered

**1. operator_workflow_map.md — new governance artefact (root,
269 lines).** A map of the current real betting workflow at the
activity level, scope A (Strategy 1 Safety Net insurance,
2nd/3rd refund variant + the free-bet conversion cycle — ~95% of
the current operation). Six sections: what-this-is/scope; the
bet-day shape (the "cheapest next move" routing model + physical
setup + the AdsPower switch gate); core cycle 1 (the insurance
back-bet loop, unhedged); core cycle 2 (the free-bet conversion
loop, where all insurance-strategy lays live); cross-cutting
layers (the single mode-selected EV column, per-race promo prep,
lagged settlement, account health, scheduling, end-of-day
cleanup); and a friction & design-signal register. Operator
confirmed scope A and the root filing as a governance artefact.

**2. The operational model the elicitation surfaced.** Forced
serial by infrastructure (one IP at a time → AdsPower accounts
worked one at a time with a switch cost between), parallel
opportunity, fixed clock; no account order — continuous
re-solving of the cheapest next move; the phone is the one
parallel lane (own-name account). The insurance back-bet loop is
UNHEDGED (the operator wants the win; the 2nd/3rd refund is the
safety net, not a hedge) — a correction to the S185-open
assumption. Lays live ONLY in the free-bet conversion loop (plus
rare non-promo turnover offsets and rare boosted-winnings/odds
lays, both out of scope here). The conversion hinge is "mark bet
triggered → tool credits the free bet to the account."

**3. The single EV column (corrected mid-session).** There is
ONE EV column on the race page; the promo buttons at the top are
a mode selector — Free Bet → conversion EV, Insurance 2nd/3rd →
insurance EV — the same column recomputing for whatever promo is
applied. It is the decision surface for every promo type, which
is why total trust in it makes calculation correctness the
highest-stakes thing in the tool.

**4. Five design signals captured (§6 of the artefact).** (a)
AdsPower-switch cost dominates routing; (b) open cycles must be
held by the tool, not the operator's head (settlement/refund
checking is lagged, sometimes to next day); (c) manual
odds-mirroring is the hidden risk surface — hand-copying
shifting soft-book odds into the race page during a burst is
where wrong-runner / wrong-odds errors are born, UPSTREAM of the
EV the operator fully trusts; (d) the EV number carries the
whole operation; (e) promo scheduling lives in the operator's
head (named to move into the tool). Plus the named manual
re-entry points (odds-mirroring pre-bet, Log Bet post-bet,
late-entry fallback) and parked future-relief items
(auto-placing/settlement, tool-side promo scheduling).

## Standing-instruction adherence check

- **Cat 1 (lead with the call; plain operational language):**
  honoured — the elicitation stayed in real-world gambling
  language; software kept concept-level per the operator's ask.
- **Cat 1 (propose structure, start writing, bring for
  review):** honoured — proposed the map structure, operator
  agreed, then drafted.
- **Cat 1 (call-driven surfacing in artefact drafting):**
  honoured — only genuine calls surfaced (scope A vs B; filing
  as a governance artefact; the two corrections). The rest
  authored autonomously.
- **Cat 2 (fenced-block ~60–70 char wraps):** honoured — the
  artefact is hard-wrapped to house style.
- **Cat 5 (operational questions are the operator's):**
  honoured — the workflow was treated as operator ground-truth,
  offered as Claude's model for redline, never asserted.
- **Cat 3 (Desktop Commander; verify every write; create_file
  banned):** honoured — artefact written via DC write_file
  chunked ≤30 lines, verified on disk.
- **Cat 3 (DB read discipline):** not exercised — no DB reads.
- **Cat 4 (Drive sync — do not prompt at close):** honoured.

## Open items

Pointer-only — full detail in current_state.md.

**Closed in Session 185:**
- The operator workflow question (S185 primary) — ANSWERED +
  assembled into operator_workflow_map.md (scope A). ✅

**New this session:**
- operator_workflow_map.md exists (root). Open for operator
  redline (between-session). Optional KB upload when design work
  picks up.
- The friction & design-signal register (§6) is now available to
  drive a v2 refinement pass or next-iteration scoping — an
  operator-choice thread, not yet committed.

**Carried to Session 186:**
- **Triage account_ref_surface_review_report.md** — the report
  is now PRESENT in interface_triage (Code has run the read-only
  review). S186's primary: triage it — confirm the surface is
  complete and the approach/altitude sound, then draft the FIX
  brief against the verified surface ("close the
  account-reference format class"). If the review trips an
  escalation trigger (frontend / schema / shared-type-now),
  that's the operator's call before the fix locks.
- Pre-cutover live-validation sweep (operator-run) — after the
  account-ref class closes.
- Launcher brief (F9/F10 + F12) — independent; parallel or after.
- Racing-API placings backfill + nightly results-sync fix — own
  brief; parallel, not a blocker.
- W16 cutover scoping (after the briefs land).
- Parking-lot (unchanged): hedge-link on manual entry;
  bet-mutation-log viewer; Log Past Bet soft-books-only picker;
  in-app catalogue-management UI; presets.ts dead-code (F6);
  free-bet config-control cosmetics (F1); …_instance_id rename;
  partial free-bet draw-down; Piece B (post-cutover).

**No build stream moved this session** (workflow-mapping detour)
— v3_build_picture.md intentionally NOT updated; its stamp
correctly predates this close. Not drift.

## Session close state

- Rebuild folder root: clean, no phantom v2 files. New this
  session: operator_workflow_map.md (root, 269 lines).
- account_ref_surface_review_report.md confirmed PRESENT in
  interface_triage (Code ran the read-only review
  out-of-session).
- current_state.md rotated to S185 close (2026-06-25 07:20
  ACST).
- v3_build_picture.md NOT updated (no build stream moved); stamp
  remains 2026-06-24 14:46 ACST. Correct, not drift.
- standing_instructions.md unchanged this session.
- .close_out_backups/: stale SESSION_185_opening_prompt.md
  removed; SESSION_186_opening_prompt.md written.

## Forward routing — CONFIRMED WITH OPERATOR

The operator framed S185 explicitly as "a quick break from dev
work," so the dev arc resumes at S186. With
account_ref_surface_review_report.md now present, S186's primary
is the carried review-report triage → on a clean review, the FIX
brief against the verified surface; on an escalation trigger, the
operator's call first. This routing is the documented carry
(confirmed across S184→S185). The workflow map (redline + the
optional friction-register-driven design work) is surfaced as an
available secondary thread the operator can pick up at S186 open
if they choose, before resuming the cutover run-up.

---
*Session 185 record. Closed 2026-06-25 07:20 ACST.*
