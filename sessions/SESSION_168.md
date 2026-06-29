# Session 168

**Title:** Free-bet pool design pass — cycle-capture
reframed into Piece 0 + A (credit-in + cycle attribution)

**Opened:** 2026-06-19 16:03 ACST
**Closed:** 2026-06-20 08:14 ACST (day-rollover; see shape)
**Tool routing:** Claude Chat (planning, review triage,
pre-code design pass, artefact drafting) + one
out-of-session Claude Code read-only review.
**Governing DRs:** DR-021 (timestamps), DR-022 (vocab),
DR-027/028 (two-DB boundary), DR-030 (module boundaries),
DR-031 (tech stack), DR-032 (Betfair canonical / cycle
axis), DR-013 (DB read discipline). Plus the **Session 70
free-bet pool lock** as the design substrate.

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
  → `2026-06-19 16:03 ACST`
- Close: same command → `2026-06-20 08:14 ACST`

## Pre-flight checks (open ritual)

Drift-check clean: `current_state.md`, `SESSION_167.md`,
and `v3_build_picture.md` all stamped 2026-06-19 13:36
ACST (S167 close). `.close_out_backups/` held only
`SESSION_168_opening_prompt.md` — no stale prior prompt
(the S166 miss did not recur). No phantom files at root.
Same-workday open (S167 closed 13:36, S168 opened 16:03).

## Session shape

A design-discovery session that diverged productively from
its plan. S168 opened to draft the cycle-capture brief
(the S168 primary). Drafting the link affordance, the
operator asked whether linking a triggered free bet to its
qualifier could be automated. That question opened the
**free-bet pool foundation**: the operator's free bets are
a pool (Session 70 lock), and the real question was no
longer "wire a link" but "how much of the pool model is
built, and what does the rest cost."

Rather than draft a build brief blind, the session
commissioned a **read-only Code review** of the free-bet
pool + settlement layer. The review's headline reframed
everything: **no production code path creates a free-bet
credit anywhere** — the pool can be drawn down but nothing
fills it up ("Bucket 0"). The session triaged that into a
three-piece shape (0 credit-in → A cycle attribution → B
timing tolerance), then ran a **full pre-code design
pass** landing a locked credit-in design, grounded against
the v2 precedent (which used exactly the operator-confirmed
trigger flow and made insurance its dominant free-bet
source).

Net: the originally-planned cycle-capture brief was
**reframed** into Piece 0 + A; its build brief is the S169
deliverable, drafted against the locked design note. The
launcher brief was untouched. Close crossed local midnight
(day-rollover split trigger) — clean close, no extra work
layered on; the design note had already been committed as
substantive work mid-session.

## What was delivered

1. **`interface_triage/free_bet_pool_review_brief.md`**
   (331 lines) — read-only review brief, drafted via the
   brief-drafting skill and handed to Code. Three review
   areas (settlement-today; pool model wired-vs-missing;
   effort split into buckets), the Session 70 locked model
   inlined for Code, full read-only hard limits. Code
   restated and confirmed the gate before running.

