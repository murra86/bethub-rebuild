# Whole-app clean pass + settled-bet edits — build report (Session 237)

**Built:** 2026-07-09 evening ACST, operator-attended (mock-first loop:
`app_pages_clean_mock.html` approved page-by-page, then built same session).
**Repo:** bethub-v3 `431890d` → **`6d35480`** (pushed, tree clean). Earlier same
session: `402e5bd` (burst-flow redesign, runner-built) and `431890d` (race-page
clean pass).
**Suites:** backend **1443** (was 1441; settled-edit paths re-pinned), frontend
**188** (was 183 at S237 open); `tsc -b` + `vite build` green; dist rebuilt with
the app confirmed down.
**Fences:** `place_lay`, settlement resolvers, reconciliation, credit-engine
maths untouched. The one money-adjacent change (below) is store/router edit-fence
scope, operator-directed.

## 1 · Settled soft-book bets are now editable (operator-directed)

The operator: "I still can't change the details of settled bets (account, book,
stake, odds)." Grounded first: P&L and every book balance derive on read
(DR-019 — nothing stored goes stale), so a settled correction re-derives
consistently on both sides of the Money-page identity.

- **Store fence** (`store/repositories/bets.py`): stake/price/account edits now
  allowed on `settled_won` / `settled_lost` / `voided` as well as pending.
  Still blocked: `provisional` (the settlement worker's in-review lane — an
  edit would race the worker) and any unrecognised state.
- **Router guards** (`ui/api/routers/bets.py`): a **settled Betfair bet is
  refused** (422, "the exchange's own record") — its figures came from Betfair
  reconciliation. Promo-attached **account moves** stay refused (the credit is
  anchored to the account), with state-aware wording; stake/odds edits on
  promo bets are allowed.
- **BetLog UI**: edit panel now live on settled soft-book rows; an **amber
  caution** shows when a bonus credit rides the bet — the credit does NOT
  recompute, the operator checks it after. BET_EDITED audit fires as before.

## 2 · Whole-app re-skin (approved mock, per page)

One warm token sheet (index.css) everywhere; one colour per meaning; navy
BACK / rose LAY side tags; inline amber confirm strips replace every
`window.confirm` (BetLog settle/delete/Placed?, Money reverse, Accounts
archive/close — the last had no confirm at all).

- **Nav**: active page now highlighted (NavLink).
- **BetLog**: filter dropdowns → chip rows (person / book / pending-settled-all /
  free-cash); the UUID account-at-book dropdown deleted; status-coloured states.
- **Accounts**: dark; cluster/platform/person/book-to-register as chips;
  already-registered books ticked-and-faded; inline confirms.
- **Log Past Bet**: dark; person/book/side/outcome as chips; race cascade stays
  dropdowns (long lists); saved panel in the standard confirmation voice.
- **Manual queue + bet card**: dark; Won/Lost green/red outlines, Void plain
  grey (purple retired); confirm panel amber.
- **Burst review**: from its one-off near-black sheet onto tokens; settle
  buttons coloured.
- **Health**: dark card. **Money**: unchanged except the inline reverse confirm.
- Deliberately untouched: the HealthBanner fault alarm stays screaming red.

## Classification & live-look

Implemented-not-live (S189 taxonomy) until the operator uses it. App was down
at dist rebuild; next launch serves everything. Checklist:
1. BetLog: open a settled soft-book bet → stake/odds/account editable; save;
   Money page still shows the green self-check tick after the edit.
2. A settled **Betfair** bet: fields locked with the exchange-record wording.
3. Settle/delete/reverse/archive: amber inline strips, no browser pop-ups.
4. Nav shows where you are; every page dark and matching.

## Residuals / notes

- Frontend lint's 12 longstanding warnings unchanged (lint is not the gate).
- The promo-credit caution is advisory only — no auto-recompute of banked
  credits by design (credit maths fenced). If settled edits on promo bets
  become frequent, a credit-recheck door is the follow-up to scope.
- Test updates: confirm-flow tests now drive the inline strips; Accounts/
  LogPastBet tests drive chips; two new BetLog tests pin settled-edit
  enablement + the Betfair lock; store/router tests re-pinned to the new fence.
