# FB cross-account draw fix — build brief (S243, Sun 19 Jul 2026)

**Commissioned:** operator, 19 Jul ("We need to fix the root cause of this"),
after the Kate–CrownBet credit was confirmed spent by a Leigh–TAB bet.

## Incident (root-caused, evidence in bet-day notes S242 item 11)

Sat 18 Jul 12:50:54 — Leigh–TAB's single $50 FB deploy (2. Tempt The Gods)
wrote TWO `free_bet_deployed` events: one correctly drawing Leigh–TAB's
credit, one drawing **Kate–CrownBet's** credit (`031bbd8e…`) for a bet Kate
never placed. Mechanism, both layers verified in code:

1. **Frontend:** `fbSelection` (owned `Racing.tsx:119`) survives an
   account-at-book switch. Auto-select had armed Kate's credit; operator
   switched to Leigh with the FB promo applied (their own 12:15 report,
   item 1); clicking Leigh's credit ADDED to the stale set
   (`TopBar.tsx toggleCredit` unions). `faceTotal` filters against the
   *current* account's list, so the bar showed a clean $50 while carrying
   two ids. `ConfirmCard.tsx:152` submitted both.
2. **Backend:** `record_free_bet_deployment` (`fb_deployment.py`) writes one
   event per submitted credit and **copies account fields from the credit**,
   never checking the credit belongs to the deploying bet's account.

Knock-on found while tracing (chain enumeration, all 25 credits):
- Kate's real FB spend today (bet `8246cc19…`, Odin Omen) correctly landed
  **source-pending** — her credit was already (wrongly) consumed.
- **Void-return gap:** `compute_free_bet_inventory`'s chain walk has NO
  void-awareness — the voided Gold Coast deploy (`5f119565…` consuming
  credit `30a147cd…`) still reads consumed. S242 item 4's live-proof
  actually observed a *different* $50 credit that was momentarily free.
  If TAB returned the FB (operator to confirm), Leigh is $50 light.

## Build scope (this brief)

1. **Backend guard (money-path fence):** `record_free_bet_deployment`
   loads the deploying bet's `account_at_book_id` and raises
   `FreeBetDeploymentError` if ANY consumed credit's `account_at_book_id`
   differs. One choke point covers all 3 doors (racing log, past-bet log,
   pair-spend). Red-before test reproduces the Sat shape.
2. **Restore door:** `POST /api/v1/promos/deployment-corrections` — body:
   `deploy_event_id`, `reason` (required, non-empty). Validations: target
   exists, is `free_bet_deployed`, is not already superseded. Writes a
   corrective `free_bet_credited` event with
   `supersedes_event_id = deploy_event_id`, payload copied from the
   original credit (face value, source, triggering ids), `source=operator`,
   `notes=reason`. Chain becomes credit → deploy → corrective credit
   (terminal CREDITED → available again, re-spendable via picker or
   pair-spend).
3. **Chain-root fix in the walk:** `compute_free_bet_inventory` must skip
   credits with `supersedes_event_id != None` as chain STARTS (a corrective
   credit is a chain link, not a root) — otherwise a restored credit
   double-counts. No behavior change for existing data (no such credits
   yet).
4. **Frontend:** (a) `Racing.tsx` clears `fbSelection` whenever
   `accountAtBookId` changes; (b) `TopBar` re-arms auto-select per account
   (reset `fbAutoDoneRef` on aab change); (c) belt-and-braces: TopBar
   prunes selected credit ids not present in the current account's
   `free_bets` list. vitest red-before on the switch-keeps-stale-id shape.

## Data corrections (through the new door, after restart)

- Kate–CrownBet: correct deploy `031bbd8e…` (reason: cross-account draw,
  S242 item 11) → pair source-pending bet `8246cc19…` to the corrective
  credit via the existing pair-spend door. Board net unchanged; records true.
- Leigh–TAB: correct voided deploy `5f119565…` ONLY after operator confirms
  TAB actually returned the $50 (and it hasn't expired). Board +$50 if so.

## Deferred (flagged, separate briefs)

- Settlement auto-restore-on-void: resolver writes the corrective credit
  when it voids an FB bet, so the void-return path is automatic (today it
  needs the manual door). Rare event; manual door covers the gap.
- The S242/S243 "honest money reads" brief (truncation review report §4) —
  including the fb_credit oldest-1000 guard window (HIGH).
- Operator void/delete-bet door (bet-day notes item 10).

## Deployment note

Backend + frontend changes require an app restart + `npm run build`
(dist rebuild app-down per S232 lesson). Operator to give a 2-minute
window; corrections run immediately after through the new door.
