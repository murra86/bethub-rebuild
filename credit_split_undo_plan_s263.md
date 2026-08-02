# Build plan — "Split this credit" + undo for account-anchored credits (worklist 0v)

S263, 2 Aug 2026. Plan only — no code changed. A reviewer follows.

## Operator summary

When a book issues a bonus as five $30 free bets and we record one $150 lump,
the first bet placed against it would silently destroy the other $120 —
using any part of a recorded credit consumes the whole thing. On 31 Jul we
fixed the live Sarie/Ladbrokes case by hand; this build turns that hand fix
into a two-click control: a **Split** button that turns one recorded lump
into the N pieces the book really issued, in one audited step, refused
outright if any of it has already been used. The same screen also gets the
**Undo** button for credits that aren't tied to a bet (deposit bonuses,
goodwill) — the server already accepts those undos; the tool just never
offered the button. Nothing needs repairing today (zero such credits are
live right now) — this is for the next lump, before it can be mis-spent.
Confidence: high — every server piece this composes already exists and is
live-proven; the new work is one composition writer plus screens.

## 1. Verified current state (all cites checked 2 Aug)

**The undo engine is complete server-side; only the UI can't reach it.**

- `POST /v1/promos/credit-revocations` (`bethub-v3/ui/api/routers/promos.py:1122-1175`)
  now covers BOTH kinds (1b, commit `d3583cf` 2 Aug): dispatches on the stored
  event type — FB → `record_free_bet_revoke`
  (`workflows/promos/v1/fb_revoke.py:46`), cash → `record_promo_cash_reject`
  (`fb_revoke.py:132`, the rejected-cash supersession, precedent `a1a86071`).
- Neither writer requires a bet. Refusals: not a credit of that kind; already
  superseded (spent / revoked / expired); cash not live-finalised; empty
  reason; concurrent supersession caught by the DB backstop
  (`uq_promo_events_supersedes`, `store/schema/promos.py:187-189`).
  **Account-anchored credits are accepted today** — verified against both
  writers; nothing in the chain reads a bet.
- Every read side already treats a rejection/revoke terminal as
  not-a-live-credit (2 Aug delta, incorporated): the BetLog paid-marker map
  filters `status='rejected'` and rejected/revoked supersessions
  (`ui/api/routers/bets.py:899, 913-921`), the strip's bonus-cash line
  filters finalised (`bets.py:1162-1163`), and the reclass fence skips
  rejection terminals (1b HIGH-1, `bets.py:2394-2401`). Tested:
  `tests/ui/api/test_bets_reclass.py:607, :668`,
  `tests/workflows/promos/v1/test_fb_revoke.py:233, :280`.
  So an undone/split credit cannot wedge reclass or ghost the feed.

**The UI-reach gap.** BetLog's "Undo credit…" keys off
`bet.insurance_credit_event_id` (`ui/web/src/routes/BetLog.tsx:720-729`),
a bet-feed field built from `_triggered_credits` (`bets.py:843`) keyed by
`triggering_bet_id`. Account-anchored credits (`credit_source='freebie'`,
payload forbids trigger fields — `workflows/promos/v1/fb_credit.py:422`)
never appear there. The Accounts page (`ui/web/src/routes/Balances.tsx`)
shows only aggregate `free_bet_balance`/`fb_count` per book row (line
320-330) plus the bank-a-credit card (lines 583, 1159) — no per-credit
rows, no undo, no split anywhere.

**No split exists.** The 31 Jul stopgap is the composition to productise,
verified in the DB: lump `54905e90` ($150 freebie) → revoke `d611fb2b`
("Book issued this sign-up bonus as 5 x $30…") → five $30 freebie credits
(`0ede3476`, `fa02e6a9`, `a449d6b0`, `26a550bf`, `aab9a423`), balance
verified `free_bet_balance=150.00 / free_bet_count=5`, cash untouched.
All five since deployed; **0 account-anchored credits are live today**
(8 ever) — no data migration, the build is purely for the next lump.

**Why the refusal matters (S260 finding):** a deploy supersedes the WHOLE
credit event (`fb_deployment.py` stamps `supersedes_event_id` = the credit;
consumption is all-or-nothing) — $30 deployed against a $150 lump destroys
$120 of inventory and breaks the certified ledger cross-foot.

## 2. Design — the split door (server)

