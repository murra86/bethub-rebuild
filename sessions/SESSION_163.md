# Session 163

**Title:** customerRef 503 — surgical draft redirected to a
read-only impact review, triaged, and locked as the Option B
(decouple, schema-less) fix brief.
**Opened:** 2026-06-18 15:53 ACST
**Closed:** 2026-06-18 19:17 ACST
**Tool routing:** Claude Chat (planning, scoping, triage,
governance). Two Code commissions produced (review brief executed
this session; fix brief v2 locked for next-session execution).
**Governing DRs:** DR-029 §2.4 (Betfair Streaming), DR-032
(Betfair canonical reference layer + auto-login), DR-021
(timestamp anchoring), DR-030 (v3 module boundaries — import
linter), DR-013 (DB read discipline).

---

## Anchor

- Open: `TZ=Australia/Adelaide date` → 2026-06-18 15:53 ACST.
- Close: `TZ=Australia/Adelaide date` → 2026-06-18 19:17 ACST.

Note: the session ran across the original S163 chat (which
stalled mid-draft of the impact-review brief at ~18:19) and a
continuation chat that completed the review brief, triaged Code's
report, and locked the fix brief. One logical session, two chats.

## Pre-flight checks

Original S163 open ran the full ritual clean (drift-check passed,
current_state/SESSION_162/build-picture all stamped 15:43 at S162
close; root clean). The continuation chat re-grounded against the
live tree (read the brief-drafting and session-close skills, the
dr029/2_4_betfair_streaming/ folder, and the impact report) rather
than re-running the open ritual.

## Session shape

A pivot session. It opened on *the fix* for the S162-named
customerRef 503 and was expected to scope-and-commission a
surgical patch. The operator's caution — "are we sure we're not
fixing one thing and breaking another?" — redirected a drafted
surgical brief into a read-only impact-and-design review before
any code change. That instinct was vindicated: tracing found the
surgical brief genuinely under-scoped (one of two placement
sites, unverified consumer assumptions). The review then produced
the decisive finding, the operator took the decouple decision on
that evidence, and the session closed with the real fix brief
locked and its Code prompt ready.

## What was delivered

1. **`customer_ref_fix_brief.md` (v1 surgical draft) — written,
   then SUPERSEDED.** The original S163 surgical brief (445 lines,
   close-the-class on the ref + strategy-4 tag). On grounding it
   was found to patch only the racing lay route and to rest on
   unverified assumptions about downstream consumers. Retained on
   disk as *input* to the review, not for execution.

2. **`customer_ref_impact_review_brief.md` — read-only review
   brief, completed.** §1–§5.2 drafted in the original S163 chat
   (stamped 18:24, stalled there); §5.3–§11 completed in the
   continuation chat. 362 lines, sha256 `b75e2a4a`. Commissions a
   no-code-change map of four identifiers (`bet_id`,
   `customer_order_ref`, `customerRef`, `customer_strategy_ref`)
   across generation, Betfair-bound consumption, read-back /
   reconciliation, internal consumers, plus a neutral two-option
   (unify vs decouple) design analysis.

3. **`customer_ref_impact_review_report.md` — Code executed the
   review.** Read-only, bethub-v3 untouched (suite 61, no git
   mutation, schema-from-source). **Headline finding:** no
   downstream consumer depends on the outbound reference's value,
   format, or length — reconciliation keys off
   `bets.betfair_bet_id`, settlement off `betfair_selection_id`,
   and the only `StrategyTag` reconstruction is from v3's own DB
   column. Consequences: the two fix options do **not** collapse
   into a forced decouple, and Option B needs **no schema change**
   (its reconciliation rationale is already met by the existing
   `betfair_bet_id` column). Also surfaced: a pre-existing latent
   bug — the 47-char ids already fail the `_coerce_uuid` /
   `_safe_uuid` parsers and fall back to a random UUID, degrading
   free-bet-deploy correlation today.

4. **Decision — Option B (decouple), schema-less form.** The
   operator's call on the review evidence ("you're the dev lead,
   go for it" — delegated after the A/B trade was surfaced).
   `bet_id` keeps its natural form; a dedicated ≤32 reference is
   minted for Betfair; no new column, no migration.

