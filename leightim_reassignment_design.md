# Reassignment operation + Leigh/Tim fix — DESIGN

## ✅✅ EXECUTED ON LIVE — 2026-07-26 11:09 (Sun), app down, VERIFIED CLEAN
- Script: `scratchpad/fix_leightim.py` (raw SQL, one BEGIN IMMEDIATE, no adapter
  pre-commit, payloads via domain models + `_event_to_row`). Verifier:
  `scratchpad/verify_leightim.py` (app's real derivations).
- **THREE independent reviews before execution:** design (reviewers A+B on copies)
  + a FINAL adversarial review of the ACTUAL script on its own fresh copy
  (byte-level table diff, GO verdict). My own dry-run on `copy1.db` reproduced the
  exact end-state first.
- **Live pre-write md5** `06370345…` (no drift) → **post-write** `d054cd51…`.
  Fresh pre-write backup `~/.bethub/backups/bethub-PRE-leightim-EXEC-20260726-110903.db`
  (+ the 10:01 one) both chmod 444. New event ids: op3 deploy
  `60b175eb-8328-404e-ad21-49d2cd170b9e`, op5 audit
  `7a845ee2-e3e9-421e-8d72-2cf8e5b58035`.
- **Post-commit on live matched the copy to the cent:** Tim cash 2682.20→2732.20
  (+$50), Leigh 2007.80→1957.80 (−$50), GLOBAL cash conserved (11555.686…), Tim
  FB-in-hand 1→0 (phantom gone), Leigh FB 0 (credit now consumed by The Creator),
  The Creator orphan→grouped, Forgotten Spirit still credited, So Rebellious row
  untouched ($300 Tim, conv NULL). `integrity_check` ok, FK clean, no
  double-consume, 0 chain-account mismatches, 141 promo rows / 0 bricked.
- **Follow-ons (not done):** productionise the reassign-account door
  (endpoint + BetLog UI + faithful `bet_reassigned` audit); optional cycle-id
  tidy for the accepted cosmetic residue.
- **Note on `bet_reclassed`:** S253 final check found the DB already allows a
  `bet_reclassed` mutation type — but it is for terminal-STATE re-class
  (won/lost/void), `BetSnapshot` has no account field, emitted by
  `void_recheck.py`. NOT for account moves. Reviewed `bet_edited` decision stood.

## ✅ REVIEW-CONFIRMED FINAL (2 independent adversarial reviewers, both on DB copies)
- **End-state CORRECT — proven twice.** Reviewer A ran a 21-check table on a
  copy using the app's real derivations: Tim cash 2682.20→2732.20 (+$50), Leigh
  2007.80→1957.80 (−$50), So Rebellious +$300 stays Tim (bet row untouched,
  conversion NULL), Tim FB-in-hand 1→0 (phantom gone), Leigh FB unchanged with
  The Creator now grouped (orphan 1→0), self-check green/unchanged, chain-account
  coherence 0 mismatches, no double-consume, FK clean, journey-state identical,
  all mutated/new rows re-hydrate byte-faithful. Reviewer B independently
  reproduced the same deltas. Both live-DB checks: UNTOUCHED.
- **FINAL MECHANISM (do exactly this):**
  1. RAW SQL only, ONE `sqlite3` connection, `PRAGMA foreign_keys=ON`, one
     `BEGIN IMMEDIATE…COMMIT`. Construct NO repo/adapter/workflow object before
     COMMIT (they auto-commit — proven).
  2. Build op-1's rewritten payload and op-3's new `free_bet_deployed` payload as
     `FreeBetDeployedPayload`/`PromoEventBase` objects serialized via
     `_event_to_row` (exact "50.00" strings, dashed UUIDs, invariants) — then raw
     INSERT/UPDATE the strings. NEVER hand-JSON (a float bricks the row on read).
  3. Op ORDER is mandatory (unique-superseder index): 1 (re-source So Rebellious
     off `19a3e9d5`) → 2 (move credit to Leigh) → 3 (new Leigh deploy supersedes
     `19a3e9d5`, groups The Creator) → 4 (move qualifier bet to Leigh) → 5 (audit).
     Wrong order fails LOUD (safe), never silent.
  4. Op-5 audit = **`bet_edited`** with the from/to Tim→Leigh triplet + correction
     reference in `notes`. **NOT `bet_reassigned`** — that value fails the DB
     CHECK and rolls the whole txn back. A faithful structured audit
     (`bet_reassigned` + enum/CHECK rebuild migration) is a FOLLOW-ON, not needed
     for this fix.
  5. In-txn pre-COMMIT asserts (raw SQL): chain-account coherence = 0; no
     double-consume; `foreign_key_check` clean; **explicit** qualifier
     `account_at_book_id == 58f3d93a…` (bets has NO FK, so foreign_key_check
     can't see op-4); S243 (each deploy's account == its deploying bet's account).
     If any fail → ROLLBACK (still safe here, before any adapter constructed).
  6. Then, POST-COMMIT, construct the adapters and run
     `compute_free_bet_inventory` + `compute_account_at_book_balance` +
     `list_source_pending_spends` + `list_uncredited_qualifiers` +
     `pnl_dashboard` as CONFIRMATION. Any anomaly ⇒ RESTORE THE BACKUP (not
     rollback). DO NOT assert FB-face net-zero (it goes $50→$0 by design).
  7. **Full dry-run on a throwaway copy first**, run the post-commit derivations
     THERE; only if clean, replay the identical raw SQL on the live DB.
- **Cosmetic residue, ACCEPTED (not fixed — minimal-change):** `cycle_id`
  `a61d684a` will span two accounts and the So Rebellious deploy's correlation
  won't match its new source. Audit/journey-only, changes NO money, harmless per
  both reviewers. Left untouched to avoid an unverified change; a cycle tidy is
  optional follow-on.
- **Standing checks after relaunch:** account_watchdog is Betfair-only ⇒ this
  all-TAB fix is invisible to it; settlement_review/reconciliation untouched.

---

# (original design below — superseded by the FINAL block above where they differ)

# Reassignment operation + Leigh/Tim fix — DESIGN (for adversarial review)

Money-ledger correction. App is DOWN. Pre-fix backup:
`~/.bethub/backups/bethub-PRE-leightim-creditfix-20260726-100118.db`. No live
changes made yet. This design is to be adversarially reviewed BEFORE building.

## 1. What we're correcting (operator-confirmed truth)
- Forgotten Spirit qualifier (Eagle Farm R4, $50 cash back, settled_lost) is
  **Leigh's**, mis-placed on **Tim**.
- Its $50 free-bet credit is **Leigh's**; Leigh spent it on **The Creator**
  (Randwick R8 free bet, settled_lost).
- The **$300 So Rebellious** free-bet win is legitimately **Tim's** — Tim had
  its own real $50 credit (`5e32f0d7`, 13:13, verified un-superseded/spare).
- The ledger instead recorded: qualifier→credit→So Rebellious as ONE consumed
  chain on Tim (cycle `a61d684a`); The Creator is an orphan free bet on Leigh
  (cycle `fc14344a`, no deploy event). So the tool auto-sourced the credit to
  the WRONG free bet.

## 2. Domain facts that constrain the design (from 3 investigators)
- **Cash P&L** = per-`bets`-row by `account_at_book_id` only. Moving a bet's
  `account_at_book_id` moves its P&L. (`balance_derivation.py`)
- **Free-bet in-hand** = a per-account **`supersedes_event_id` chain walk**; a
  credit is in-hand iff its chain terminal is still `free_bet_credited`.
  `source_credit_event_ids`, `draw_down_breakdown`, `cycle_id`, `correlation_id`
  are **NOT load-bearing for money** (audit/journey only).
  (`promo_derivations.py:157-256`)
- **Self-check = CASH ONLY and GLOBAL** — cannot see free-bet corruption, and is
  insensitive to WHICH account P&L lands in. ⇒ verification MUST add per-account
  cash + free-bet-chain coherence checks.
- **Invariants to preserve:** (a) a credit + every event in its supersedes chain
  + the two bets share ONE `account_at_book_id`; (b) S243 deploy guard: a
  deploy's credit account == deploying bet's account (`fb_deployment.py:195`);
  (c) `uq_promo_events_supersedes` — each event superseded ≤ once; (d)
  once-per-qualifier credit guard; (e) promo_events FKs (account_id, book_id,
  account_at_book_id) resolve to a real `accounts_at_book` triplet.
- **The promo spine is APPEND-ONLY** — no `update_row`/`delete_row`; the app has
  NEVER mutated a promo_events row. `revoke`/`restore` copy the account forward
  unchanged — there is **no "re-anchor a live credit to a new account" verb**.
- **This case is already-consumed** (credit already superseded by the So
  Rebellious deploy), so the clean append-based "supersede-to-re-anchor" is
  **blocked** by the single-superseder index. ⇒ the mechanism must be a raw,
  in-place, transactional UPDATE (investigator-2 Option 1) — the tool is the
  first writer to mutate `promo_events`.

## 3. The exact target end-state
Chain X (Leigh): qualifier `bcd524f8` → credit `19a3e9d5` → deploy (NEW) →
The Creator `76ae5c5a`. All Leigh@TAB. Credit consumed by The Creator.
Chain Y (Tim): Tim real credit `5e32f0d7` → deploy `19dd4d9b` → So Rebellious
`8149d9e9`. All Tim@TAB. $300 stays Tim.

## 4. Mechanism — ONE transaction, `PRAGMA foreign_keys=ON`, verify-before-commit
Leigh@TAB triplet: account_id `8b723c2b…`, book_id `1f56df19…` (TAB, unchanged),
account_at_book_id `58f3d93a…`. Tim triplet: account_id `ef9cf678…`, same book.

Ops (single `BEGIN IMMEDIATE`):
1. **Re-source So Rebellious** — `UPDATE promo_events` id `19dd4d9b`:
   `supersedes_event_id` `19a3e9d5`→`5e32f0d7`; rewrite payload
   `source_credit_event_ids` + `draw_down_breakdown.credit_event_id` to
   `5e32f0d7`. Account stays Tim. (Frees `19a3e9d5`; consumes `5e32f0d7`; S243 ok
   — both Tim.)
2. **Move credit to Leigh** — `UPDATE promo_events` id `19a3e9d5`: account triplet
   → Leigh. (Now free — no superseder yet.)
3. **Group The Creator** — INSERT a `free_bet_deployed` promo_event, Leigh
   triplet, `supersedes_event_id`=`19a3e9d5`, payload
   `deploying_bet_id`=`76ae5c5a`, `source_credit_event_ids`=[`19a3e9d5`],
   `draw_down_breakdown`=[{`19a3e9d5`,`50.00`}], `total_deployed`=`50.00`,
   `event_id`=uuid4, recorded=occurred=now, source=`operator`,
   correlation_id=The Creator's cycle. Built by MIRRORING the validated
   `FreeBetDeployedPayload` shape exactly. (Consumes `19a3e9d5` on Leigh; S243 ok
   — credit Leigh == The Creator Leigh.)
4. **Move qualifier bet** — `UPDATE bets` id `bet-bcd524f8`:
   `account_at_book_id`→Leigh (book_or_exchange stays `tab`). (−$50 cash → Leigh.)
5. **Audit** — INSERT a `bet_mutation_events` row (reuse `bet_edited`, or add a
   `bet_reassigned` type) recording the qualifier account move + a note pointing
   at this correction.

Then run §5 verification IN the same transaction; COMMIT only if all pass, else
ROLLBACK.

## 5. Verification (self-check is insufficient — these prove clean)
Compute BEFORE (from the backup) and AFTER (pre-commit), assert:
- **Cash, global:** self-check identity still `difference==0.00`.
- **Cash, per-account:** Tim P&L +$50 vs before (qualifier loss leaves);
  Leigh P&L −$50 (loss lands); So Rebellious +$300 still on Tim; net global 0.
- **Free-bet chain coherence (the unchecked invariant):** every
  `promo_events.supersedes_event_id` points at an event whose
  `account_at_book_id` equals the successor's (0 mismatches). Both chains
  single-account.
- **No double-consume:** `GROUP BY supersedes_event_id HAVING COUNT(*)>1` empty.
- **Inventory:** Tim free-bets-in-hand −1 ($50 — the phantom gone); Leigh
  unchanged in count but The Creator now grouped.
- **Orphan/credit-gap parity:** `list_source_pending_spends` — The Creator no
  longer orphan; `list_uncredited_qualifiers` — Forgotten Spirit not newly
  uncredited. So Rebellious not newly orphaned.
- **FK integrity:** `PRAGMA foreign_key_check` clean.

## 6. Rollback / safety
Backup taken. All ops in ONE transaction — any failed check ⇒ ROLLBACK (no
partial state). After COMMIT, relaunch the app and re-confirm the self-check +
both accounts' balances in the UI; if anything is off, restore the backup
(app-down) and escalate. TAB is a soft book ⇒ no Betfair watchdog involvement.

## 7. Tool generalization (the recurring need)
The reusable "reassign a bet to the correct account" tool is the clean-whole-
chain case: move a bet + its (account_at_book, chain) events to a target account
via the same transactional in-place account-triplet UPDATE, keeping structure,
with these same verifications, emitting `bet_reassigned`. THIS fix additionally
needs the deploy **re-sourcing** (op 1) + **regroup** (op 3) because the credit
was auto-consumed by the wrong free bet — that's the extra capability beyond a
plain account move. Productionising as `POST /v1/bets/{id}/reassign-account` +
BetLog door + `bet_reassigned` enum migration is a follow-on; the reviewed CORE
operation is what fixes this bet and is the tested basis for the door.

## 7b. MECHANISM REVISED after adversarial review B (design §4–§5 as written was UNSAFE)

End-state CONFIRMED correct and reproduced cleanly on a copy (Tim cash +$50,
Leigh −$50, Tim FB-in-hand −1, Leigh unchanged, The Creator grouped, So
Rebellious +$300 untouched). But the MECHANISM had to change:

- **F1 — the "verify-in-transaction / rollback" safety net is an ILLUSION.**
  Every repo/adapter/workflow constructor commits the open transaction
  (`apply_migrations→conn.commit`, `append_row` commits again). So calling the
  writer (op-3) OR any verification derivation mid-transaction COMMITS the raw
  ops; a later rollback does nothing. **NEW mechanism:** (a) do ALL mutations +
  integrity checks with RAW SQL on ONE connection, constructing NO
  repo/adapter/workflow object until after COMMIT; (b) DRY-RUN the identical ops
  on a throwaway copy first and run the adapter-based derivations THERE; (c) only
  if the dry-run is clean, replay the identical raw-SQL in one
  `BEGIN IMMEDIATE…COMMIT` on live; (d) post-commit derivations are CONFIRMATION
  only — a failure means RESTORE THE BACKUP, not rollback. (Reviewer proved the
  raw-SQL-only path works and gives the exact intended deltas.)
- **NC4 — never hand-write payload JSON.** A float `amount_drawn` (natural from
  `json.dumps`) fails `FreeBetDeployedPayload` validation, and the adapter
  re-parses every event on read ⇒ the event becomes UNREADABLE on every future
  scan (inventory/journey/balance throw), invisible to the cash-only self-check.
  **Build `FreeBetDeployedPayload`/`PromoEventBase` objects, serialize via
  `_event_to_row`, then raw-INSERT/UPDATE the resulting strings** — exact
  "50.00" encoding, dashed UUIDs, min_length/sum invariants for free, WITHOUT
  constructing the committing adapter. Applies to op-1's payload rewrite too.
- **NC2 — `bets` has NO foreign keys**, so `foreign_key_check` can't see op-4.
  Verification MUST explicitly assert the qualifier's new `account_at_book_id`
  exists in `accounts_at_book` AND equals the exact Leigh triplet `58f3d93a…`.
- **NC3 — `bet_edited` audit is EMPTY** (`BetSnapshot` has no account field ⇒
  before==after, no-op diff). Either add a `bet_reassigned` mutation type (needs
  a CHECK-constraint table-REBUILD migration — a PREREQUISITE, not follow-on),
  or record from/to triplet + correction ref in the event `notes`+`correlation_id`.
- **NC5 — op ORDER is load-bearing** (unique-superseder index): op-1 (re-point So
  Rebellious off `19a3e9d5`) BEFORE op-3 (new deploy superseding `19a3e9d5`);
  op-2 (move credit to Leigh) BEFORE op-3. Also assert S243
  (deploy.account == deploying_bet.account) for BOTH deploys in verification.
- **NC5b — DROP the "FB face net-zero" check** — global FB-in-hand face goes
  $50→$0 BY DESIGN (phantom eliminated; cash is conserved, FB face is not).
  Instead assert: `5e32f0d7` chain terminal now DEPLOYED (Tim in-hand −1);
  `19a3e9d5` terminal DEPLOYED on Leigh; every credit in-hand-or-consumed exactly
  once; `list_uncredited_qualifiers` shows neither `bcd524f8` nor `2527b525`
  newly uncredited; per-account cash deltas; the NC2 triplet assertion.

CONFIRMED-SAFE by review B: settled-won re-source doesn't change So Rebellious's
P&L/conversion/$300; correlation/cycle stay as-is (matches convention); cross-
account cycle not money-load-bearing; no event-hash/merkle/replay/trigger
immutability dependency; Leigh triplet resolves to a real accounts_at_book row.

## 8. Open questions for the review (attack these)
1. Is raw in-place UPDATE of `promo_events` genuinely safe here, or does
   ANYTHING (a derivation, a future operation, the burst-review, journey-state)
   break because an event's account/supersedes changed under the append-only
   assumption? Is `bet_reassigned` needed vs `bet_edited`?
2. Does op-1 (re-sourcing a SETTLED-WON deploy to a different credit) create any
   inconsistency — e.g. `realised_conversion_rate`, the FB bet's link, journey
   state — given So Rebellious is already settled_won?
3. Op-3 built by mirroring the payload vs calling `record_free_bet_deployment`:
   the writer would re-validate S243 + supersede-once (good), but runs on its own
   connection/txn — can it join our single transaction, or must we mirror? Which
   is safer?
4. Correlation trap: credit correlation = qualifier-bet-uuid, deploy correlation
   = cycle-uuid. After the move, does leaving cycle_id/correlation as-is make the
   journey-state or any "find the chain" view show something wrong?
5. Is the verification in §5 actually SUFFICIENT to prove clean, given the
   self-check can't see free-bet corruption? What's missing?
6. Any ordering hazard in the 5 ops (e.g. FK checks firing mid-transaction, the
   unique-superseder index during the re-source)?
