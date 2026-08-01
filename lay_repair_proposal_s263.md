# Lay linkage repair — operator-review proposal (0t-A historical half, S263)

**Prepared:** 2 Aug 2026, from the live store (read-only — nothing has been changed).
**What you asked for:** *"review bets and propose linkage for remaining hedges, I will review to confirm. We want 100% on this for past bets, and for future bets."*
**Design being executed:** `lay_matching_brief.md` §3 (already adversarially reviewed). This document is the review list — nothing runs until you confirm.

---

## What this means for your betting day

Every one of your **32 stranded Betfair lays has exactly one matching free bet** — same horse, same race, logged **1.1 to 4.0 seconds after** the lay went on. No guesswork was needed on any of them: for 30 of the 32 there is only one possible partner in the entire betting history, and for the two Sir Myka lays the clock decides cleanly (details below — those two are the ones worth your closest look).

On top of the 32 lays there are **2 free bets sitting in the wrong group** — leftovers from the 25 July Leigh/Tim wrong-account fix, where the money was corrected but the grouping wasn't. Their correct homes are verified from the funding records.

**So the repair list is 34 moves: 32 lays + 2 free-bet re-groupings. Proposed: 34. Ambiguous: 0. No-match: 0.**

Your 2 deliberately-unhedged free bets from Saturday — **El Pensador $10 (TAB)** and **Syrian Diamond $30 (Ladbrokes)** — are exactly where they should be. They are **not** in the repair list and nothing touches them.

**The future side is already proven: since the automatic linking shipped on 31 July, every single lay — 21 of 21, including all 19 from Saturday's race day — linked itself to its free bet. Zero misses.** Once this repair runs, past and future are both at 100%.

**No money moves.** Not one stake, price, result or per-bet profit figure changes — only which group each bet sits in. (The per-group "Net" lines in BetLog will change, because the groups become correct — that is the point.)

**Confidence: HIGH** on 32 of the 34 moves (only one possible partner exists). **HIGH-with-a-caveat** on the two Sir Myka lays: the two lays are identical twins ($43.10 @ 14.0, two minutes apart), so the clock is the only thing that tells them apart — each lay was followed by its free bet within ~2.4 seconds, while the wrong pairing would be ~100 seconds out or backwards in time. That is the same rule the live linker now applies to every new bet, and the same tiebreak sanctioned back in S246.

### Next steps

1. You review the table below (the two Sir Myka rows especially) and say **go / no-go / changes**.
2. On go: I build the repair script per the reviewed design, rehearse it on a copy of the database, then run it for real — **app closed, backup first, about 5 minutes**, on a quiet (non-race) day.
3. After it runs: the daily money check's pairing watch should show **zero** stranded lays, and the audit re-run should show every insurance → free bet → lay chain in one group.

---

## The proposed pairings — review list (plain language)

"Gap" = how long after the lay went on the free bet was logged. All 32 free bets are on the **same horse in the same race** as their lay.

