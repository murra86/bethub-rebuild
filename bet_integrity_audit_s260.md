# Bet-integrity audit — every bet in the tool (S260, audit half of 0t)

**Date run:** 30 July 2026, 18:30 Adelaide
**Scope:** all 336 bets in the live tool, 18–30 July 2026. Read-only; nothing was changed.
**Commissioned bar:** *"every single insurance bet and free bet has been grouped or linked in its full journey"; "every bet has a story that makes sense and has the right shape"; 100% of cycles accurately tracked.*

---

## What this means for your betting day

**Your money records are sound. Your grouping records are not.**

Of your **336 bets**, **272 (81%)** are fully joined up. **64 bets (19%)** are not — and they are all the same
single problem, repeated 32 times: **since 22 July, every Betfair lay you have placed has landed in its own
separate group instead of joining the free bet it was hedging.** The free bet is in one group, the lay that
covered it is in another, and the tool no longer knows they were the same play.

Concretely: **32 of your 61 lays are stranded.** All 32 have their matching free bet sitting on the same horse
in the same race — the tool simply never linked them. Your 18–20 July lays are all correctly linked (those were
joined up by hand back in S246); **not one lay placed since then has linked itself**. So the automatic linking
has never actually worked in live use — the 29 that look right are the hand-repaired ones.

**Why it happens (one sentence):** you place the lay *first*, then log the free bet 1–3 seconds later — and the
linking check only looks for bets that already exist, so at the moment the lay goes on there is nothing to link
to. In 31 of the 32 cases the lay beat the free bet to the database by 1–3 seconds. The design assumed you'd log
the bet first and lay second; you work the other way round.

**What is definitely fine:**

- **Every free bet is accounted for, to the cent.** $2,853.00 credited across 8 account-books = $2,778.00 spent
  + $75.00 taken back by the books + $0.00 sitting unused. Not one cent unexplained, at every single account.
- **Every bet is in a group** — no bet is floating with no group, no group points at nothing.
- **Every free bet you placed traces back to the credit that paid for it, and that credit traces back to the
  bet that earned it.** 59 of 61 land in the right group; 2 are in the wrong one (see below).
