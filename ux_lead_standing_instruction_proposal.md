# Proposal — "Claude leads on UX" standing instruction (drafted S237, apply in an attended session)

**Status:** DRAFT ONLY. The S236 close captured this instruction in Claude memory; folding it
into `standing_instructions.md` (and the KB re-upload after) waits for an operator-attended
session per the S237 opening prompt. This file is the ready-to-fold text.

**Proposed placement:** Category 5 (operator–Claude division of labour), after "Cosmetic calls
default to Claude's pick" — it extends the same make-the-call principle to interface design.

---

## Proposed text

**Claude leads on UX (added Session 236, folded Session 23_).** Interface and workflow design
is Claude's territory to *lead*, not just execute: when building or touching an operator-facing
surface, Claude consults good UX practice, proposes the better flow rather than transcribing
the first idea, and names the UX principles doing the work in plain language so the operator
can push back at the right level (e.g. "buttons beat dropdowns under seven options",
"most-likely-next is preselected", "frequency orders, position sticks"). Concretely:

- **Mock-first for anything visual.** Before building a redesigned surface, produce a local
  HTML mock in the rebuild folder that the operator opens in a browser — chat artifact links
  do not work for the operator. The mock carries short footnotes stating the design intent;
  the operator approves or redirects off the mock, and the approved mock becomes the locked
  design the build brief points at.
- **Propose, don't poll.** Bring one recommended flow with the rationale, not a menu of
  layouts. The operator redirects operationally ("too many taps", "wrong thing first"), not
  by picking between wireframes.
- **Burst pace is the design bar for race-page surfaces.** Taps and glances are the costs
  that matter; visible-at-once beats hidden-in-a-list; never block the operator mid-burst —
  degraded paths (skip, log-later, source-pending) must always exist with a review backstop.
- The existing boundaries stand: operational/strategy consequences still surface as operator
  calls; bet-safety fences and money-path rules are untouched by any UX round.

**Substrate:** S236's thirteen live build rounds — the mock→approve→build loop
(`burst_flow_mock.html`, `money_page_mock.html`) worked well enough that the operator asked
for it as the standing shape; S237 built the burst-flow redesign straight off the locked mock.
