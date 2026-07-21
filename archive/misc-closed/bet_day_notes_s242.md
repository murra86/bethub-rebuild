# Bet-day notes — Session 242 (Sat 18 Jul 2026)

Operator feedback captured live during the big bet day. NO code today (standing
rule) — these feed the next UI pass brief. Pattern per S234 bet-session notes.

## 1. Free-bet auto-select misbehaving on account switch

**Operator report (~12:15 ACST):** free-bet auto-select (the UI-pass item 7
behaviour — auto-pick when only one FB is available, or the same FB across
accounts) doesn't appear to work properly, **especially when switching from one
account / account-at-book to another while the free-bet promo stays applied.**

- Suspected shape: the FB selection isn't re-derived when the account context
  changes — a stale selection (or none) rides across the switch while the promo
  chip stays lit.
- Risk class: logging/UX, not money-path — but a wrong-account free bet on the
  slip could mis-log a bet if unnoticed. **Interim habit today: glance the FB
  chip after every account switch.**
- Build note: reproduce with two accounts holding FBs at the same book, then
  switch account-at-book with the promo applied; check what the auto-select
  derives from (per-account inventory refetch vs cached list).

## 2. BetLog row summary: P&L impact + insurance-trigger gift icon

**Operator request:** on the BetLog single-row summary,
(a) show the **P&L impact** on the row itself (not only inside the expanded
view), and
(b) add a **small gift icon on bets that triggered insurance** (stake-back /
bonus-back promo fired), so triggered bets are scannable at a glance.

- Data note: insurance-trigger state should derive from the promo-event spine
  (credit-in events keyed to the qualifying bet), not a new stored flag —
  derive-on-read per DR-019.

## 3. Match-status + settle latency (operator observation ~13:40)

**Report:** Betfair bet matched/unmatched status slow to update, "sometimes not
at all"; BetLog slow to settle.

**Grounded (S242, read-only):** reconciliation worker interval =
`DEFAULT_RECONCILIATION_INTERVAL_SECONDS = 300.0` (+60s young-bet guard) →
3–6 min visible lag. Settlement worker = 60s but gated on Betfair market CLOSED
+ resolved runners (S223 keying) → Betfair's own 2–5+ min close time dominates.
"Never updates" candidates: honest pre-jump unmatched state (lapses ~2 min
post-jump), or frontend display staleness (store is right underneath).

**Queued build (weekend, operator asked):** reconciliation 300s → 60s; make
both worker intervals env-tunable (no env override exists today — constants
only). Safety assessed OK: per-pass Betfair calls only for unresolved bets,
read-type calls, trivial volume at current bet counts; keep the 60s young-bet
guard; leave settlement at 60s. Also check frontend status-refresh cadence
(ties to the parked "amber unmatched recheck" item).

## 4. Voided free bet → pool return: LIVE-PROVEN correct (~13:50)

Gold Coast R4, 8. Inbestigator scratched → Leigh–TAB $50 FB deploy voided
(`bet-a5f3cfb2…`, settled voided $0) + Tim–BetFair offsetting lay voided $0
(`bet-60ce7b90…`). Operator asked whether the FB returned to the account:
**verified via `/racing/log-context` — Leigh–TAB free_bet_balance $50.00,
fb_count 1 (same credit event `a7949d61…`)**. Derive-on-read drops the voided
deploy from the draw-down; no correction needed. First live exercise of the
void→FB-return path — money surface correct end-to-end. Operator to confirm
TAB's own app shows the returned FB + any shortened expiry.

## 5. Race-page bottom bar: fully-unmatched Betfair bet shows "$0.00 @ $0.00"

**Operator report (~13:55):** when a Betfair bet is fully unmatched, the race
page's bottom bar renders it as "$0.00 @ $0.00". It should show at least the
ORDER price (and ideally the requested stake), e.g. "unmatched $35.65 @ 9.60",
not zeros.

- Shape: the bar is reading matched_stake/matched_price (both honestly 0/null
  pre-match) instead of falling back to requested_stake + order price for the
  unmatched display. Same family as the S241 UI-pass "honest frozen
  matched-unmatched" work — display fallback, not money-path.
- Data is already on the record (`requested_stake`, leg order price) —
  frontend-only fix for the next UI pass.

## 6. Total matched money: stale in race list, absent on race page

**Operator report (~14:00):** the racing list (left bar) shows a very old
total-matched amount per race; the specific race page doesn't show it at all.
Want a CURRENT total-matched figure visible on the race page at least.

- The live `/racing/markets/{id}/prices` payload already carries
  `total_market_traded_volume` fresh from Betfair (proven in today's R3
  monitor — it ticked $29k→$92k pre-jump) — the race page just doesn't render
  it. The left-bar figure likely comes from the older race-list read and never
  refreshes.
- Build shape: render total matched (and maybe Δ since page open) from the
  prices payload the page already polls; frontend-only. Liquidity-at-a-glance
  matters for lay sizing pre-jump (thin-pool caution from the BF Close
  masterclass + watcher research).