2. **`interface_triage/free_bet_pool_review_report.md`**
   (Code's output, ~348 lines) — the review. Headline: the
   free-bet **read** side is built (pooled balance,
   inventory, deploy), the **write/credit** side is not.
   No production path creates a `free_bet_credited` event.
   Settlement (1,354 lines) touches the promo layer in
   zero places — a settled qualifier does not auto-credit
   a free bet. Five-piece map: pooled balance BUILT;
   credit→qualifier link PARTIAL (modelled, unreachable —
   no write path); oldest-first drawdown + auto cycle
   attribution MISSING; discrete flag MISSING; deploy
   surface PARTIAL (per-credit checkboxes, not pool-draw).

3. **Review triage** — reshaped the work into three
   pieces: Piece 0 (credit-in, the hidden prerequisite),
   Piece A (cycle attribution, ~1 session, moderate risk),
   Piece B (timing tolerance, 2–3 sessions, HIGH risk,
   settlement-adjacent). Operator locked **0 + A
   pre-cutover, B as its own slice after**.

4. **Pre-code design pass** — locked the credit-in
   approach through several operator calls:
   - Credit creation is **derived** from the settled
     qualifier + its attached promo, not a manual "free
     bet triggered" declaration.
   - Placing source = **operator confirmation at settle**
     (option 1): the win/lose feed can't see placing, so
     for a non-winning insurance qualifier the operator
     answers one "placed?" yes/no — the proven v2 flow.
     Auto-placing detection deferred to Piece B.
   - Consumption order = **FIFO (oldest-earned first)**;
     expiry isn't tracked and won't be pre-cutover.
     Returns to the Session 70 lock.
   - **Whole-credit consumption only** for cutover;
     partial deferred (noted as the better future system).
   - Free-bet **amount defaults to the qualifier's stake**
     (capped); v3 stores promo terms free-form, so no
     structured-terms modelling pre-cutover.
   - **Safety seam:** credit-write reads settled output;
     it does NOT modify the settlement engine internals —
     keeps Piece 0 out of the bet-safety zone.

5. **`interface_triage/free_bet_credit_in_design.md`**
   (127 lines) — the locked design note. The spec the
   Piece 0 + A build brief is drafted against. Captures
   the flow, the safety seam, drawdown rules, edge cases,
   what's deferred to B, and a governance note.

6. **v2 precedent confirmed** via read-only DB inspection
   (`bethub-v2/data/bethub.db`, `start_process` Python,
   not copied). v2's `bets` carried `promo_insured_
   positions` + a `promo_triggered` flag; result was only
   W/L, so the operator supplied the placing. Insurance
   was the dominant free-bet source — **226 deployed** vs
   a handful of freebies/signups. Confirms option 1 is the
   proven flow, not a new bet.

## Standing-instruction adherence check

- **Cat 1 (call-driven surfacing, brevity):** honoured.
  Only operator-facing calls were surfaced (placing
  source, FIFO vs expiry, whole vs partial, now-vs-later
  sequencing); all technical detail led autonomously.
  Detail escalated only at genuine decision points
  ("deserves detail" flagged). Build picture rendered
  inline at open.
- **Cat 2 (session protocol):** timestamps anchored open
  + close (DR-021). Session record written. Opening prompt
  generated at close without being asked. Day-rollover
  split trigger respected (clean close, no layered work).
- **Cat 3 (filesystem + skills):** Desktop Commander used
  exclusively; `bash_tool` not touched. `bethub-session-
  open`, `bethub-brief-drafting`, `bethub-session-close`
  skills each read before use. Writes chunked + verified.
- **Cat 5 (tool routing):** every hand-off named its tool
  with reason (review → Code read-only; build brief →
  Chat-drafted then Code). Dev-lead calls made
  autonomously; only operator-territory calls surfaced.
- **DR-013 (DB read discipline):** v2 DB read via
  `start_process` Python at the canonical path, never
  copied.
- **Google Drive auto-sync:** not prompted at close (per
  standing instruction — Drive auto-syncs the folder).

## Open items

Pointer-only — full detail in `current_state.md`.

**Promoted for Session 169:**
- Draft the **Piece 0 + A build brief** for Code, against
  `free_bet_credit_in_design.md`. S169 primary.

**Carried:**
- **Launcher brief** (F9 throttle-to-disk + F10 port
  override, consider F12) — untouched this session, still
  pending.
- Governance: decide whether to formalise the credit-in
  design as a short DR or a Session 70 amendment —
  operator's call, deferred.
- Parking-lot items (unchanged) — see `current_state.md`.

## Open items out

- **Cycle-capture brief (as originally scoped)** —
  superseded. The records-look-based "link affordance +
  manual realised-conversion" framing was reframed by the
  pool review into Piece 0 + A. The realised-conversion
  manual entry is now part of the same credit-in design
  (the credit carries the conversion basis). ✅
- **Free-bet pool review** — commissioned, run, triaged. ✅
- **Pre-code design pass for credit-in** — complete,
  locked, captured. ✅

## Session close state

- Rebuild folder root: clean, no phantom files.
- `interface_triage/`: three new files this session
  (review brief, review report, design note).
- `standing_instructions.md`: untouched this session (no
  new instructions surfaced). KB re-upload still pending
  operator-side (carried from S163 — unchanged).
- `v3_build_picture.md`: updated at this close (Interface
  refinement stream's milestone moved — cycle-capture →
  Piece 0 + A credit-in build).
- `.close_out_backups/`: holds `SESSION_169_opening_
  prompt.md` after this close.

## Forward routing

**S169 drafts the Piece 0 + A build brief** for Code,
against the locked `free_bet_credit_in_design.md`. Then
the launcher brief remains the other pre-cutover drafting
job. **Confirmed with operator** — the operator endorsed
closing here and taking the build brief fresh next session
(clean split point; the brief deserves deliberate drafting
since Piece 0 reaches the credit-write). Governance
formalisation of the design is deferred to the operator's
discretion.
