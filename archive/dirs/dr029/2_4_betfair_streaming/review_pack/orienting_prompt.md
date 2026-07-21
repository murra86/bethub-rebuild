# Orienting prompt — §2.4 Betfair Streaming brief fresh-eyes review

**Purpose:** Single prompt sent to each reviewer alongside the locked §2.4 brief and sanctioned Betfair API resources, GitHub, and the Betfair Developer Forum. Same prompt to both reviewers per the multi-agent review pattern in `governance.md`.

**Authored:** Session 65, 2026-05-03.

---

## Prompt text

```
You are conducting a single-pass fresh-eyes review of a locked architectural
brief for a betting platform's Betfair Streaming integration. The brief is
the v3 design specification for one module of a larger rebuild; your review
is the last gate before downstream implementation work commissions against
it.

YOUR TASK

Reconcile every substantive design choice, claim, and assumption in the
brief against Betfair's sanctioned developer materials and other materials. Where the brief is consistent — note it briefly. Where the brief diverges from, contradicts, or
makes assumptions that does not support — flag it
explicitly with the relevant reference. Where the brief makes a claim the
sanctioned material doesn't cover at all — flag the gap.

You are not being asked whether the brief's overall direction is right.
That work has already been done. You are being asked whether the brief's
specific design choices and load-bearing assumptions hold up against what
Betfair officially documents and what The Racing API officially exposes.

The reference document opens with a section-by-section guide explaining
its structure, a cross-reference index mapping brief sections to relevant
reference material, and provenance notes for each captured source.


WHAT GOOD FINDINGS LOOK LIKE

- "Brief §X claims [specific claim]; sanctioned reference [specific
  source] says [specific contradiction or qualification]."
- "Brief §X assumes [specific assumption]; sanctioned reference does not
  support this. The closest sanctioned material [specific source] covers
  [adjacent topic] but does not address [the specific assumption]."
- "Brief §X is silent on [specific concern]; sanctioned reference
  [specific source] indicates this matters because [specific reason]."

WHAT WEAK FINDINGS LOOK LIKE

- Stylistic preferences ("I would have structured §X differently") —
  out of scope. The brief's structure is locked.
- Generalised concerns without a specific sanctioned-material citation
  — the review's value is in the specificity.
- Findings about the brief's overall direction or scope — out of scope.
  Direction is settled.

OUTPUT FORMAT

A markdown document with the following structure:

1. ## Findings — substantive
   Each finding numbered. Each finding cites the specific brief section
   and the specific sanctioned reference. Severity tag at the head of
   each finding: BLOCKING (brief is incorrect on a load-bearing point),
   SIGNIFICANT (brief makes an assumption the sanctioned material does
   not support, requires operator decision before implementation),
   MINOR (cosmetic or low-impact alignment issue).

2. ## Findings — gaps
   Sections of the brief where the sanctioned material is silent and the
   brief's claim depends on assumed behaviour. These are gaps in the
   sanctioned material rather than errors in the brief, but worth
   surfacing.

3. ## Sections reviewed without findings
   Brief sections that you reviewed and where you found no issues.
   Brief listing only.

4. ## Notes for the operator
   Anything you noticed that doesn't fit the above categories but the
   operator should know.

CONSTRAINTS

- Single pass. Do not iterate.
- Cite specific brief sections (e.g. "§9.6", "§13.2") and specific
  reference sections (e.g. "Section 1 — Streaming API, Connection",
  "Section 2.1 — placeOrders").
- Plain operator language where possible. Technical terms are fine where
  they're load-bearing.
- Do not propose redrafts of brief sections. Findings only.
```

---

## Operator-side notes

- Send the same prompt to both reviewers (Claude fresh session + Grok session) per `governance.md` multi-agent review pattern.
- The reference document `sanctioned_reference.md` Section 2 includes ten sub-sections covering the Betfair Reference Guide pages directly relevant to §2.4 (placeOrders, cancelOrders, replaceOrders, updateOrders, Login & Session Management, Betting Enums, Betting Exceptions, Best Practice, Market Data Request Limits, Betfair Starting Price Betting). The pack is complete and shippable as of Session 66.
- After both reviewers return findings, triage happens in a fresh Claude session against the locked brief — surface alignment, flag conflict, decide remediation per finding.