## 7. FLAG — Sarie bonus-winnings FB didn't credit (Rosehill R7 #4 Roselyns Star)

**Operator flag (~14:30), triage LATER (not today):** Sarie–TAB $50 cash back
on 4. Roselyns Star @ 2.0, **settled WON +$50**
(`bet-8e2a16c9-d86f-5d16-b631-4ec8b3f2667f`, cycle `408baadd…`, promo template
`0f6456d4-759d-51be-af27-ddb1b6987c5e` = bonus-winnings variant). Expected: $50
winnings credited as a free bet to Sarie–TAB — **no FB credit landed.**

Read-only facts captured at flag time:
- The bet is **NOT on the credit-gaps surface** (23 gaps listed, this bet
  absent) — so the gap detector didn't catch it either. Triage should ask why:
  bonus-winnings variant not covered by the gap query? template terms wrong
  (wrong variant per S233 lesson)? credit gate expecting `settled_lost`
  (insurance shape) rather than WON (winnings shape)?
- Cross-check TAB's app for whether the book itself credited (real-world side)
  before crediting through the door — never credit off an unverified variant.
- Related: 23 undismissed credit-gaps is a lot mid-day — worth a sweep in the
  same triage sitting.

## 8. Sunday review: P&L reconciled to the cent; bets-list 50-row cap trap

Sunday (19 Jul) burst review: operator questioned Balances-page P&L +679.08 vs
Claude's scan +651.56. **Resolution: the Balances page was RIGHT** — the
`/api/v1/bets` list defaults to a 50-row page; Saturday had **107 bets** and the
scan saw only the newest 50. Full-book settled P&L = **+679.08 exactly** =
balances derivation; Kate–CrownBet −$265 all logged, her $0 balance derives
correctly (seed 265 − losses 265). No Betfair anomaly; money check clean.

- **Verify item (next UI pass):** does the BetLog screen fetch beyond 50 rows?
  A 100+ bet day could silently hide older bets if it shares the default cap.
- **Operator action (open):** log the missing second hop for the Sat $400
  BetRight deposit — an account_holder_funding (Tim, external bank money in)
  via the movements door; Sarie's $300 had both hops, this one only the deposit.
- Corrected counts: 107 bets Sat, 21 lay-only cycles for burst-review pairing.

## 9. Item-8 follow-through: full truncation review COMPLETE (Sun 19 Jul eve)

The 50-row-cap question was escalated to a full money-read silent-truncation
review (46-agent workflow). The session running it died at the report stage;
recovered same evening from the run journal, last 2 verifications re-run
fresh. **Full report: `money_read_truncation_review_report.md`.** Headlines:
data certified clean (+679.08 three independent ways, incl. the 3-way
reconcile certificate); BetLog screen itself is honest (paginates with a
visible total — the item-8 verify question is answered NO-problem); 1 real
HIGH found (free-bet credit guard reads only oldest 1000 promo events —
~one-season fuse to double-credit risk); one batched "honest money reads"
fix brief recommended (§4 of the report). Two operator-attention items from
the reconcile: confirm the zeroed won bet `bet-ac23aa98…` was intentional;
$50 FB inventory double-deployment on `bet-3b84ec36…` (board shows $150/3,
truth $200/4).

## 10. RESOLVED (Sun 19 Jul): zeroed BetRight bet — real gap = no void/delete door

Operator confirm on `bet-ac23aa98…` (Tim–BetRight safety_net "won" @8.0):
**the bet never existed at BetRight** — operator thought the slip was
confirmed, verified on the BetRight website it was not. Zeroing
matched_stake post-settlement was the only workaround the tool allowed.
**Flagged gap for next brief: the tool has no way to void/delete a bet in
any state (pending, settled, or otherwise).** Wants an audit-trailed
operator void door (same shape as the manual settle door / signed correction
discipline). Note the row still reads `settled_won` semantically — counts
and safety-net stats include a bet that never existed; the void door should
also allow re-classing this row.

## 11. FB double-deployment = CROSS-ACCOUNT draw — likely item-1's money fingerprint

Corrected picture (Sun 19 Jul eve, operator BetLog check + DB re-read; my
first read wrongly put both Notified bets at Leigh–TAB):

- Kate–CrownBet $50 on 2. Notified (Flemington R1, 11:29 @3.2, lost) →
  $50 FB credit `5fb003c4…` at **Kate–CrownBet**.
- Leigh–TAB $50 on the same horse (11:32 @3.1, lost) → $50 FB credit
  `6e98446e…` at **Leigh–TAB**. Both bets + both credits REAL; no phantom,
  Sat P&L stands.
- Leigh–TAB's single $50 FB deploy (2. Tempt The Gods, Morphettville R3,
  12:50:54) wrote TWO deploy events at the identical microsecond, same
  correlation/cycle `0a60077d…`, source=operator: `6202dcc6…` correctly
  draws Leigh–TAB's credit; **`031bbd8e…` is filed under Kate–CrownBet and
  draws HER credit for Leigh's bet — a cross-account draw that should be
  impossible.**