| # | Date | Horse (race) | Free bet | Lay | Gap |
|---|------|--------------|----------|-----|-----|
| 1 | 22 Jul | 3. Tassoro (Murray Bridge) | $30 — Tim @ TAB | $22.65 @ 12.0 | 1.9s |
| 2 | 22 Jul | 5. Shalhavmusik (Murray Bridge) | $33 — Tim @ TAB | $25.49 @ 7.2 | 2.9s |
| 3 | 22 Jul | 3. Mystic Reign (Sandown) | $12 — Tim @ TAB | $8.56 @ 12.0 | 3.0s |
| 4 | 22 Jul | 2. Justicas Bonus (Murray Bridge) | $22 — Tim @ TAB | $16.98 @ 9.8 | 1.3s |
| 5 | 22 Jul | 4. Carravilla (Doomben) | $50 — Tim @ BetRight | $39.06 @ 6.8 | 3.1s |
| 6 | 22 Jul | 5. Oxley Flyer (Taree) | $50 — Tim @ BetRight | $36.42 @ 8.96 | 4.0s |
| 7 | 25 Jul | 9. Grinzinger Halo (Morphettville) | $50 — Sarie @ TAB | $38.38 @ 9.2 | 1.9s |
| 8 | 25 Jul | 8. Harleynrose (Morphettville) | $50 — Sarie @ TAB | $41.06 @ 21.98 | 2.6s |
| 9 | 25 Jul | 3. Sunset Adios (Gold Coast) | $50 — Sarie @ TAB | $38.62 @ 7.2 | 2.1s |
| 10 | 25 Jul | 7. Murmurs (Mackay) | $50 — Sarie @ TAB | $40.21 @ 14.89 | 1.9s |
| 11 | 25 Jul | 13. The Judge Ruled (Murtoa) | $50 — Leigh @ TAB | $41.61 @ 14.5 | 2.3s |
| 12 | 25 Jul | 2. Pub Crawl (Darwin) | $50 — Leigh @ TAB | $46.34 @ 19.5 | 2.9s |
| 13 | 25 Jul | 3. Cool Magnum (Morphettville) | $50 — Sarie @ TAB | $38.66 @ 5.9 | 2.0s |
| 14 | 25 Jul | 4. Lucky Lass (Mackay) | $50 — Tim @ PointsBet | $38.34 @ 6.6 | 3.5s |
| 15 | 25 Jul | 9. Glouf (Morphettville) | $50 — Tim @ PointsBet | $40.14 @ 8.8 | 1.8s |
| 16 | 25 Jul | 3. Minozza (Roebourne) | $50 — Sarie @ TAB | $41.21 @ 11.0 | 1.9s |
| 17 | 25 Jul | 9. Ambello (Murtoa) | $50 — Sarie @ TAB | $37.75 @ 12.0 | 1.9s |
| 18 | 25 Jul | 1. Macaverty (Darwin) | $50 — Leigh @ TAB | $38.15 @ 8.6 | 2.8s |
| **19** | **25 Jul** | **1. Sir Myka (Morphettville) — first lay 14:44:29** | **$50 — Leigh @ TAB (logged 14:44:31)** | **$43.10 @ 14.0** | **2.4s** |
| **20** | **25 Jul** | **1. Sir Myka (Morphettville) — second lay 14:46:07** | **$50 — Tim @ PointsBet (logged 14:46:09)** | **$43.10 @ 14.0** | **2.3s** |
| 21 | 25 Jul | 13. The Creator (Randwick) | $50 — Leigh @ TAB | $41.04 @ 13.5 | 2.8s |
| 22 | 25 Jul | 8. Pin Deep (Belmont) | $50 — Tim @ PointsBet | $37.59 @ 5.4 | 2.1s |
| 23 | 25 Jul | 1. Anemacore (Eagle Farm) | $50 — Tim @ TAB | $24.10 @ 12.0 | 1.9s |
| 24 | 25 Jul | 7. Heat (Bundaberg) | $50 — Tim @ TAB | $37.57 @ 7.4 | 2.0s |
| 25 | 25 Jul | 3. So Rebellious (Kembla Grange) | $50 — Tim @ TAB | $38.96 @ 7.8 | 1.1s |
| 26 | 25 Jul | 5. Smart Legend (Mackay) | $50 — Tim @ PointsBet | $39.51 @ 14.0 | 2.0s |
| 27 | 25 Jul | 10. The Girls Boy (Darwin) | $30 — Tim @ PointsBet | $24.08 @ 8.8 | 1.8s |
| 28 | 28 Jul | 5. Kota Lambai (Angle Park) | $100 — Tim @ AllBets (goodwill FB) | $79.79 @ 7.6 | 1.7s |
| 29 | 29 Jul | 3. Swag (Eagle Farm) | $25 — Sarie @ TAB | $20.39 @ 10.5 | 1.9s |
| 30 | 29 Jul | 9. The Mean Fiddler (Sandown) | $30 — Leigh @ TAB | $24.51 @ 6.2 | 1.5s |
| 31 | 29 Jul | 5. Gambino (Eagle Farm) | $40 — Leigh @ TAB | $32.63 @ 10.5 | 2.0s |
| 32 | 30 Jul | 1. Cryptonic (Illawarra Grange NZ) | $10 — Sarie @ TAB | $8.06 @ 12.5 | 2.9s |