5. **`customer_ref_fix_brief_v2.md` — the locked fix brief.** 356
   lines, sha256 `bf59638b`. Supersedes v1. Four anchored changes
   (unify lay `bet_id` to clean canonical form; mint a ≤32 ref at
   *both* placement sites via one shared helper, reused across
   retries; boundary-map the strategy tag to ≤15; install a
   client-side length guard that raises, not truncates), plus
   tests. Schema-less, dirty-tree discipline (no git mutation,
   anchors re-grounded by grep), bet-safety gate fenced. Live $5
   lay named as the operator-side gate Code cannot verify.

6. **Claude Code session prompt provided** for v2 execution —
   includes the read-and-confirm gate before any editing.

7. **`standing_instructions.md` — two instructions added (160 →
   165 lines).** Cat 1: *don't surface dev-lead/technical calls
   for review by default* — surface only when a decision or a
   usability/operational angle is in play. Cat 2: *always provide
   the ready-to-paste Code session prompt at hand-off* without
   being asked. Both from operator feedback this session.

## Standing-instruction adherence check

- **Cat 1 brevity / decision-framing** — held after an explicit
  mid-session correction; the new Cat 1 instruction codifies the
  lesson (over-surfacing dev-lead calls).
- **Cat 1 hard-wrap review blocks** — Code prompt and brief
  content wrapped.
- **Cat 2 timestamp anchors (DR-021)** — open + close anchored
  ACST.
- **Cat 2 always-provide-opening-prompt** — S164 prompt produced;
  Code prompt produced (now also a standing rule).
- **Cat 3 Desktop Commander exclusive; verify every write** —
  all writes via DC; line/sha verified post-write.
- **Cat 3 empirical-verification before editing governance
  artefacts** — current_state.md and standing_instructions.md
  re-read from disk before edit.
- **Cat 5 make-the-call / dev-lead territory** — technical shape
  (ref scheme, helper placement, guard semantics) handled in the
  brief; only the unify-vs-decouple call surfaced to the operator.
- **Brief-drafting skill** — fix brief follows the surgical-fix
  shape with dirty-tree handling (Sessions 35/36 precedent).

## Open items out (closed this session)

- **Lay-503 fix scoping** — the S163 primary. Resolved into a
  commissioned-and-triaged impact review plus a locked fix brief.
  ✅ (execution carries to S164.)
- **"Does shortening the ref break anything downstream?"** — the
  operator's open question. Answered definitively NO by the
  impact review (§5.3). ✅
- **Surgical brief v1** — superseded; no longer a live artefact. ✅

## Open items (carried — pointer to current_state.md)

- **Execute `customer_ref_fix_brief_v2.md`** (Code) → triage
  `customer_ref_fix_report.md` (Chat) → operator runs live $5
  lay. The S164 primary.
- All S162 parking-lot items unchanged (F1 uncaught-transport
  gap, 200-market over-subscription, audit-sink durability,
  streaming hardening F3/F5/F4, modal error-reason surfacing,
  W16 cutover scoping, and the longer parking lot).
- **Bet-safety hard rule** — clean + proven live (5 runs, no bet
  placed). Preserve at the fix (it touches the placement path).

## Session close state

- **Rebuild folder root:** clean, no phantom files.
- **`dr029/2_4_betfair_streaming/`:** holds v1 brief (superseded),
  impact-review brief + report, fix brief v2. All on disk.
- **`bethub-v3`:** untouched this session (review was read-only;
  the fix is not yet executed). Tree remains dirty/in-flight.
- **`.close_out_backups/`:** S164 opening prompt written; stale
  S163 prompt removed.
- **Project knowledge base:** `standing_instructions.md` edited →
  needs re-upload (operator-side action, flagged below).

## Forward routing — CONFIRMED WITH OPERATOR

S164 hands `customer_ref_fix_brief_v2.md` to a fresh Claude Code
session (prompt ready in this session and in the opening prompt),
triages the resulting `customer_ref_fix_report.md`, and — if
clean — the operator re-runs the live $5 lay, which should now
place. A successful lay clears the last validation gate before
the W16 v2→v3 cutover decision. Operator confirmed close.

## Pending operator-side action

- **Re-upload `standing_instructions.md`** to the bethub-rebuild
  Claude Project knowledge base (edited this session: two new
  instructions). Drive auto-syncs the rebuild folder; the Project
  KB copy is the one that needs the manual refresh.
