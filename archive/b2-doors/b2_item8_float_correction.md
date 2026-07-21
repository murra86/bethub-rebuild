# B2 Item 8 — day-zero float correction (S246, 20 Jul 2026)

**What changed for your money view:** the combined float no longer reads
−$3,126.42. It now reads **+$1,259.80** — which is exactly Sarie's real
parked pool — and every other holder's float reads 0.00. Nothing about
your P&L, book balances, or bet history changed; the operation's
self-check still reconciles to the cent (difference 0.00).

## The root cause (grounded S246)

The 17-Jul data-reset re-seed wrote Tim's opening book balances as two
**deposit** events (BetFair $2,674.02 + TAB $1,712.20). Deposits drain a
holder's float by design — but the money that funded those balances was
never booked INTO the float, because it pre-dated the ledger. So Tim's
float derived to −$4,386.22 for money that was never actually missing.
Kate/Leigh/Sarie were unaffected (their ledgers were already coherent;
Sarie's +$1,259.80 is the S244-trued pool).

## The operator ruling

"The balances we establish on launch are essentially the money I already
had in circulation as of go-live." (S246, in-session.) That makes the
day-0 deposits the SECOND hop of a two-hop movement whose first hop
(circulation money in) was never written — the same shape as the S244
$400 BetRight correction.

## What was written

Two signed `account_holder_funding` events for Tim, occurred-at matching
the day-0 deposits (17 Jul 16:33 ACST), operator source, notes carrying
the ruling and the paired deposit event ids:

- `edf2b115-7213-4972-828c-8f56cd8cc7c0` — $2,674.02 (pairs deposit
  `3a861575…`, Tim@BetFair)
- `6f7c2eb1-c6f4-41c2-bab2-c6f0d837a719` — $1,712.20 (pairs deposit
  `35be6998…`, Tim@TAB)

Written through the same domain-event + adapter path the movements door
uses (app was down; identical validation and append-only spine).
Reversible via the existing reverse door if ever needed.

## Verification (live read path)

- Per-holder floats after: Kate 0.00 / Leigh 0.00 / Sarie 1,259.80 /
  Tim 0.00; combined +1,259.80.
- `pnl_dashboard` self-check: **ok, difference 0.00** (cash view = P&L
  = $895.27; funding is netted out of the cash view by construction, so
  the correction cannot move P&L).
- Backup taken before the write:
  `data/bethub.db.bak-s246-pre-floatfix-20260720-173922`.

## Consequence for B2

The negative-float tripwire (B2 Item 4) can now go live without crying
wolf from day one. Standing rule unchanged: any Tim deposit at a book =
fresh bank money, always (the new door defaulting encodes it).