**Rows 19–20 (Sir Myka) — the two to eyeball.** You laid the same horse twice, two minutes apart, for two different free bets (Leigh's TAB one, then Tim's PointsBet one), and the two lays are identical. The pairing above says: **first lay ↔ Leigh's free bet, second lay ↔ Tim's free bet** — because each free bet was logged ~2.3 seconds after its lay, in order. The cross-pairing would mean you logged a free bet 100 seconds before/after its lay, which never happens anywhere in your history. If your memory of that afternoon says otherwise, say so and I'll swap them.

### Plus the 2 free bets in the wrong group (Leigh/Tim fix leftovers)

| Free bet | Where it sits now | Where it belongs | Why |
|---|---|---|---|
| **The Creator** $50 FB (Leigh @ TAB, 25 Jul 15:00) | A group of its own | With **Forgotten Spirit** $50 qualifier (Leigh @ TAB, Eagle Farm) | Its funding record says Leigh's credit came from the Forgotten Spirit bet — the correction note on file says exactly this |
| **So Rebellious** $50 FB (Tim @ TAB, 25 Jul 15:23) | With Leigh's Forgotten Spirit qualifier (wrong person's group) | With **Horizons** $50 qualifier (Tim @ TAB, Randwick) | Its funding record says Tim's credit came from the Horizons bet |

These two move FIRST, and their lays (rows 21 and 25 above) then follow them into the corrected groups — otherwise those two lays would be re-stranded.

### Deliberately unhedged — no action, listed so nothing looks forgotten

| Free bet | Status |
|---|---|
| 9. El Pensador $10 (TAB, Townsville, 1 Aug) | Intentional no-hedge — **stays as is** |
| 3. Syrian Diamond $30 (Ladbrokes, Doomben, 1 Aug) | Intentional no-hedge — **stays as is** |

Both are back bets (not lays), both settled, and both drop off the daily watch naturally — the watch only flags a missing hedge in the first 24 hours.

### Future bets — the other half of your 100%

Every lay placed since the automatic linker went live (31 Jul 09:33) was checked against the store: **21 of 21 are linked** — 2 on Friday (Geelong, including the first-ever live auto-pair), 19 on Saturday's race day. Every one sits in a group with its free bet (and in 17 of 21, the qualifier as well — the full insurance → free bet → lay story in one group; the other 4 are Ladbrokes free bets whose group correctly holds just the free bet + its lay). **The future side needs no repair.**

---

## Honest statement of anything ambiguous

There is exactly one place where the evidence is timing rather than uniqueness: the two Sir Myka lays (rows 19–20). The two lays are indistinguishable from each other ($43.10 @ 14.0, same market, same horse), so horse/race/stake cannot tell them apart — only the clock can, and it does so cleanly (each lay is followed by exactly one free-bet log within 2.4s / 2.3s; the cross-match is +100.3s / −95.6s, and a free bet logged *before* its lay occurs nowhere in the 32). This is the same rule the shipped forward-linker applies to every live bet, and both assignments settle to the same books your records already name (Leigh@TAB, Tim@PointsBet), so no plausible mis-assignment changes any money — but it is the one pairing resting on seconds rather than on a unique partner, so it is flagged for your explicit confirmation rather than waved through. Everything else in this proposal has exactly one possible answer.

---

# Technical appendix

## A1. Derivation (re-run 2 Aug 2026 against the live store, read-only)