New writer `workflows/promos/v1/fb_split.py::record_credit_split(conn, *,
credit_event_id, parts_count, reason)`, following the S254 §3d verb
discipline (`ops/correct_promo_selection.py` ◆2 / `ops/correct_credit_amount.py`
◆2): `PRAGMA foreign_keys=ON` before `BEGIN IMMEDIATE`, events built via the
domain models, raw-inserted with the promos `_event_to_row`, ONE commit —
no adapter/repository on the transaction connection (they commit internally,
which would break atomicity mid-composition).

**Composition (one transaction):**
1. Cancellation, kind-matched (the ◆1 sanctioned shapes): FB lump →
   `free_bet_revoked` terminal; cash lump → new `promo_cash_credited` with
   `status='rejected'` superseding it. Reuse the two existing writers'
   payload shapes but write raw (do not call `append_event`).
2. N re-issues copying the lump's identity: `credit_source` UNCHANGED (◆3 —
   the enum has no 'correction' member; `freebie` stays `freebie`),
   `face_value_expiry` copied verbatim (the book's window applies per piece),
   `reference` = the lump's event id, `notes` = "split k of N — {reason}",
   `correlation_id` = ONE fresh split-operation UUID shared by all N pieces
   (groups the operation; freebie correlations are replay keys, not joins,
   so a fresh one breaks nothing). `occurred_at` = the LUMP's `occurred_at`
   (the 2 Aug operator decision pattern — `ops/correct_credit_amount.py:360-369`:
   replacements carry the original economic date; `recorded_at` stays now).

**Refusals (plan-time, re-asserted under the lock):**
- lump not found / not a credit event type;
- not live: already superseded (spent → "restore the spend first", revoked,
  expired) or cash not `finalised`;
- **bet-triggered credit (payload carries `triggering_bet_id`) — refused in
  v1** with a named reason. Rationale: the store's standing invariant is ≤1
  live credit per qualifier (`find_existing_credit` natural key;
  `ops/correct_promo_selection.py:211-215` refuses ">1 live credits —
  ambiguous"; `_triggered_credits` maps one credit per bet). N live pieces
  on one qualifier breaks those reads. The worklist sketched a BetLog
  surface too; deferring it is deliberate — the only real N×$X case so far
  is sign-up/goodwill (account-anchored), and no book has issued a
  bet-triggered credit in pieces. If one ever does, that becomes its own
  worklist item because the invariant itself has to move.
- `parts_count` outside 2..10;
- lump amount does not divide into `parts_count` exact-cent equal pieces
  (e.g. $100 into 3) — unequal parts out of scope (books issue equal
  denominations; the live case was 5×$30);
- empty reason.

**Idempotency / concurrency:** the lump's single supersession slot IS the
idempotency. CAS re-check under `BEGIN IMMEDIATE` ("still not superseded"),
`uq_promo_events_supersedes` as the DB backstop — a replayed split, or a
deploy racing the split, leaves exactly one winner; the loser gets a clean
refusal (map `DuplicateSupersessionError` → 4xx, never a 500 — the S247
B5(a) pattern in `fb_revoke.py:113-121`).

**Endpoint:** `POST /v1/promos/credit-splits`
`{credit_event_id, parts_count, reason}` → 201
`{cancellation_event_id, part_event_ids: [...], part_amount}`;
workflow errors map to 422 with the writer's wording (same shape as the
revocations endpoint). `extra='forbid'`.

**Undo of a split comes free:** each piece is an ordinary live credit — the
existing revocations door covers it; no new undo machinery. Un-splitting
(merging back) = revoke the unspent pieces + bank one lump via the existing
account-credit door; not a dedicated door.

## 3. Design — UI reach (the undo gap + the split's home)

1. **New read** `GET /v1/promos/account-credits?account_at_book_id=…` →
   live account-anchored credits, BOTH kinds: `{event_id, kind (free_bet|
   cash), amount, credited_at (occurred_at), face_value_expiry, notes}`.
   One indexed query over `promo_events` (freebie source, finalised, not
   superseded). Deliberately NOT bolted onto the racing log-context read —
   that is the race screen's hot path and its `free_bets` list is FB-only.
2. **Accounts tab (Balances.tsx):** each book row gains a small "credits"
   expander (shown when the row has any live account-anchored credit; the
   row already knows `fb_count`). Each credit line:
   - **Undo credit…** — S237 inline confirm naming amount/book/holder +
     mandatory reason, wired to the EXISTING `revokeCredit`
     (`ui/web/src/api/promos.ts:225`). UI-only; the server refuses
     everything it should.
   - **Split…** — count field (2..10), live preview "N × $X", inline
     confirm + reason, calls the new endpoint. Server refusal text surfaced
     verbatim.
   Invalidate the log-context query family on success (the Balances rows
   and race-panel inventory re-derive).
3. **BetLog:** no change. Bet-attached credits already have undo there;
   split on bet-attached credits is refused v1 (see §2).
4. **Recommended tiny complement (reviewer's call, ~0.5h):** the bank-credit
   card (`Balances.tsx:1159`) gains a "book issued as N pieces" count field —
   the UI loops N `account-credits` posts with N pre-minted idempotency keys
   (exactly the sanctioned stopgap composition, replay-safe per piece). This
   prevents the lump mis-record at the source; the split door remains the
   cure for lumps already recorded.

## 4. Red-before tests

Server (new `tests/workflows/promos/v1/test_fb_split.py` +
`tests/ui/api/test_promos_split.py`):
- split of a live $150 FB freebie lump → revoke + 5×$30 in ONE txn; then
  `compute_account_at_book_balance`: `free_bet_balance` unchanged,
  `fb_count` 1→N, cash untouched (the exact 31 Jul verification);
- cash lump → rejected-cash cancellation + N cash credits; strip/feed
  reads unchanged in total;
- pieces carry: lump's `occurred_at`, copied `credit_source` + expiry,
  `reference` = lump id, shared fresh correlation;
- refusals red-before: deployed lump ("restore first"), revoked/expired
  lump, bet-triggered credit, non-exact division ($100/3), parts_count 1
  and 11, empty reason, unknown event id;
- concurrency: superseder landing between plan and write → CAS refusal;
  double-fire race → DB backstop, clean 4xx (mirror
  `test_b5_revoke_race_hits_db_backstop_and_refuses_cleanly`);
- crash injection mid-composition → full rollback, lump still live
  (mirror `test_failure_rolls_back_everything` in the selection-verb suite);
- each piece is individually revocable via the existing endpoint after the
  split (the "undo for free" claim, asserted).

UI (vitest): expander lists account-anchored credits only; Undo appears on
an account-anchored row and posts to credit-revocations (today: nothing
renders — red); Split preview arithmetic; refusal detail rendered verbatim.

## 5. Effort

- Server writer + endpoint + listing read + tests: ~half a sitting.
- Accounts-tab expander + two inline actions + vitest: ~half a sitting.
- Total: **one focused sitting**, same size class as the 0j rider + 0q
  work. Frontend gate `npm run build`; no migration; no deploy-window risk
  (additive endpoints, one additive UI surface).

## 6. Out of scope (named so they don't creep back in)

- An expiry door (the S262 $10 Sarie FB expiry was written by sanctioned
  composition; if wanted it is its own small item — not part of 0v).
- Splitting bet-triggered credits / unequal parts (see §2 rationale).
- Any change to deploy semantics (all-or-nothing consumption stands).

## 7. Operator questions

None. The two judgement calls (v1 restricted to account-anchored credits;
equal parts only, 2..10) are documented above with rationale and are
reversible later without unwinding anything.

## Adversarial planning review (S263) — SAFE WITH FIXES; amendments NORMATIVE

Core composition verified sound (sanctioned supersessions; the unique
index leaves piece roots unconstrained; the W12.1 walk counts each
piece once; account credits bypass the bet-triggered idempotency guard
in both directions; account-anchored undo already works server-side;
"partially deployed" cannot exist). REFUTED premise that STRENGTHENS
the plan: the 31 Jul hand-split pieces already share one occurred_at
second, and no automatic FIFO consumer exists (deploys are
operator-selected ids) — identical-dated pieces are the live-proven
shape.
1. MEDIUM — gate the Accounts expander on the NEW LISTING READ's
   result, never `fb_count` (it counts bet-triggered FBs and no cash —
   a cash-only goodwill row would get no expander: the exact case 0v
   exists for).
2. LOW-MED — add a `face_value_expiry <= now` refusal (plan-time AND
   under-lock): an expired-but-unactioned lump is hidden only by the
   read-time filter, so the CAS passes and the split mints N expired
   pieces "successfully". Decide whether the listing shows
   face-expired credits.
3. LOW — the raw-insert backstop raises sqlite3.IntegrityError, not
   DuplicateSupersessionError — catch it; word the double-fire test
   honestly (the CAS is what actually fires).
4. LOW-MED — §3.4's N client-side POSTs: pin idempotency keys to the
   opened card + document retry, or move server-side one-txn.
5. COSMETIC — name which date the expander shows (recorded_at = split
   time vs occurred_at = lump date); refresh the bets.py cites.
PROCESS: the UI (expander + split control) goes through the MOCK-FIRST
loop with the operator before build (standing UX feedback).
