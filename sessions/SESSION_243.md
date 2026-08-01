# Session 243 — Sun 19 Jul 2026 (afternoon → evening)

_Closed: 2026-07-19 17:54 ACST. (Stamp added at the S244 close — the
original close-out omitted it; flagged by the S244 open drift-check.
No other content altered.)_

Covers the Sunday arc: recovery of the crashed morning review session,
the full FB correction saga, and the S242 bet-day follow-through. (Sat
18 Jul = S242 bet day, NO-code by standing rule — its record is
`bet_day_notes_s242.md`, items 1–12.)

## Headline deliverables

1. **Interrupted money-read truncation review RECOVERED + COMPLETE**
   (`money_read_truncation_review_report.md`). The morning session died
   mid-workflow (41/46 agents done); recovered from the run journal, the
   2 lost verifications re-run fresh. Verdict: **store certified clean —
   bets / ledger / API all +679.08 to the cent** (Saturday's +651.56
   scare was the 50-row API default, not data). 1 HIGH latent (fb_credit
   oldest-1000 guard window, ~10–16 week fuse), 2 MEDIUM (omitted-limit
   trap on /api/v1/bets; UI itself honest), 2 LOW, 38 refuted. One
   batched "honest money reads" fix brief recommended (report §4) — NOT
   yet commissioned.
2. **FB cross-account draw ROOT-CAUSED + FIXED + LIVE-PROVEN**
   (`fb_cross_account_draw_fix_brief.md` → `fb_cross_account_fix_report.md`,
   commits `9427f26` + `452b35d`). Sat incident: Leigh–TAB's FB spend
   drew Kate–CrownBet's credit — stale frontend selection rode an
   account switch AND the deploy writer never checked ownership. Built:
   batch-validated cross-account guard (all 3 doors), TopBar selection
   clear+re-arm on account switch + stale-id prune, LogPastBet clear,
   restore door (`POST /v1/promos/deployment-corrections`), revoke door
   (`POST /v1/promos/credit-revocations`), chain-root walk fix.
   Red-before/green-after proven both sides.
3. **FB spine reconciled to REALITY, account by account.** Corrections
   run through the new doors same evening (their first production use):
   Kate restore+pair (Odin Omen), Leigh void-return restore+pair (Oscar
   Phoenix — TAB's return proven by operator re-use), BetRight phantom
   credit revoked. **Final board: 0 unspent FBs everywhere = exactly the
   real-world accounts.** Also surfaced: the inventory walk was never
   void-aware — S242 item 4's "void→FB-return live-proof" had actually
   observed a different credit (documented; auto-restore-on-void queued).
4. **BetRight T&C confirmed (operator query): insurance excludes 3rd
   place at ≤7 runners.** Ballpark's Rosehill R4 shrank via a scratching
   → 3rd paid nothing. Promoted to Cat-4 standing lessons
   (`bethub_promo_terms_lessons` memory): field-size check before
   BetRight safety-nets; post-placement scratchings degrade protection;
   picker/EV can't express the conditional (catalogue gap flagged).
5. **Bet-day item 3 BUILT: reconciliation 300s→60s + env-tunable worker
   intervals** (commit `7b63b82`): `BETHUB_RECONCILIATION_INTERVAL_SECONDS`
   / `BETHUB_SETTLEMENT_INTERVAL_SECONDS`, gt=0 validation, 10s clamp
   floor; young-bet guard unchanged. Match-status lag should drop from
   3–6 min to ~1–2.
6. **Sunday burst review closed clean** (S242 item 8): Balances page was
   RIGHT (+679.08); 107 Sat bets; 21 lay-only cycles paired; day
   reconciled to the cent.

## Suites / state at close

Backend **1481** green, frontend **209** green + tsc clean, HEAD
`7b63b82` pushed. **Pending next app restart (no urgency):** 60s
reconciliation cadence + credit-revocations endpoint go live (all data
corrections already applied via door functions). Dist rebuilt by
operator during the evening window (S232 app-down rule observed).

## Operator decisions this session

- Root-cause fix commissioned same day ("we need to fix the root cause").
- No event churn to re-label the Ballpark/Missapprehend attribution
  (board correct; notes hold the true story).
- Feedback items consolidated into a workplan (below) rather than
  piecemeal builds.

## Next session

**Workplan: `s242_s243_feedback_workplan.md`** — Monday remains TAB API
build + watcher walkthrough per S241 flags; then the honest-money-reads
brief (HIGH fuse first), UI pass #3 (race-day display items), and the
Sarie/credit-gaps triage sitting. Operator actions open: $400 BetRight
deposit second hop; app restart when convenient.
