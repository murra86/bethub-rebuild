# Bank transfer playbook (S248 bankroll model)

One page: what to tap in the tool for every real-world money move.
Written 21 Jul 2026, the day the bankroll account went live. Until
the one-tap transfer door lands (worklist 0d), two of the scenarios
below take two taps — the door labels still carry old wording; follow
the recipe, ignore the labels, the numbers land right.

## The two golden rules

1. **Every real transfer gets booked the same day it happens.**
2. **The Bankroll row must equal the bankroll bank app, every day.**
   If they differ, something is genuinely wrong — say so in session.

## The map

- **Bankroll account (UBank)** = the operation's homebase. Shown as
  the Bankroll row/tile. Source and destination of all funds.
- **Sarie / Kate / Leigh cash floats** = operation money they
  physically hold as intermediaries.
- **Personal money** = outside the operation entirely. Crosses the
  boundary only via the Bankroll row's doors.

## Scenarios

**1. Put personal money into the operation** (e.g. the $3,000 seed)
Real world: personal account → bankroll account.
Tool: Bankroll row ＋/− → "Top-up float" for the exact landed amount.

**2. Take profit home**
Real world: bankroll account → personal account.
Tool: Bankroll row ＋/− → "Return float".

**3. Fund one of YOUR books** (e.g. $200 into Tim @ TAB)
Real world: bankroll account → TAB.
Tool: that book's ＋/− → Deposit, source **"Tim's float"** (the
default). Bankroll drops, book rises. One tap.

**4. Withdraw from one of YOUR books**
Real world: book → **bankroll account** (always withdraw to the
bankroll account, never straight to personal).
Tool: that book's ＋/− → Withdraw. Lands in the Bankroll row
automatically. One tap. (If the book forces a different destination
account, book a "Return float" as well so the tool matches reality.)

**5. Fund an intermediary's book when their float is EMPTY**
(the $300 → Sarie → CrownBet case)
Real world: bankroll account → Sarie's account → CrownBet.
Tool, two taps:
  a. Bankroll row → "Return float" $300  (bankroll drops)
  b. Sarie @ CrownBet → Deposit $300, source **"fresh bank money"**
     (writes her top-up + deposit together; her float nets zero)
Never a bare one-tap deposit — it either drives her float negative
or leaves the bankroll overstated.

**6. Fund an intermediary's book from money they ALREADY hold**
Real world: Sarie moves her held cash into a book.
Tool: her book's ＋/− → Deposit, source "Sarie's float". One tap.

**7. Intermediary withdraws from their book**
Real world: book → their account; they now hold operation cash.
Tool: their book's ＋/− → Withdraw. Lands in their float. Correct —
it stays operation money until moved home.

**8. Move an intermediary's held cash home to the bankroll**
Real world: Sarie's account → bankroll account.
Tool, two taps (mirror of #5):
  a. Sarie's float row → "Return float" $X
  b. Bankroll row → "Top-up float" $X

**9. Pay a helper their cut**
Real world: their float (or the bankroll) → theirs to keep.
Tool: that float row → "Profit share". Money leaves the operation;
P&L is not touched (it was already earned).

**10. Trying a new book** (the UpYaGo lesson done right)
Fund it via #3 (your book) or #5 (theirs). Withdraw the lot at the
end via #4 or #7. The day's profit shows up in P&L from the bets
themselves — the transfers never create or destroy profit.

## If you mis-book something

Money movements ledger (bottom of the Balances page) → Reverse on
the wrong row, then book it correctly. Bank-pair rows reverse both
halves together — the tool will ask.
