# Build brief — UI pass (operator session notes, 14 Jul) — APPROVED

**Approved:** operator, 14 Jul 2026, after mock walkthrough (`ui_pass_jul14_mock.html` v2 — column order locked in walkthrough) + design note (`ui_pass_jul14_design_note.md`).
**Repo:** bethub-v3 only. **Timing:** build starts AFTER the S238 W7c dist swap releases the v3 repo (Tue 15 Jul evening); scheduled runner Wed 16 Jul 13:03, dist swap runner Wed 22:33 (app-idle-checked).
**Fences:** NO money paths — `place_lay`, settlement resolvers, reconciliation, credit maths untouched. Persist/lapse is READ-ONLY display. Settled-bet edit rules untouched (dedicated future session). All P&L/derivations stay derive-on-read (DR-019).

## Items (10)

1. **BUG (top): runner list scroll + density (operator amendment 14 Jul):** race-page runner table scrolls instead of clipping; full field always reachable; sticky header; bottom fade + "all N runners" hint. **Vertical space for runners is the layout priority: ~10 rows visible without scrolling** (compact row height; page chrome above the table — top bar, promo bar, filters — stays tight so the list gets the room). Big fields scroll for the tail; typical fields read on one screen.
2. **BUG: promo button selected state** — visible active treatment (border + fill + check), per mock.
3. **Theme: black content / white frame, app-wide** — token swap in `index.css` (mock's `:root` values are the spec: sheet #111417 / raised #1a1e23 / ink #e8e6e1 / line #2e343b; navy/rose lifted for dark). Page beyond content stays white. One pass over all pages for contrast regressions; no per-page CSS forks.
4. **EV colours:** negative red / 0–5% amber / 5%+ green — BOTH Raw EV and Promo EV columns, and anywhere else EV renders (burst review, confirm card).
5. **BetLog columns:** Placed · Race+No · Runner · Account · Book · Side · Stake@odds · Promo · State. Bet id off the grid, in row-expand only.
6. **Same-race duplicate warning:** amber non-blocking strip on the lay confirm card when the selected account-at-book already has any bet on the race (activity-feed lookup). Never blocks (S236). **Text (operator-locked, 14 Jul): just "⚠ {Account} @ {Book} already has a bet on this race ({bet details})" — nothing more.**
7. **Free-bet auto-select** in the race-page promo bar iff exactly one FB credit OR all FB credits same kind; auto-note under the bar ("✓ auto-selected — …"); multiple kinds → manual. **Additive-only rule (operator, 14 Jul): ALL current promo-bar capability is retained untouched** — promo template selection/serials, insurance-armed lay default, FB inventory draw-down (S235 §5.5), EV-at-log stamping, spend-now-file-later. The mock's three-button bar was illustrative, not a spec to shrink to.
8. **Persist/lapse read-only tags** on the race-page activity rows for Betfair bets — `persistence_type` already on the current-orders read path; serialize through the activity feed; PERSIST solid green / LAPSE dashed grey per mock.
9. **Results in the settle door:** BetLog settle door shows the race result via the existing vps_client results read (placings, SP, margins, condition where held). Graceful absence (result not yet captured → plain "no result captured yet"). Thoroughbred full; harness/dogs winner-level.
10. **BF Close column:** `sp_near` (projected BSP) per runner — **column order LOCKED (operator): # | Runner | Matched | BF Back | BF Lay | Raw EV | Promo EV | Soft Odds | BF Close | Trend | Actions** (Matched moved before prices; BF Close beside Soft Odds for quick comparison). Render: price + green ▼ shortening / red ▲ drifting / grey — flat vs current lay mid. `sp_near` already typed in `api/racing.ts:75`; verify the `/prices` route serializes it (research-prep note); null → dash.

11. **Live EV/conversion at the edited lay price (operator, 14 Jul):** in the Betfair modal, when the operator overrides the lay price (existing capability — e.g. market 6.40, enter 6.00 persist), the modal recomputes and displays the EV **and, for free-bet hedges, the FB conversion %** at the entered price, live as the field changes. Purpose: seeing where the 65–70% conversion threshold sits while choosing the price. Render: conversion % beside the price field — green ≥65% (the locked S231 baseline), amber 60–65%, red <60%; plain EV for non-FB lays. Reuses the existing conversion/EV maths (display-side recompute only — no placement or money-path change; the price-entry capability itself is untouched).

12. **Quick-lay modal cleanup (operator screenshot, 14 Jul):**
    (a) **cash / free-bet toggle alignment BUG:** each radio sits hard against ITS OWN label with clear separation between the two options (screenshot shows the free-bet radio reading as cash's — wrong-bet-type risk mid-burst). A two-segment control is acceptable if cleaner.
    (b) **Remove the permanent FREE BET explainer box** (the amber "face value below must equal…" paragraph). Superseded by item 11's live conversion display. Replace with a CONDITIONAL one-line amber warning shown only when the entered FB face value ≠ the FB credit selected in the promo bar (the one real mistake the old box guarded). No static instructional text remains in the modal.

## Acceptance
- Suites: `uv run pytest` green; `cd ui/web && npm run build` (the frontend gate — vitest does not typecheck).
- New/updated component tests: runner-list scroll presence, EV band classes at boundary values (−0.1/0/4.9/5/5.1), auto-select rule (one-credit / one-kind / multi-kind), duplicate-warning trigger, persist-lapse tag render, results-door absence case, BF Close direction classes, modal live-conversion recompute (price change → % updates; band classes at 59.9/60/64.9/65), modal toggle label-association (selected state visually bound to its own label), conditional FB-mismatch warning (fires on face≠credit, absent otherwise, explainer box gone).
- Dist swap ONLY app-down (S232 lesson); swap runner checks idle first, defers + notifies if in use.
- Visual: operator glance-check on next app open (theme is subjective — one revision round expected).

## Out of scope (named)
Settled-bet edit loosening · Betfair order edits (price/persistence changes) · any placement-time persistence choice · matcher/confidence work beyond the W7c flag already shipping.
