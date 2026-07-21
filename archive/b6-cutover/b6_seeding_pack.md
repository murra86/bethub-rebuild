# B6 seeding pack — gate #3 worksheet (accounts / books / account-at-book)

**Drafted:** 2026-07-06 23:02 ACST, Session 232 (headless runner — PREP ONLY per the S231
close; the seeding itself is interactive operator work and has NOT been executed).
**Status:** READY FOR THE SEEDING SESSION — every factual cell below is deliberately BLANK.
Nothing here is pre-filled; the operator dictates the rotation in the interactive session.
**Gate served:** #3 — tick criterion (judge, verbatim): *"operator confirms a real bet can
be recorded/tagged against every account in current rotation."* Maps to day-one checklist
line DAY-02 in `b6_scope.md` §1.2.
**Governing DRs:** DR-022 (account / book / account-at-book vocabulary — this pack's spine),
DR-019 (money derives on read — why opening balances are captured as events, not stored
numbers), DR-021 (Adelaide timestamps), DR-027/028 (two-database split — everything here
lands in v3's operational store only).
**Grounding:** entry mechanics below were verified against bethub-v3 HEAD `4f98ad5` on
2026-07-06 (Accounts screen + `/api/v1/accounts` router; `cash_flow_events` store layer;
balance derivation read path). No guessed capability.

---

## 0. How to run the seeding session (~20 minutes)

1. Open a normal governance session with Claude and say "run the seeding session —
   `b6_seeding_pack.md`".
2. Work through §1 → §2 → §3 in order, dictating rows. Claude fills the worksheet as you
   go and enters the rows via the mechanics in §4.
3. Finish with the §5 verification pass — that pass, recorded, is what ticks gate #3.
4. Do all of this BEFORE the proving window opens (§6).

Vocabulary reminder (DR-022): an **account** is a betting identity (a person);
a **book** is a bookmaker; an **account-at-book** is one account registered at one book —
the operational unit where balance, promo eligibility and limiting status live.

---

## 1. Worksheet — accounts (identities)

One row per real-world betting identity in the current rotation. Typically a short list.

| # | Account name (as you call them) | Is this you? (yes/no) | Notes |
|---|---|---|---|
| A1 | Tim | yes | |
| A2 | Kate | | |
| A3 | Sarie | | |
| A4 | Leigh | | |

Column guidance:
- **Account name** — the everyday name you use for the identity. It only has to be
  recognisable to you; it is not sent to any bookmaker.
- **Is this you?** — the store records self vs household-member identities (`is_self`).
- Add rows as needed; blank rows are simply skipped.

---

## 2. Worksheet — books (bookmakers)

One row per bookmaker that any account in §1 is actively registered at. Only books in the
CURRENT rotation — archived/closed books can be added later if analytics ever needs them.

| # | Book name | Ownership cluster (optional) | Platform (optional) | Notes |
|---|---|---|---|---|
| B1 | Betfair | | | |
| B2 | TAB | | | |
| B3 | TABTouch | | | |
| B4 | PickleBet | | | |
| B5 | PointsBet | | | |
| B6 | StarSports | | | |
| B7 | Betr | | | |
| B8 | | | | |
| B9 | | | | |
| B10 | | | | |
| B11 | | | | |
| B12 | | | | |
| B13 | | | | |
| B14 | | | | |
| B15 | | | | |

Column guidance:
- **Ownership cluster / platform** — optional dropdowns on the registration screen (locked
  S152 list: clusters Entain / Flutter / Tabcorp / bet365 / betr–BlueBet / Crown–Blackstone /
  PlayUp / PointsBet / Independent; platforms BetMakers / GenerationWeb / Punterstech /
  BetCloud / ApolloTech / BetEngine / Custom). Leave blank if unsure — they can be filled
  any time and gate nothing.

---

## 3. Worksheet — account-at-book rows (the operational unit) + opening balances

One row per active account-at-book pairing — this is the ~10–15-row heart of the seeding.
Every row here must end up registered in the store AND verified in §5.

| # | Account (from §1) | Book (from §2) | Opening cash balance ($) | Unused free bets on hand ($ + which promo, if any) | Limited/restricted? | Notes |
|---|---|---|---|---|---|---|
| R1 | Tim | Betfair | 3,157.93 | none | no | |
| R2 | Tim | TAB | 1,317.20 | none | no | |

*Operator confirmed at seeding: NO unused free bets at any book, any account (2026-07-07).*
| R3 | Kate | TABTouch | 246.85 | none | yes — limited | |
| R4 | Kate | PickleBet | 557.02 | none | no | |
| R5 | Kate | PointsBet | 1,102.50 | none | no | |
| R6 | Kate | StarSports | 670.00 | none | yes — limited | |
| R7 | Leigh | TAB | 1,220.20 | none | no | reassigned from Kate at seeding — Kate has no TAB account |
| R8 | Sarie | TAB | 1,267.00 | none | no | |
| R9 | Sarie | TABTouch | 1,287.50 | none | yes — limited | |
| R10 | Sarie | PointsBet | 889.80 | none | no | |
| R11 | Sarie | StarSports | 380.00 | none | yes — limited | |
| R12 | Sarie | Betr | 695.73 | none | yes — limited | |
| R13 | Sarie | CrownBet | 0.00 | none | no | added live at seeding — real account, zero balance today |

*Books note (2026-07-07): SportsBet registered with no pairings yet — kept deliberately,
accounts expected there in future.*
| R14 | | | | | | |
| R15 | | | | | | |

Column guidance:
- **Opening cash balance** — the withdrawable cash sitting at that book at seeding time.
  Read it off the book's own app/site during the session; approximate-to-the-cent is the
  goal, but an honest close figure beats a stale exact one. This is the day-0 anchor for
  cash tracking: from this point on the tool derives every balance on read (DR-019) from
  events, so day-0 correctness is what makes every later daily money check meaningful.
- **Unused free bets on hand** — any free-bet credits currently sitting at the book. Listed
  so nothing is silently lost at day 0. NOTE: how these enter the store is a decide-in-
  session item (§4.3) — do not assume a mechanism; worst case they are recorded on this
  worksheet and carried manually until first use.
- **Limited/restricted?** — yes/no/partly, your read of the account's health at that book.
  Captured as row notes for now; useful context for the proving window.

---

## 4. Entry mechanics — how the rows get into the v3 store

### 4.1 Accounts, books, registrations — the UI path (RECOMMENDED)

Use the **Accounts setup screen** in the running v3 app (registration confirmed working
operator-side at S159; surface re-verified against HEAD `4f98ad5` at S232). Flow per row:
create the account (§1) → register the book (§2) → register the account-at-book pairing
(§3). The screen guards the obvious mistakes itself (duplicate registration warns; a
missing account/book errors in plain English).

Why the UI path: the seeding session then doubles as a **workflow shakedown** — 10–15 real
registrations through the real screen is exactly the kind of live-usability pass that
caught the Log-Past-Bet gap at S189. If the screen fights you at any point, that friction
is itself a finding — note it, keep going.

**Fallback** (only if the UI path breaks mid-session): a supervised seed script writing
through the same store layer the screen uses, dictated rows read back line-by-line before
committing. Named for completeness; not the plan.

### 4.2 Opening cash balances — supervised scripted write (no UI path exists)

Ground truth at `4f98ad5`: the store fully supports opening balances (an
`account_at_book_balance_adjustment` event per row in the cash event log, which the
balance display then derives from on read per DR-019), but **no screen writes cash events
today**. So in the seeding session, Claude writes one balance-adjustment event per §3 row
through the store's cash-flow write surface (`source='operator'`, a note marking it
"day-0 opening balance seed"), with two safeguards:

1. **Read-back before write** — the full row list (account-at-book + amount) is read back
   to you and confirmed before anything is committed.
2. **Verify on the real read path after write** — for each row, the race-screen balance
   display (the same cash-balance read used in live play) must show the seeded figure.
   The write isn't trusted; the derived read is.

A pre-write backup of the v3 store is automatic on launch (S231 build) — take/confirm one
before the balance writes as a belt-and-braces restore point.

### 4.3 Day-0 free-bet inventory — decide in session (do not assume)

Whether existing free-bet credits can be seeded cleanly (the free-bet inventory normally
derives from promo credit events tied to a qualifier bet) is NOT confirmed. In-session:
if a clean seed mechanism exists, use it with the same read-back + derived-read
verification; if not, the §3 worksheet column is the record, and each free bet is entered
at the moment it is first used. Losing track of them is the only failure mode; a worksheet
line prevents that at zero risk.

---

## 5. Gate-3 verification procedure — what actually ticks the gate

The tick criterion is about **recording bets**, not just listing accounts. After all rows
are in:

1. **Per-row dry recorded-bet check.** For EVERY §3 row, open the bet-logging panel and
   take the entry far enough to prove the row is selectable and a bet could be recorded/
   tagged against it — the account-at-book appears in the picker, its cash balance shows
   the §3 figure, the form accepts it. Recording an actual test bet into the store is NOT
   required (and keeping the store clean of fake bets is preferred — DAY-09 wants a clean
   working view); selectable-with-correct-balance is the proof. ~30 seconds a row.
2. **One real-workflow pass (DAY-02's "reviewed complete against one real day's
   workflow").** On the next real racing day (this can be proving-window day 1), confirm
   the day's actual bets each found their account-at-book in the picker with nothing
   missing and no workaround needed.
3. **Tick evidence to record** (a short dated note appended to this file or the session
   record): the row count seeded, "all rows selectable, balances correct" (or the
   exceptions), and the operator's one-line confirmation echoing the criterion — *"a real
   bet can be recorded/tagged against every account in current rotation."* Gate #3 is then
   marked MET in `b6_scope.md`'s gate table.

Any row that fails (missing from the picker, wrong balance, screen error) blocks the tick
until fixed — that is exactly the day-one blocker this gate exists to catch early.

---

## 6. Sequencing reminder

Seeding lands **BEFORE the proving window opens**. Gate #9's window days only count from a
seeded store (`b6_scope.md` §1.2 DAY-02 is a day-one precondition), and each window day
ends with the daily money check (`uv run python -m ops.settlement_review`) signing the day
off — which is only meaningful once day-0 balances are in. Seed first, then play.

---

## 6a. Seeding record (2026-07-07, S232 — appended live)

- Registrations: 4 accounts, 13 active pairings entered by the operator through the
  Accounts screen (12 worksheet rows + Sarie@CrownBet added live at $0). Reconciled
  against the store read-only before any write.
- Store backed up pre-write: `~/.bethub/backups/bethub-20260707-preseed-gate3.db`.
- 13 `account_at_book_balance_adjustment` / `day_0_opening` events written via the
  store adapter (source=operator, one shared correlation id), plus 1 correction event
  on Tim@BetFair netting out the 9 pre-seed live-proof bets (all terminal, net +2.7588)
  already included in the operator's balance read.
- Verification: all 13 derived balances match the worksheet exactly on the real read
  path (`compute_account_at_book_balance`, same derivation the race screen serves).
  Total cash across rotation: $12,791.73.
- §5.1 per-row check PASSED (2026-07-07 19:53 ACST, relaunched live app): all 13
  account-at-books present in the picker data with exact balances and zero free bets,
  verified via the live `/api/v1/racing/log-context` read per row; operator eyeballed
  the picker + balances in the app and confirmed correct.

## 5a. Gate-3 tick evidence (2026-07-07, S232)

- Rows seeded: 13 (4 accounts, 9 books). All 13 selectable with correct balances —
  no exceptions.
- Operator confirmation (criterion): balances confirmed correct in-app; no bets placed
  yet by design — the tick criterion is *recordable*, not *recorded*. First real racing
  day (§5.2, proving-window day 1 counts) re-confirms in live use.
- **Gate #3 marked MET** in `b6_scope.md` gate table (rider: §5.2 on window day 1).

## 7. Shakedown findings (live, S232 seeding session)

- **F1 — remove the "My own account" tickbox** from the account-creation screen (operator:
  no use for it). **CLOSED same session**: checkbox + mine/household tag removed from the
  UI, create call sends `is_self=false`, API/store untouched. Suites 1390 / 132 green,
  dist rebuilt, committed + pushed (`4f98ad5` → `18177e0`).
- **F2 — operator expected pairings to be seeded for him**: the §0/§4.1 flow didn't make
  it clear the account-at-book registration step was his. Resolved live (he registered all
  13 after the reconciliation caught only 1 present). No build action; noted as a pack-
  clarity lesson for any future seeding-shaped session.
- Also tidied at operator direction: dead duplicate BetFair book row deleted from the
  store (zero references, verified before delete). SportsBet kept (future accounts).

---

*Prepared by the S232 headless runner. Every factual field left blank by design — the
operator's account knowledge is the only source for §§1–3.*