- Store now holds **466 bets / 339 distinct cycles / 82 LAYs** (grown from the audit's 336/248/61 — 1 Aug race day since).
- Unlinked population re-derived, not taken from the audit: **LAY whose cycle holds no non-LAY bet → 32 rows**, identical to the audit's V1 list (no new stranded lays since 30 Jul; none of the 32 self-healed).
- All 32 lays are **solo in their cycles** (no multi-lay cycles). Zero prior `bet_mutation_events` on any of the 34 bets — clean slate.
- Candidate resolution (forward-linker's own rule: same `betfair_market_id` + `betfair_selection_id`, `lay.placed_at < back.placed_at`, delta ≤ 30s, target cycle holds no LAY on that selection):
  - 30 lays: **exactly one** back exists on the market+selection in the entire store. All deltas 1.1–4.0s. All candidates are free-bet backs.
  - 2 lays (Sir Myka, market `1.260297597` sel `100920222`): two candidates each on market+selection alone; the rule eliminates one each (delta +100.3s > 30s window; delta −95.6s violates lay-before-back) → **exactly one candidate each**. Assignment is 1:1 and order-consistent.
  - The mapping is a bijection: 32 distinct lays → 32 distinct FBs in 32 distinct cycles.
- **L3 fence verified:** all 32 target cycles hold **zero lays** (30 are {1 cash qualifier + 1 FB}; `1aa7cca6…` is {qualifier only — its FB arrives in this repair}; `ef657283…` is {goodwill FB only, fresh-cycle-by-design, S256 AllBets}).
- FB-side mirror check: FB backs with no lay in cycle → **34 rows** = the 32 pairing targets + El Pensador + Syrian Diamond. Reconciles exactly with the money check's 34.
- The money-check "34" decomposes as: 32 via `list_unpaired_lays` (30-day window) + 2 via `list_fb_conversions_missing_lay` (24h window, both 1 Aug). Post-repair expectation: **0 + 0** (the 2 intentional have already aged out of the 24h window).

## A2. The 32 lay moves (bet id → from-cycle → to-cycle, in `placed_at` order)

Format: `lay bet_id | lay placed_at | from cycle | to cycle (= FB's cycle) | FB bet_id | FB logged_at | delta`

| # | Lay | Placed | From | To | FB | FB logged | Δs |
|---|-----|--------|------|----|----|-----------|----|
| 1 | `bet-df4dd0bb-b7bf-41af-8322-8aee25a85e85` | 22 Jul 13:18:29 | `cycle-1ca6fcd7-d8bb-4aaa-9a3b-2e08968aa82b` | `85fcaafd-5332-4fdf-bc9f-77e648349a2a` | `bet-e138d477-befa-5a3f-ab7b-df2eea91c15e` | 13:18:30.877 | 1.9 |
| 2 | `bet-898e82a4-7b5d-4773-9a91-b4ce37e1c28a` | 22 Jul 13:51:35 | `cycle-e9af2715-01c2-4255-9869-1b2375e29a96` | `ea497ba4-9eee-4098-bf3c-75ba5efe7c3f` | `bet-e9a53d63-f4dc-5e0d-9326-59aae31ec96c` | 13:51:37.851 | 2.9 |
| 3 | `bet-e36d3821-f3e0-4acf-87d8-be288055320d` | 22 Jul 14:12:37 | `cycle-d8c6da5a-0103-405b-8950-844ebfb2d84a` | `2dcfb2c4-09a2-4256-8749-fb3937957562` | `bet-032b087f-3465-53b7-9ea5-46f53ddcd234` | 14:12:39.970 | 3.0 |
| 4 | `bet-26d63e92-58ea-44f1-b7c6-3760c489c6c9` | 22 Jul 14:16:53 | `cycle-0d7bdbc6-1995-47bf-b60b-bdd65e09835c` | `978b1d39-f51b-4482-9522-720fab226808` | `bet-e4433685-d2de-501f-847b-edbc29da941c` | 14:16:54.310 | 1.3 |
| 5 | `bet-107f3175-4448-42c7-bbfd-2518c22a45db` | 22 Jul 15:28:53 | `cycle-7726ea57-8a1f-4238-a87a-64500cc2bbc4` | `ade2e7b9-e78f-4041-910d-3127de9a7490` | `bet-ea6d006c-ce2f-5081-b93b-70ba8b1836c4` | 15:28:56.142 | 3.1 |
| 6 | `bet-d1cbf340-c94e-477b-abc4-6a7676e5dabc` | 22 Jul 16:36:19 | `cycle-a1be07df-ecfc-46fb-a924-0686b452c4c3` | `e2335b71-1287-41eb-8b0a-3944583a0c61` | `bet-141b0bae-69d7-5a3a-82fb-7680fe213929` | 16:36:23.024 | 4.0 |
| 7 | `bet-3b4bb91f-543b-4c8e-8a0a-d70ead4cdbde` | 25 Jul 11:51:51 | `cycle-797c4f9d-9cb2-4b64-9e23-698076e612af` | `4ed5da74-89dd-4373-9db6-c24eda95d3e3` | `bet-c9c57c5f-24ed-5943-9ee7-08b1275bb476` | 11:51:52.869 | 1.9 |
| 8 | `bet-a7eddb87-2b83-4057-ae4a-24d9e02cb856` | 25 Jul 12:20:22 | `cycle-18ff70da-e19f-47ae-b5a7-c0db614106f9` | `a98ac6f8-9467-4646-929b-acda3044547d` | `bet-a0b71d05-270c-5b96-97ca-fbe82a0dc5af` | 12:20:24.643 | 2.6 |
| 9 | `bet-8f20497f-d85b-410c-b204-022b5144e305` | 25 Jul 12:35:43 | `cycle-a1bd15b2-d3b6-4b5b-8226-8818327b2a72` | `c6c8c950-e8b9-4856-8c01-994f17a6eb2f` | `bet-4154f501-b769-59e9-94c3-25264137aab3` | 12:35:45.068 | 2.1 |
| 10 | `bet-fa4798db-0f80-49f6-a3ac-3d17a80ed322` | 25 Jul 12:56:00 | `cycle-0c5ad927-a557-4ffa-8a9c-5d4305e741af` | `a47666f8-1be2-4eac-8bfb-c89541fe32dc` | `bet-20d91e61-afec-5499-80c7-d304fff100ca` | 12:56:01.946 | 1.9 |
| 11 | `bet-5421d5a0-3a4d-4ce9-9999-a26c55ce9057` | 25 Jul 13:03:01 | `cycle-d18fda57-9ce3-41d7-8565-a10754070f14` | `e21ce13f-2091-4cc6-a58f-6a7efc523e4d` | `bet-90de9026-3f1f-59ce-8111-77d6d1c936b4` | 13:03:03.269 | 2.3 |
| 12 | `bet-fe4e76bd-3c06-4db3-a83e-488947f8f9c3` | 25 Jul 13:18:49 | `cycle-86281152-e53e-4a90-9f60-0388a47f1948` | `6f2ac443-34c5-42d6-83e6-e93fdcd6e990` | `bet-725a719f-c4d6-581c-a6a4-2acaff4d1541` | 13:18:51.854 | 2.9 |
| 13 | `bet-1f154431-8649-453d-b363-20111b140346` | 25 Jul 13:35:52 | `cycle-5d16d162-ab38-4faa-a967-a8e22118785a` | `b64a2391-bb6f-4a93-a87b-07b3c69d0855` | `bet-a4189c05-4174-541b-b677-2816e551ccbc` | 13:35:54.023 | 2.0 |
| 14 | `bet-1cea5a27-555b-4b82-9be8-0d200cd6316d` | 25 Jul 14:05:18 | `cycle-47caafd9-2b73-48cc-b913-8970ed440e17` | `5e7824db-6e14-40c1-9661-d202bbef8247` | `bet-ff5eba56-1219-5299-8b8b-c662f6103556` | 14:05:21.472 | 3.5 |
| 15 | `bet-f7c31d01-005b-426c-801c-604cb664db83` | 25 Jul 14:06:13 | `cycle-75a840b0-4b79-49c3-8afb-f1d289e40e7d` | `2783fb07-b9e3-4a86-ba30-a9213faaba21` | `bet-d17232dc-2ba6-5ecf-a736-799341a06362` | 14:06:14.761 | 1.8 |
| 16 | `bet-8b93d5a0-89e3-4acd-8ec7-060962d3e5cd` | 25 Jul 14:12:42 | `cycle-6fa43cf7-a8bb-4cca-bf49-a34dbfac547c` | `2bb98542-c72d-4c91-aaac-2294866c191f` | `bet-cac3e931-cfda-53a6-ab71-49dfa0370d7a` | 14:12:43.920 | 1.9 |
| 17 | `bet-dc66d03f-27ba-42a5-812d-2f0b1ea9db01` | 25 Jul 14:14:30 | `cycle-eb1a184d-96f4-4de2-b581-a34173a0a139` | `034b21a3-366e-429b-b33e-cfac8d11ef57` | `bet-0856d032-db64-5899-b909-2a2525160924` | 14:14:31.934 | 1.9 |
| 18 | `bet-a7aa03c1-722e-4519-9fb5-e2d9e400b844` | 25 Jul 14:36:25 | `cycle-bf837dbe-f392-4182-bcbb-6618a94d6e28` | `7c033b5b-5cc5-47be-9482-db3da9b375e6` | `bet-8724d8e4-519f-5e93-bc72-3a3be92fdd9e` | 14:36:27.814 | 2.8 |
| 19 | `bet-8b7f04c7-cbed-4d34-91d1-5474e13c5291` | 25 Jul 14:44:29 | `cycle-95e3e3d3-205e-407b-820e-d3322e408fb4` | `8d04db69-34c6-4ca5-ad5f-0325471173ac` | `bet-94a4365c-249b-5dfc-8fd3-5ff3a9b5a7c9` (Leigh@TAB) | 14:44:31.372 | 2.4 |
| 20 | `bet-0b244c21-f583-4df2-ab07-a28de9898814` | 25 Jul 14:46:07 | `cycle-b967405c-220d-4222-995e-4e0c30de7a4e` | `d8425837-c0b9-49ec-91ed-2e412f107ca8` | `bet-9c47ffd9-37e7-5a73-b3b7-55d68a11514f` (Tim@PointsBet) | 14:46:09.255 | 2.3 |
| 21 | `bet-0a498911-7ff7-48cb-84e6-bea987f2c530` | 25 Jul 14:59:59 | `cycle-f4443d6b-1182-489d-a1b9-0ee3f629a7a2` | `a61d684a-c968-47e2-8e63-f1993a2225f3` **(FB's corrected cycle — after move R1)** | `bet-76ae5c5a-7652-5975-942c-cc71c93f5d65` | 15:00:01.786 | 2.8 |
| 22 | `bet-dc224ee5-75c8-4cd0-a43c-3fcf0bf7e749` | 25 Jul 15:07:23 | `cycle-7045ad55-db57-47c9-b191-3c9716603b54` | `bd90046e-d019-4339-91aa-d1882c620b8d` | `bet-7015f52d-23ca-5a89-b54f-3f8b00800e2d` | 15:07:25.131 | 2.1 |
| 23 | `bet-820cdb27-9376-49f1-98d7-bb9fb6fa8145` | 25 Jul 15:10:29 | `cycle-bba61462-f529-4370-ba21-f4ab2f705eb4` | `acf6b8f0-50ad-4f98-9579-8b9b58ded452` | `bet-d670e447-9431-53f9-a0b1-c748fe68ff48` | 15:10:30.895 | 1.9 |
| 24 | `bet-604689b0-a51e-41eb-ad33-be6022ddd4db` | 25 Jul 15:21:50 | `cycle-12bac4c9-3f08-4bc8-a000-4ccedf957f12` | `df2462a7-5f6d-46a3-b777-88adc24d6dbc` | `bet-d6d605f3-f817-5f70-a750-48f096b7ee4c` | 15:21:52.007 | 2.0 |
| 25 | `bet-d67c5ffe-485f-4406-bd1f-d85b7f16f7e3` | 25 Jul 15:23:05 | `cycle-268a329e-2200-42b5-b14a-254877b7e0bc` | `1aa7cca6-c9f5-4acc-b3b8-afea39e6fbc2` **(FB's corrected cycle — after move R2)** | `bet-8149d9e9-fbdc-5749-9911-b7ccdc2f4315` | 15:23:06.136 | 1.1 |
| 26 | `bet-dcba3c74-4e14-4a14-9c99-ecef42341557` | 25 Jul 15:28:16 | `cycle-f5a04655-334d-4ca2-ab71-3b986b7016b3` | `bdc025bf-8db9-4fe5-b87e-3de0b25c0e56` | `bet-ad852eef-8a59-573f-b355-563d58a83677` | 15:28:18.041 | 2.0 |
| 27 | `bet-ae65da03-d372-4ca0-8fe1-a20e404ed180` | 25 Jul 17:03:22 | `cycle-4a4bb72b-831c-460a-b17a-98a1c7b4e836` | `2998620d-312b-408c-b00b-a3b72ffcfb0b` | `bet-84c6725d-f9df-580c-bdc2-a3e1dd1e6434` | 17:03:23.841 | 1.8 |
| 28 | `bet-44ac9e9a-541c-4124-b72a-d0f8e544086f` | 28 Jul 13:06:21 | `cycle-82f731a2-9f4b-4b4c-b05c-767741d90b5e` | `ef657283-bc83-4746-9343-5111fc03c31c` | `bet-8b3a1ce1-0aca-5ba0-a0cc-f7a1bdaba1a5` | 13:06:22.715 | 1.7 |
| 29 | `bet-1a556402-6e80-4c8b-92dd-9ab29a59beda` | 29 Jul 14:47:23 | `cycle-e1d3cd40-255c-4abb-aff9-f063a3434eb0` | `a4e0c238-90f2-47a2-b7d6-d6bb6a009a4c` | `bet-ddc32e68-f550-53c9-bad7-dc9e667d1162` | 14:47:24.891 | 1.9 |
| 30 | `bet-4ecb7087-1a91-4f90-a68f-a8c84549b69f` | 29 Jul 15:22:03 | `cycle-26ae9fb0-bc40-4fee-88da-f3aacabb4c87` | `d5fba9b3-d404-40c3-8dd1-58f6045ab85a` | `bet-389f3f0b-846b-55b4-a684-ee1804866808` | 15:22:04.479 | 1.5 |
| 31 | `bet-bd4cda8a-9d39-4d7e-b37a-d0993b5c2881` | 29 Jul 15:23:53 | `cycle-cc0de1c1-5842-4431-bdda-94f6cc85bba9` | `c2d98124-a491-4970-aef0-97662873286f` | `bet-a93fe58b-6515-5948-96bc-4128b519de81` | 15:23:55.003 | 2.0 |
| 32 | `bet-24b99ae1-0643-42a7-a68a-d5f047a6ec65` | 30 Jul 15:30:44 | `cycle-e58a93bb-db72-4fd5-937d-8ce88af44297` | `9274169d-bce0-4377-9159-4c2539e77af9` | `bet-b415ab8b-8ae2-5123-9e6a-f54e5de4bb47` | 15:30:46.902 | 2.9 |

Sir Myka evidence in full (market `1.260297597`, sel `100920222`): lay 14:44:29 sees FB@14:44:31.372 (+2.4s, in-window) and FB@14:46:09.255 (+100.3s, out-of-window) → one candidate. Lay 14:46:07 sees FB@14:44:31.372 (−95.6s, back-before-lay, excluded) and FB@14:46:09.255 (+2.3s) → one candidate.

Row 32's target `9274169d…` is the 30 Jul promo-selection-correction cycle the audit's Check 6 verified end-to-end; the lay joining it completes that story.

## A3. The 2 FB re-points (run FIRST — R1, R2)

Funding chains re-verified 2 Aug against live `promo_events` (not taken on trust from the audit):

| Move | Bet | From cycle | To cycle | Evidence |
|---|---|---|---|---|
| R1 | `bet-76ae5c5a-7652-5975-942c-cc71c93f5d65` (The Creator FB, Leigh@TAB) | `fc14344a-df4c-4f38-a6bb-61545947374f` (alone) | `a61d684a-c968-47e2-8e63-f1993a2225f3` | Active deploy event `60b175eb…` (notes: "S253 wrong-account correction: Leigh's earned credit (Forgotten Spirit qualifier bcd524f8)…") draws credit `19a3e9d5…` → triggering bet `bet-bcd524f8-4f9d-56ea-9b75-debc492b6be5` (Forgotten Spirit, Eagle Farm) whose cycle is `a61d684a…` |
| R2 | `bet-8149d9e9-fbdc-5749-9911-b7ccdc2f4315` (So Rebellious FB, Tim@TAB) | `a61d684a-c968-47e2-8e63-f1993a2225f3` (wrongly with Leigh's qualifier) | `1aa7cca6-c9f5-4acc-b3b8-afea39e6fbc2` | Deploy event `19dd4d9b…` draws credit `5e32f0d7…` (Tim@TAB, re-sourced by S253) → triggering bet `bet-2527b525-57df-5f9b-abaf-4a88050d2c57` (Horizons, Randwick) whose cycle is `1aa7cca6…` |

Ordering is **necessary, not stylistic**: without R1/R2 first, lays 21 and 25 would land in `fc14344a…` / alongside the wrong qualifier and re-strand (brief §3 + review confirmation).

## A4. Future-side verification (the "100% for future bets" half)

Query: all `side='LAY'` with `placed_at >= 2026-07-31T09:33` → **21 lays; 21 of 21 have a non-LAY bet in their cycle. Zero misses.**

- 31 Jul: 2 (Inside Job, Prevention — Geelong; Inside Job is the first-ever live auto-pair, 1.43s).
- 1 Aug: 19, across Rosehill / Morphettville / Townsville / Hamilton / Gilgandra / Gold Coast / Belmont / Doomben / Flemington / Newcastle. 17 of 19 cycles hold the full {cash qualifier + FB + lay}; 2 (Excess Baggage, Just Flying — Ladbrokes FBs) hold {FB + lay} with no qualifier back in-cycle, same shape as the 31 Jul pair — consistent with those FBs' funding, not a linker miss.
- One minor observation, no action: lay `bet-52a3614f…` (Calmundi, Gilgandra 1 Aug) has `matched_stake = 0` (fully unmatched) — it still linked correctly; money handling of $0-matched lays was closed in the B3 investigation.

## A5. Execution plan (per brief §3 + normative v2 review; runs only on your go)

1. **Build** `ops/repair_lay_cycles.py` (does not exist yet) on the `ops/correct_promo_selection.py` template: dry-run by default, `--apply` to commit. Moves hard-coded from this reviewed proposal (R1, R2, then rows 1–32 in `placed_at` order).
2. **Per the review's L2 (binding):** every move is a **raw** `UPDATE bets SET cycle_id = ?` plus a raw-inserted `bet_edited` mutation event, both inside ONE `BEGIN IMMEDIATE` transaction on a fresh bare connection with `PRAGMA foreign_keys=ON` — never the `update_cycle_id` adapter (its separate autocommit connection is the split-commit trap). One transaction for all 34 rows; crash = clean rollback of everything.
3. Each `bet_edited` payload: before/after snapshot **identical** (the no-money-moved proof), from→to cycle in `notes`. 34 events total.
4. **Rehearsal:** copy the live DB; run `--apply` on the copy; assert (a) per-bet `bet_net_pnl` and the all-bets total byte-identical before/after, (b) all 34 payloads have before == after, (c) verification queries below pass on the copy.
5. **Live run:** quiet non-race day, **app closed**, backup first (`cp` of `bethub.db` + `-wal` + `-shm`, name `bethub.db.pre-layrepair-YYYYMMDD-HHMMSS`, per the 29 Jul promo-swap precedent). Dry-run must print exactly this proposal's 34 moves; any drift (new bets, changed rows) = stop and re-review. Then `--apply`. ~5 minutes.
6. **Verification (after apply):**
   - Unpaired lays (the A1 derivation query, no window) → **0**.
   - FB backs with no lay in cycle → **2** (El Pensador `bet-d967e395…`, Syrian Diamond `bet-def9f12c…`) and nothing else.
   - `SELECT COUNT(DISTINCT cycle_id) FROM bets` → **306** (339 − 32 vacated solo lay cycles − `fc14344a…` vacated). (The brief's 215 was against the audit-era 248; the store has since grown — same arithmetic, −33.)
   - The 33 vacated cycle ids appear on zero bets.
   - 34 new `bet_edited` events, each pointing at a real bet, before == after.
   - `uv run python -m ops.settlement_review` → CYCLE PAIRING WATCH clean.
   - Complete qualifier→FB→lay chains: 28 → ~60 of the eligible population (audit Check 5 metric); re-run the integrity audit's Check 5 for the formal 100% sign-off.
7. **Rollback:** restore the backup, or reverse from the 34 `bet_edited` events (each records from→to).

## A6. Classification summary

| Class | Count | Rows |
|---|---|---|
| **PROPOSED** | **34** | 32 lay moves (A2) + 2 FB re-points (A3) |
| AMBIGUOUS | 0 | — (Sir Myka pair resolves to exactly one candidate each under the shipped linker rule; flagged for explicit operator confirmation anyway) |
| NO-MATCH | 0 | — |
| INTENTIONAL | 2 | El Pensador $10 FB (TAB), Syrian Diamond $30 FB (Ladbrokes) — unhedged backs, excluded from repair |

Derived 2 Aug 2026 from the live store. If bets are placed before the repair runs, the script's dry-run re-derives and must reproduce this table exactly before `--apply` is allowed.