- **Every recent correction held.** The reassignments, the promo swaps, the stake edits, the undo-credit, the
  manual bets — all 25 correction records point at real bets, nothing was corrected twice, and the rejected $10
  cash credit is correctly excluded from your balance (verified: including it would inflate Sarie@TAB by exactly
  $10.00, and it doesn't).
- **Today's promo correction (wrong promo picked at log time) closed perfectly** end to end: qualifier → cash
  credit rejected → free bet credited under the right promo → free bet placed → all in one group.
- **No bet has a broken shape.** Zero settled-with-no-result, zero zero-or-negative stakes, zero back bets at
  odds of 1.00 or less, zero free-bet-flagged lays, zero duplicates, zero stale pending bets.

**Two other real (small) problems:**

1. **2 free bets are grouped with the wrong qualifier** — fallout from the 25 July Leigh/Tim wrong-account fix.
   The money was corrected; the *grouping* was left pointing at the old story.
2. **The daily "unpaired lay" flag only looks back 24 hours** — so it is showing you 1 stranded lay (today's)
   when there are actually 32. The same 24-hour limit means the repair button cannot reach the older 31 either.

**Confidence level: HIGH.** Every one of the 336 bets was examined individually (not sampled), every free-bet
credit chain was walked event by event, and the free-bet totals were independently re-derived and then
cross-checked against the tool's own calculation functions — both agree exactly. The one number I cannot
independently verify is whether the 65 insurance losers that got no credit genuinely finished outside the paid
places (that needs finishing positions, which aren't in this database).

**Acceptance bar (100% of cycles accurately tracked): NOT MET.** 184 of 248 groups (74%) are accurately tracked.

### Recommended next steps

1. **Fix the lay linking for the way you actually work** — when a lay goes on and no back bet exists yet, hold
   the lay's group open for a few minutes so the free bet logged seconds later joins *it*. This is the whole
   defect; fix it and the number goes from 74% to ~99%.
2. **Widen the "unpaired lay" flag and repair button past 24 hours** — otherwise you cannot see or fix the 31
   older ones. Repair them in one batch; 30 of the 32 pair unambiguously on horse + race, the 2 Sir Myka lays
   (25 July, 14:44 and 14:46) need account/book to tell them apart.
3. **Re-point the 2 mis-grouped free bets** (`bet-76ae5c5a…`, `bet-8149d9e9…`) at the qualifiers their funding
   credits actually name. No money moves.
4. **After 1–3, re-run this audit.** Expect 336/336 bets and 216 groups, ~99% coherent.

---

## The numbers, check by check

### Check 1 — Census

| | |
|---|---|
| Total bets | **336** |
| BACK, cash, from the racing screen | 208 |
| BACK, cash, manually logged | 6 |
| BACK, free bet | 61 |
| LAY (Betfair) | 61 |
| Settled (won 119 / lost 209 / voided 4) | 332 |
| Pending | 2 (both AFL manual logs, 30 Jul) |
| Placed today, not yet settled | 2 |
| Date range | 2026-07-18 → 2026-07-30 (13 days) |
| Distinct cycles | **248** |
| Bets carrying a promo template | 194 (insurance 163, bonus-winnings 27, price-boost 4) |
| Bets with no promo template | 142 (61 lays + 61 free bets + 20 plain cash backs) |

### Check 2 — Cycle membership and free-bet cycle inheritance

| Test | Result |
|---|---|
| Bets with missing / empty `cycle_id` | **0 / 336 — PASS** |
| `cycle_id` values pointing nowhere | **0 — PASS** |
| Free-bet bets recomputed against `resolve_inherited_cycle` from the raw events | 61 checked |
| … stored cycle == qualifier's cycle (correct) | 58 |
| … goodwill-funded, fresh cycle correct by design | 1 |
| … free bets with no deploy event (funding untracked) | **0 — PASS** |
| … **MIS-LINKED** | **2 — FAIL** |
| Deploy events pointing at a non-existent bet | **0 — PASS** |
| Free-bet bets where credit drawn ≠ bet stake | 1 (historically corrected — see violation list) |

### Check 3 — Insurance / promo journeys (all 194 promo-tagged qualifiers)

| Outcome | Count |
|---|---|
| **Complete chains** (qualifier → credit → free bet placed → free bet settled) | **59** |
| Open but coherent | **135** |
| … insurance lost, no credit due (finished outside paid places) | 65 |
| … insurance won, no credit due — correct | 43 |
| … other kind settled, no credit due | 21 |
| … qualifier voided, no credit — correct | 2 |
| … credited then revoked by the book (terminal, coherent) | 2 |
| … qualifier still pending | 2 |
| **BROKEN** | **0 — PASS** |
| Credits with no source bet (and not goodwill) | **0 — PASS** |
| Credits whose source bet doesn't exist | **0 — PASS** |
| Credits consumed twice | **0 — PASS** |
| Credits revoked-but-also-consumed | **0 — PASS** |
| Credit amount ≠ stake × promo rate (triggered insurance) | **0 / 52 — PASS** |
| Bonus-winnings qualifiers that won with no credit | **0 / 27 — PASS** |
| Credits whose account-at-book differs from their source bet's | **0 — PASS** |

Insurance trigger rate observed: **52 credited of 117 lost qualifiers (44%)**.

Note on lays: 59 chains are "complete" in the promo sense (the free bet was placed and settled), but only
**28** of them have their hedging lay in the same group. That is the Check 5 defect, not a promo-chain defect.

### Check 4 — Free-bet ledger (every credit chain-walked)

| | |
|---|---|
| Free-bet credit chain roots | **62** |
| Corrective (restore / re-true) credits, correctly treated as chain links not roots | 4 |
| Unspent (available) | 0 |
| Consumed by exactly one bet | 60 |
| Revoked | 2 |
| Expired | 0 |
| Consumed by more than one deploy | **0 — PASS** |
| Consumed amount > credited amount | **0 — PASS** (chain-aware) |
| Superseded events excluded everywhere | **PASS** |

**Cross-foot, per account × book** (credited − consumed − revoked − expired = available):

| Account @ book | Credited | Consumed | Revoked | Available | |
|---|---|---|---|---|---|
| Kate @ CrownBet | 150.00 | 150.00 | 0 | 0.00 | OK |
| Leigh @ TAB | 703.00 | 703.00 | 0 | 0.00 | OK |
| Sarie @ CrownBet | 200.00 | 200.00 | 0 | 0.00 | OK |
| Sarie @ TAB | 698.00 | 698.00 | 0 | 0.00 | OK |
| Tim @ AllBets | 100.00 | 100.00 | 0 | 0.00 | OK |
| Tim @ BetRight | 250.00 | 200.00 | 50.00 | 0.00 | OK |
| Tim @ PointsBet | 305.00 | 280.00 | 25.00 | 0.00 | OK |
| Tim @ TAB | 447.00 | 447.00 | 0 | 0.00 | OK |
| **TOTAL** | **2,853.00** | **2,778.00** | **75.00** | **0.00** | **8/8 OK** |

Cross-checked against the project's own `compute_free_bet_inventory` / `compute_account_at_book_balance` run
read-only on a copy of the live database: derived free-bet balance **$0.00 at all 12 account-books** — exact
agreement with the independent recomputation above. **PASS.**

A note on method: a naive cross-foot that reads each credit's *original* face value fails Tim@TAB by −$2.00.
That is not a defect — it is the two S250 TAB whole-dollar re-trues ($11→$12 Krasina, $21→$22 Velaris). The
corrective credit is a chain *link*, and the chain's terminal face is the live truth. Both the tool and this
audit handle it correctly; anyone re-checking this by hand should walk the chain, not sum the roots.

### Check 5 — Unpaired lays, full history (no 24-hour window) — **THE HEADLINE FAILURE**

| | |
|---|---|
| LAY bets in a cycle holding no non-LAY bet | **32 of 61 (52%) — FAIL** |
| … of those, that have a free-bet back on the **same market + selection** in a **different** cycle | **32 of 32 (100%)** |
| Settled free-bet backs with no lay in their cycle (full history) | **32** |
| Correctly-paired lays | 29 — **all placed 18–20 July** (the S246 hand backfill) |
| Lays paired since 21 July | **0 of 32** |
| What the tool's own `list_unpaired_lays` shows the operator (24 h window) | **1** |

**Paired / unpaired by day:**

| Date | Paired | Unpaired |
|---|---|---|
| 18 Jul | 21 | 0 |
| 19 Jul | 5 | 0 |
| 20 Jul | 3 | 0 |
| 22 Jul | 0 | 6 |
| 25 Jul | 0 | 21 |
| 28 Jul | 0 | 1 |
| 29 Jul | 0 | 3 |
| 30 Jul | 0 | 1 |

**Root cause (evidenced, not inferred):** the lay reaches the database **before** the free bet it hedges in
**31 of 32** cases, by 1–3 seconds (e.g. 25 Jul: lay 13:03:01, free bet 13:03:03). `list_parent_cycle_candidates`
only offers *existing* BACK bets on that market/selection, so at lay time the candidate list is empty and the
lay takes a fresh cycle. The plumbing is all present and correct (`HedgeModal` → `cycle_id` → `PlaceLayRequest`);
it is the **direction of the lookup** that does not match the operator's actual sequence. Even the 29 paired lays
were placed lay-first (28 of 29) — confirming these were repaired after the fact, and that the live auto-pair door
has never once fired in production.

**Effect on the group picture:**

| | Today | If the 32 were paired |
|---|---|---|
| Cycles | 248 | 216 |
| Complete qualifier + free-bet + lay cycles | **28 of 60** (47%) | **57 of 60** (95%) |

### Check 6 — Corrections integrity

| Test | Result |
|---|---|
| Correction / mutation events examined | 25 (17 `bet_edited`, 6 `bet_created`, 2 `bet_reclassed`) |
| Events targeting a bet that doesn't exist | **0 — PASS** |
| Double-supersede in the correction chain | **0 — PASS** |
| Double-supersede in the promo-event chain | **0 — PASS** (unique index holds) |
| `bet_created` events matched to a real manual bet | **6 of 6 — PASS** |
| Rejected-cash-credit filter (S259) re-derivation, Sarie@TAB | including superseded **$10.00** vs filtered **$0.00**; difference **$10.00** = superseded amount exactly — **PASS** |
| Money event both superseded and still counted | **0 — PASS** |
| S253 wrong-account reassignment — credit account matches bet account | **PASS at all credits (0 mismatches)** |
| Today's promo-selection correction chain (`bet-bc1e2dd8…`) | qualifier → cash credit **rejected** → replacement free-bet credit → deployed on `bet-b415ab8b…` → **same cycle `9274169d`** — **PASS** |

### Check 7 — Cross-date cycles

| | |
|---|---|
| Cycles spanning more than one Adelaide date | **6 of 248 (2.4%)**, 20 bets |
| Bets a single-day view would orphan from their group | 20 |
| Would repairing the 32 lays create more cross-date cycles? | No — still 6 (the lay always lands the same day as its free bet) |

All 6 are the same coherent shape: a cash qualifier on day 1, then the free bet + its lay on day 2 (once on
day 3). Their net computes correctly from all members — the members are all present and correctly grouped; the
exposure is purely that a **date-filtered daily view splits 6 groups and shows 20 bets without their partners.**
Cycle `87957d21` spans 18–19 July with 5 members (a void-and-replace) and would be split three ways by a strict
day filter.

### Check 8 — Story shape (bounded judgment pass over all 336)

| Flag | Count |
|---|---|
| Settled with NULL outcome | **0** |
| Stake ≤ 0 | **0** |
| BACK at odds ≤ 1.00 | **0** |
| Settled-won BACK with no price (return uncomputable) | **0** |
| Free-bet flag on a LAY (contradiction) | **0** |
| Duplicate-looking (same account/book/market/selection/side/stake within a minute) | **0** |
| NULL settlement state on a bet not placed today | **0** |
| Stale pending (placed before today, still pending) | **0** |
| **Total shape flags** | **0 — PASS** |

Adjacent observations (not defects):
- 3 bets carry **no market/selection leg row** (`bet-b1fa124b…` AllBets 23 Jul, `bet-bc01507c…` Ladbrokes AFL,
  `bet-2bfd1931…` Neds AFL). All 3 are manual logs with no Betfair market — expected. Consequence worth knowing:
  every surface that joins through `bet_legs` (lay pairing, unpaired-lay flag, free-bet-missing-lay watchdog)
  cannot see them.
- The 2 pending bets are AFL manual logs (Collingwood +3.5 @1.90, Port Adelaide H2H @1.77) — correct as pending.
- 64 `promo_journey_annotation` events are all `credit_gap_dismissed` markers naming a specific bet — the
  operator's "no credit due here" dismissals. All name a real bet.

---

## Violation lists (every one, by bet id)

### V1 — Stranded lays: 32 lays whose hedged free bet sits in a different cycle (Check 5)

| Lay bet id | Placed | Runner | Matched free bet | Book | FB $ |
|---|---|---|---|---|---|
| `bet-df4dd0bb-b7bf-41af-8322-8aee25a85e85` | 22 Jul 13:18 | 3. Tassoro | `bet-e138d477-befa-5a3f-ab7b-df2eea91c15e` | tab | 30 |
| `bet-898e82a4-7b5d-4773-9a91-b4ce37e1c28a` | 22 Jul 13:51 | 5. Shalhavmusik | `bet-e9a53d63-f4dc-5e0d-9326-59aae31ec96c` | tab | 33 |
| `bet-e36d3821-f3e0-4acf-87d8-be288055320d` | 22 Jul 14:12 | 3. Mystic Reign | `bet-032b087f-3465-53b7-9ea5-46f53ddcd234` | tab | 12 |
| `bet-26d63e92-58ea-44f1-b7c6-3760c489c6c9` | 22 Jul 14:16 | 2. Justicas Bonus | `bet-e4433685-d2de-501f-847b-edbc29da941c` | tab | 22 |
| `bet-107f3175-4448-42c7-bbfd-2518c22a45db` | 22 Jul 15:28 | 4. Carravilla | `bet-ea6d006c-ce2f-5081-b93b-70ba8b1836c4` | betright | 50 |
| `bet-d1cbf340-c94e-477b-abc4-6a7676e5dabc` | 22 Jul 16:36 | 5. Oxley Flyer | `bet-141b0bae-69d7-5a3a-82fb-7680fe213929` | betright | 50 |
| `bet-3b4bb91f-543b-4c8e-8a0a-d70ead4cdbde` | 25 Jul 11:51 | 9. Grinzinger Halo | `bet-c9c57c5f-24ed-5943-9ee7-08b1275bb476` | tab | 50 |
| `bet-a7eddb87-2b83-4057-ae4a-24d9e02cb856` | 25 Jul 12:20 | 8. Harleynrose | `bet-a0b71d05-270c-5b96-97ca-fbe82a0dc5af` | tab | 50 |
| `bet-8f20497f-d85b-410c-b204-022b5144e305` | 25 Jul 12:35 | 3. Sunset Adios | `bet-4154f501-b769-59e9-94c3-25264137aab3` | tab | 50 |
| `bet-fa4798db-0f80-49f6-a3ac-3d17a80ed322` | 25 Jul 12:56 | 7. Murmurs | `bet-20d91e61-afec-5499-80c7-d304fff100ca` | tab | 50 |
| `bet-5421d5a0-3a4d-4ce9-9999-a26c55ce9057` | 25 Jul 13:03 | 13. The Judge Ruled | `bet-90de9026-3f1f-59ce-8111-77d6d1c936b4` | tab | 50 |
| `bet-fe4e76bd-3c06-4db3-a83e-488947f8f9c3` | 25 Jul 13:18 | 2. Pub Crawl | `bet-725a719f-c4d6-581c-a6a4-2acaff4d1541` | tab | 50 |
| `bet-1f154431-8649-453d-b363-20111b140346` | 25 Jul 13:35 | 3. Cool Magnum | `bet-a4189c05-4174-541b-b677-2816e551ccbc` | tab | 50 |
| `bet-1cea5a27-555b-4b82-9be8-0d200cd6316d` | 25 Jul 14:05 | 4. Lucky Lass | `bet-ff5eba56-1219-5299-8b8b-c662f6103556` | pointsbet | 50 |
| `bet-f7c31d01-005b-426c-801c-604cb664db83` | 25 Jul 14:06 | 9. Glouf | `bet-d17232dc-2ba6-5ecf-a736-799341a06362` | pointsbet | 50 |
| `bet-8b93d5a0-89e3-4acd-8ec7-060962d3e5cd` | 25 Jul 14:12 | 3. Minozza | `bet-cac3e931-cfda-53a6-ab71-49dfa0370d7a` | tab | 50 |
| `bet-dc66d03f-27ba-42a5-812d-2f0b1ea9db01` | 25 Jul 14:14 | 9. Ambello | `bet-0856d032-db64-5899-b909-2a2525160924` | tab | 50 |
| `bet-a7aa03c1-722e-4519-9fb5-e2d9e400b844` | 25 Jul 14:36 | 1. Macaverty | `bet-8724d8e4-519f-5e93-bc72-3a3be92fdd9e` | tab | 50 |
| `bet-8b7f04c7-cbed-4d34-91d1-5474e13c5291` | 25 Jul 14:44 | 1. Sir Myka | `bet-94a4365c-249b-5dfc-8fd3-5ff3a9b5a7c9` (tab) — **see note** | tab | 50 |
| `bet-0b244c21-f583-4df2-ab07-a28de9898814` | 25 Jul 14:46 | 1. Sir Myka | `bet-9c47ffd9-37e7-5a73-b3b7-55d68a11514f` (pointsbet) — **see note** | pointsbet | 50 |
| `bet-0a498911-7ff7-48cb-84e6-bea987f2c530` | 25 Jul 14:59 | 13. The Creator | `bet-76ae5c5a-7652-5975-942c-cc71c93f5d65` | tab | 50 |
| `bet-dc224ee5-75c8-4cd0-a43c-3fcf0bf7e749` | 25 Jul 15:07 | 8. Pin Deep | `bet-7015f52d-23ca-5a89-b54f-3f8b00800e2d` | pointsbet | 50 |
| `bet-820cdb27-9376-49f1-98d7-bb9fb6fa8145` | 25 Jul 15:10 | 1. Anemacore | `bet-d670e447-9431-53f9-a0b1-c748fe68ff48` | tab | 50 |
| `bet-604689b0-a51e-41eb-ad33-be6022ddd4db` | 25 Jul 15:21 | 7. Heat | `bet-d6d605f3-f817-5f70-a750-48f096b7ee4c` | tab | 50 |
| `bet-d67c5ffe-485f-4406-bd1f-d85b7f16f7e3` | 25 Jul 15:23 | 3. So Rebellious | `bet-8149d9e9-fbdc-5749-9911-b7ccdc2f4315` | tab | 50 |
| `bet-dcba3c74-4e14-4a14-9c99-ecef42341557` | 25 Jul 15:28 | 5. Smart Legend | `bet-ad852eef-8a59-573f-b355-563d58a83677` | pointsbet | 50 |
| `bet-ae65da03-d372-4ca0-8fe1-a20e404ed180` | 25 Jul 17:03 | 10. The Girls Boy | `bet-84c6725d-f9df-580c-bdc2-a3e1dd1e6434` | pointsbet | 30 |
| `bet-44ac9e9a-541c-4124-b72a-d0f8e544086f` | 28 Jul 13:06 | 5. Kota Lambai | `bet-8b3a1ce1-0aca-5ba0-a0cc-f7a1bdaba1a5` | allbets | 100 |
| `bet-1a556402-6e80-4c8b-92dd-9ab29a59beda` | 29 Jul 14:47 | 3. Swag | `bet-ddc32e68-f550-53c9-bad7-dc9e667d1162` | tab | 25 |
| `bet-4ecb7087-1a91-4f90-a68f-a8c84549b69f` | 29 Jul 15:22 | 9. The Mean Fiddler | `bet-389f3f0b-846b-55b4-a684-ee1804866808` | tab | 30 |
| `bet-bd4cda8a-9d39-4d7e-b37a-d0993b5c2881` | 29 Jul 15:23 | 5. Gambino | `bet-a93fe58b-6515-5948-96bc-4128b519de81` | tab | 40 |
| `bet-24b99ae1-0643-42a7-a68a-d5f047a6ec65` | 30 Jul 15:30 | 1. Cryptonic | `bet-b415ab8b-8ae2-5123-9e6a-f54e5de4bb47` | tab | 10 |

**Note on the Sir Myka pair:** two lays (14:44, 14:46) and two free bets (`bet-94a4365c…` at TAB, `bet-9c47ffd9…`
at PointsBet) sit on the same market and selection. Market + selection alone cannot tell which lay hedged which
free bet — pair these two by account/book or by stake, not automatically.

The 32 free bets listed above are the mirror side of this failure: each is a settled free-bet back with no lay
in its own cycle. **64 bets in 64 cycles are fragments of 32 chains that should be 32 cycles.**

### V2 — Free bets grouped with the wrong qualifier (Check 2)

| Bet | Stored cycle | Cycle its funding credit implies | Why |
|---|---|---|---|
| `bet-76ae5c5a-7652-5975-942c-cc71c93f5d65` (25 Jul 15:00, TAB, $50, Leigh) | `fc14344a…` (alone) | `a61d684a…` — qualifier `bet-bcd524f8…` | Funded by credit `19a3e9d5…`, whose triggering bet is `bet-bcd524f8…`. Sits in an empty cycle of its own instead. |
| `bet-8149d9e9-fbdc-5749-9911-b7ccdc2f4315` (25 Jul 15:23, TAB, $50, Tim) | `a61d684a…` (with `bet-bcd524f8…`) | `1aa7cca6…` — qualifier `bet-2527b525…` | Funded by credit `5e32f0d7…` (Tim's real credit, re-sourced by the S253 fix), whose triggering bet is `bet-2527b525…`. Left grouped with Leigh's qualifier. |

These two are the residue of the 25 July Leigh/Tim wrong-account correction: the **money** side was re-anchored
(the credits now hang off the right accounts and the right bets — verified, 0 account mismatches across all
credits), but the **cycle_id** on these two deployed free bets was not moved with them. No money is affected.

### V3 — Stale deploy event on a corrected cross-account draw (Check 2, informational)

`bet-3b84ec36-c0d0-5bb4-88e4-1dbf0e93f60c` (18 Jul, TAB, $50) carries **two** `free_bet_deployed` events at the
same second, totalling $100 against a $50 bet:

- `031bbd8e…` drew Kate@CrownBet credit `5fb003c4…` — **the S243 cross-account error**, since reversed by
  restore credit `774a6af1…` (19 Jul 17:23).
- `6202dcc6…` drew credit `6e98446e…`, triggering bet `bet-5f6c8ff3…`, which **is** in this bet's cycle.

**Live state is correct**: the free-bet ledger closes and the cycle link is right. The hazard is read-side only:
any surface that sums `total_deployed` per bet without walking the supersession chain will double-count $50 here.
The tool's own inventory walk handles it correctly. **No action needed on the data; flagged so nobody "fixes" it.**

---

## Reconciliation summary

| | |
|---|---|
| Bets audited | **336 (100%, not a sample)** |
| Bets fully coherent | **272 (81.0%)** |
| Bets in a broken link | **64 (19.0%)** — all one defect class, 32 split chains |
| Cycles | **248** |
| Cycles accurately tracked | **184 (74.2%)** |
| Cycles that are half of a split chain | **64 (25.8%)** |
| Free-bet money accounted for | **$2,853.00 of $2,853.00 (100%)** — 8 of 8 account-books cross-foot exactly |
| Corrections that held | **25 of 25 (100%)** |
| Shape defects | **0 of 336** |
| Complete qualifier → free bet → lay chains | **28 of 60 (47%)**; would be 57 of 60 (95%) after repair |

**Checks passed: 5 of 8** (2, 6 partial — see per-check tables). **Checks failed: Check 5 (unpaired lays,
32 violations)**; **Check 2 (2 mis-linked free bets)**; **Check 7 not a failure but a quantified exposure**
(6 cycles / 20 bets split by any date filter).

**100%-of-cycles bar: NOT MET.**

---

## What this audit did NOT check

Being explicit so nothing is assumed covered:

- **P&L arithmetic.** Whether the profit and loss figures are *right* is the other half of 0t and is being
  audited separately. This audit checked that every bet's *links* and *shape* are sound, and that the free-bet
  face-value ledger cross-foots — not that stakes × prices × commission produce the correct dollars.
- **Whether the tool matches the bookmakers.** There is no external source in this database. If TAB's records
  say something different from these 336 rows, this audit cannot see it. The stakes, prices and outcomes were
  taken as given.
- **Whether the 65 uncredited insurance losers genuinely finished outside the paid places.** That needs finishing
  positions, which are not in this database. 44% of lost insurance qualifiers were credited; if the true
  place-rate is materially higher, there are missed credits this audit cannot detect. Worth a targeted check
  against the capture-side results data.
- **Settlement correctness.** Whether a bet marked won actually won. The settlement worker and reconciliation
  were not re-verified.
- **Betfair commission accuracy.** The per-market netting maths (S247 item 2 / S250 0g) was read but not
  re-derived.
- **Capture-side race data.** The twin-row / DR-036 fix, race_date stamping, and the market-id union are
  capture-side and out of scope here — though the 2 Wagga mis-stamped markets on the S259 review list would
  not show up in any check above.
- **The correctness of the *reasons* recorded in corrections.** The audit confirmed the 25 correction records
  are structurally sound and point at real bets; it did not re-litigate whether each operator judgement was right.
- **Anything about cash-flow events** (deposits, withdrawals, transfers) beyond their role in the free-bet
  cross-foot.