- **Almost certainly the money-side fingerprint of item 1** (FB auto-select
  stale across account switch, operator-reported ~12:15 same day, this at
  12:50): stale Kate–CrownBet FB selection rode across the account switch
  and the door wrote draws for both the stale and the correct credit.
- **Real-world check now: Kate's CrownBet app — is her $50 FB still
  available?** If yes (expected): supersede deploy `031bbd8e…` via signed
  correction → Kate–CrownBet FB back to $50, board $150/3 → $200/4.
- Brief items this feeds: item-1 auto-select fix MUST clear FB selection on
  account switch; deploy door MUST hard-reject draws whose credit
  account_at_book ≠ deploying bet's; correction door for this event.

## 12. Tim–BetRight FB mismatch — operator cross-referencing (19 Jul eve)

Board shows $50/1 FB at Tim–BetRight; real BetRight account shows NONE.
The on-board credit (`98c79d35…`) traces to the **8. Missapprehend**
safety-net loss (Flemington R4, $50 @4.4, placed 13:19 Sat). The two
earlier credits (Kakoda R3 11:53, Ballpark R4 12:26) are consumed and
uncontested.

**RESOLVED same evening (money side):** operator confirmed BetRight paid
only 2 of 3 qualifiers. Built the credit-revocation door (`fb_revoke.py`,
commit `452b35d`) and revoked one credit (revoke event `23cfae56…` on
`98c79d35…`). Final board: 0 FBs at every account-at-book — matches real
world exactly.

**Attribution correction (operator, later same eve):** the unpaid one was
**BALLPARK's** credit (ran 3rd, NO third dividend on the card), not
Missapprehend's — operator suspects a BetRight T&C: no 3rd div → no
stake-back (other books pay regardless). Board unaffected (same $50/same
account/same day), but the spine currently reads: 2nd FB spend drew
Ballpark's credit (really spent Missapprehend's), Missapprehend revoked
(really Ballpark unpaid). **Deliberately NOT re-labelling while the
operator's BetRight query is open:**
- BetRight pays → un-revoke `98c79d35…` (needs the restore door extended
  to revoke targets — small build), board +$50, labels then materially
  moot (3 credits, 2 spent, 1 available).
- BetRight refuses → money already right; this note is the true story.

**PROMO-TERMS LESSON — CONFIRMED BY BETRIGHT (operator query, 19 Jul):
BetRight excludes THIRD placing from insurance bets when the field is
SEVEN runners or fewer.** Rosehill R4 evidently shrank to ≤7 via a
scratching — so Ballpark ran 3rd and earned nothing. **CASE CLOSED: no
money owed, the revocation stands final; spine attribution note above is
the permanent record (no event churn — board correct either way).**

Standing strategy implications (→ Cat-4 lessons + feedback session):
1. **Check the FIELD SIZE before every BetRight safety-net bet** — ≤7
   runners means 3rd place pays nothing there while TAB etc. still
   credit. Prefer other books for insurance on small fields.
2. **Scratchings can shrink a field below 8 AFTER placement** — the
   protection can silently degrade post-bet. On scratching-heavy days,
   a placed BetRight insurance bet may be worth less than at placement.
3. Catalogue/EV gap: the promo catalogue's `refund_positions` is static
   (`[2,3]`) — it can't express "positions [2] when field ≤7". Picker EV
   overstates BetRight insurance on small fields. Discuss whether to add
   conditional terms or a picker warning (feedback session).

## DISCUSSION QUEUE — for the bet-day feedback session (operator-flagged 19 Jul)

Status at S243 close: items 4 (void→FB-return) and the item-1/-11 FB
cross-account arc are FIXED + LIVE-PROVEN (`fb_cross_account_fix_report.md`).
Still to discuss/action when the feedback session opens:

- **Item 1 residual:** auto-select re-derivation shipped; walk through the
  new behaviour with the operator on a live race day.
- **Item 2:** BetLog row P&L impact + insurance-trigger gift icon (build).
- **Item 3:** reconciliation 300s→60s + env-tunable worker intervals
  (queued build, safety already assessed OK).
- **Item 5:** race-page bottom bar "$0.00 @ $0.00" on fully-unmatched
  lays — display fallback to requested stake + order price.
- **Item 6:** current total-matched on the race page (payload already
  carries it); stale left-bar figure.
- **Item 7:** Sarie bonus-winnings FB no-credit triage + the 23
  undismissed credit-gaps sweep (reduced-count recheck post-S243).
- **Item 8 riders:** BetLog >50-row verify ANSWERED (honest pagination —
  truncation review); operator still to log the $400 BetRight deposit's
  second hop (account_holder_funding).
- **Item 10:** void/delete-bet door (gap confirmed by BetRight phantom).
- **Item 12:** BetRight FB mismatch (above) — resolve after cross-ref.
- Plus standing queue: honest-money-reads brief (credit-guard 1000-window
  HIGH), settlement auto-restore-on-void, take-SP sign-off, TAB API build
  (Mon), watcher walkthrough, results-retention build.

## (more to come — operator flagged further items will follow during the day)
