# FB cross-account draw fix — build report (S243, Sun 19 Jul 2026)

Brief: `fb_cross_account_draw_fix_brief.md` (operator-commissioned same
day). **All 4 scope items BUILT + red-before/green-after proven.
Implemented-not-live: needs the app-down window below.**

## What was built

1. **Backend cross-account guard** — `workflows/promos/v1/fb_deployment.py`
   - `record_free_bet_deployment` now loads the deploying bet's
     account-at-book from the bets row and refuses any credit banked at a
     different account ("S243 cross-account draw guard"). Missing bets row
     also refuses (integrity fault, not a skip).
   - Whole-batch validate-then-write: a bad credit anywhere in the list
     leaves NO partial deploy events (the incident batch mixed a valid and
     a cross-account credit).
   - One choke point covers all three doors: race-screen log, Log-Past-Bet,
     burst-review pair-spend.
   - Red-before proven: old code accepts the exact Sat 18 Jul shape; new
     code raises and writes nothing.
2. **Restore door** — new `workflows/promos/v1/fb_restore.py` +
   `POST /api/v1/promos/deployment-corrections` (promos router).
   Append-only undo: writes a corrective `free_bet_credited` event
   superseding the wrong deploy, payload copied from the original credit,
   mandatory reason → `notes` (audit trail). Refuses non-deploy targets,
   already-superseded deploys, missing events, empty reasons. Restored
   credits are re-spendable through the picker and pair-spend (guard
   passes: corrective credit keeps the true owner's account).
3. **Chain-root fix** — `compute_free_bet_inventory` skips credits
   carrying `supersedes_event_id` as chain roots (a corrective credit is a
   link, not a root) — without this a restored credit double-counts. No
   behavior change for existing data.
4. **Frontend clear-on-switch** — `ui/web/src/components/TopBar.tsx`:
   the FB selection clears and auto-select re-arms on every
   account-at-book change; a second belt-and-braces effect prunes any
   selected credit id not present in the current account's inventory
   (recomputing the face total over survivors). Implemented in TopBar
   (which owns the inventory fetch) rather than Racing.tsx as briefed —
   single owner, covers every parent. Same clear added to Log-Past-Bet's
   own FB draw-down set (`routes/LogPastBet.tsx`). Red-before proven: both
   S243 vitest tests fail on the old TopBar (stale id survives the
   switch), pass on the new one.

## Suites

- Backend: `uv run pytest` → **1474 passed, 0 failed** (one racing test
  fixture updated: mocked orchestrator now seeds the bets row the real
  one guarantees before deploy).
- Frontend: `npx tsc --noEmit` clean; `npx vitest run` → **209 passed**
  (2 new S243 tests). `npm run build` NOT yet run — dist rebuild is
  app-down only (S232 lesson); see window below.

## Go-live window (operator, ~2 minutes)

1. Close/stop the BetHub app (BetHub.command window).
2. `cd ~/Desktop/Projects/bethub-v3/ui/web && npm run build`
3. Relaunch BetHub.command.
4. Claude then runs the data corrections (below) through the new door and
   verifies the board.

## Data corrections — EXECUTED + VERIFIED (19 Jul ~17:24, post-restart)

All four ran through the new doors, first production use:

1. Kate restore: corrective credit `774a6af1…` superseded `031bbd8e…` ✓
2. Kate pair: `bet-8246cc19…` (Odin Omen) → deploy `54c8e123…` ✓
3. Leigh restore: corrective credit `001b3c92…` superseded `5f119565…`
   (TAB's return confirmed by the operator RE-USING the FB on Oscar
   Phoenix 16:57 — logged via bonus-not-banked-yet, parked
   source-pending exactly as designed) ✓
4. Leigh pair: `bet-d5f61a99…` (Oscar Phoenix) → deploy `21b5d28e…` ✓

Verified end-state: source-pending queue EMPTY; Kate–CrownBet 0 FBs
(3 credits = 3 real spends); Leigh–TAB 0 FBs (8 credit events = 7 earned
+ 1 corrective link; 7 real spends — matches the operator's real-world
count exactly); board total $50/1 = Tim–BetRight's genuinely unspent FB.
Restore→re-pair chain (credit → deploy → corrective → deploy) live-proven.

## Original staged plan (superseded by the above)

1. **Kate–CrownBet restore** — `POST /api/v1/promos/deployment-corrections`
   `deploy_event_id = 031bbd8e-fc6d-4306-85ed-f43cc5111f85`
   (the rogue Sat 12:50:54 cross-account draw), reason: S242 item 11.
2. **Pair Kate's real spend** — `POST /api/v1/promos/pair-spend`
   `bet_id = bet-8246cc19-c8d8-5872-952a-b6ad236674e4` (Odin Omen,
   Carnarvon R3, currently source-pending) +
   `credit_event_id = <corrective id from step 1>`.
   End state: all 3 Kate credits truly consumed, source-pending empty,
   board unchanged in total (restore +50, pair −50) but records true.
3. **HOLD — Leigh voided-bet restore** (`deploy_event_id =
   5f119565-655e-4d95-ab43-3f40a777fdbc`, Gold Coast R4 void): run ONLY
   after the operator confirms in Leigh's TAB app that the $50 FB was
   returned and is still there (S242 item 4 follow-up; the inventory walk
   was never void-aware — the item-4 live-proof saw a different credit).
   If confirmed: board +$50 → Leigh 2 FBs.

## Addendum (19 Jul eve): credit-revocation door + BetRight phantom credit

Operator cross-referenced the Tim–BetRight board FB against the real
account: **BetRight paid only 2 of 3 Saturday safety-net qualifiers**
(Kakoda ✓ spent, Ballpark ✓ spent, Missapprehend ✗ never landed). Built
the un-credit twin of the restore door same evening: `fb_revoke.py` +
`POST /v1/promos/credit-revocations` (append-only `free_bet_revoked`
superseding the credit; refuses spent/already-revoked; mandatory
reason). Suite 1477 green, commit `452b35d` pushed. Phantom credit
`98c79d35…` revoked via the door function (revoke event `23cfae56…`);
endpoint live at next app restart.

**Final verified board state: every account-at-book 0 FBs — matches the
operator's real-world accounts exactly.** Note: if BetRight ever pays
the Missapprehend credit late, re-crediting needs a correction (the
credit-in idempotency guard will see the revoked event's qualifier as
already credited) — flagged in fb_revoke.py's module note.

## Deferred (flagged in the brief)

- Settlement auto-restore-on-void (resolver writes the corrective credit
  when voiding an FB bet) — manual door covers the rare case meanwhile.
- "Honest money reads" brief (truncation review §4) incl. the fb_credit
  oldest-1000 window (HIGH) — separate build.
- Operator void/delete-bet door (notes item 10).
