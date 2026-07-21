# B2 — Money-safety doors: design note (S246, 20 Jul 2026)

**Status: DRAFT — awaiting operator walkthrough. Nothing here is built.**
Every item below touches money paths or money-adjacent surfaces, so per
standing practice the build is commissioned only after this walkthrough.
Grounding was read-only (three parallel code sweeps, S246); all file
references verified against bethub-v3 HEAD `f28a7ef`.

**How to read this:** each item leads with what it protects on a betting
day, then current state, then the proposed door, then **DECIDE** lines —
the choices only you can make. Decisions are numbered D1–D10 and
collected at the end for the walkthrough.

---

## Item 1 — Void/delete-bet door (the BetRight phantom, feedback item 10)

**What it protects:** a bogus row — like the BetRight "settled_won @ $0"
phantom — currently sits in your P&L forever. No door can fix its
classification; your day's numbers carry it.

**Today:** hard delete exists but only for unsettled, un-cycled,
unreferenced bets (`store/repositories/bets.py:1321`). The settle door
only fires from pending; the manual queue only from provisional. **No
door in the app can change a terminal state (won/lost/void) to anything
else.** Money-field edits on settled bets are allowed (S237), so you can
fix a wrong amount — but not a wrong verdict.

**Proposed:** an audit-trailed **re-class door** on the BetLog row
(terminal state → another terminal state, mandatory reason). The row is
never deleted — the trail shows old state, new state, reason, timestamp.
Two build notes surfaced by grounding:
- The bet-mutation audit table's type list is closed (3 types) — adding
  a `BET_RECLASSED` audit type is a small schema migration. This was
  already flagged as a parked follow-up when the settle door was built.
- Re-classing can strand promo money: a won→void flip on a bet whose FB
  or insurance credit already banked needs the existing revoke door run
  alongside. The re-class door should **show linked promo events and
  block until you've dealt with them** (refuse-with-list, like the
  credit-in gate refuses with a reason).

**DECIDE D1:** re-class allowed between ANY terminal states (won↔lost↔
void), or only →void? (Recommend: any, with reason — a wrong "lost"
that was actually won is the same class of error.)
**DECIDE D2:** hard delete stays fenced exactly as-is (recommend yes —
the phantom's cure is re-class-to-void, keeping the audit trail, not
deletion).

## Item 2 — Auto-restore-on-void (feedback item 4's class)

**What it protects:** when a book voids your FB bet (scratched runner),
the book hands the free bet back — but the tool's FB pool doesn't get it
back until you remember the manual restore door. Forgotten = you under-
count your own ammunition.

**Today:** the settlement worker flips the bet to VOIDED (two reasons:
market voided / runner removed) but has **zero promo coupling** — the
restore door (`fb_restore.py`) is manual-only. The corrective-credit
primitive already exists and is idempotent (supersession guard), so the
auto version is a thin call, not new money arithmetic.

**Proposed:** when settlement writes VOIDED on a bet that consumed FB
credits, the worker writes the corrective credit automatically (system-
sourced, correlated to the void, idempotent). Failure never blocks the
void — it warns, mirroring the existing FB-deploy-write-failed pattern,
and lands a line in the daily money check.

**DECIDE D3:** auto-restore on BOTH void reasons (scratched runner AND
market void), or scratched-runner only? (Recommend both — in both cases
the book returns the stake; if a book ever keeps an FB on a market void,
that's a per-book terms observation and the daily-check line catches
the mismatch.)

## Item 3 — Small-field insurance honesty (feedback item 9 follow-on)

**What it protects:** BetRight insurance pays nothing for 3rd at ≤7
runners (confirmed 19 Jul, standing lesson). Today the picker/EV can't
know that — it shows insured-for-3rd EV on a 6-runner field, overstating
the promo. You bet thinking you're covered when you're not.

**Today:** the catalogue's `refund_positions` is a plain list with no
field-size condition; nothing structured can express the clause. BUT the
EV engine **already receives the field size** (`fieldSize`, from the
active-runner count) — it just has no term to check it against. The
race page already knows active (non-scratched) runners.

**Proposed (Option A, recommended):** one new optional catalogue column
— per-position minimum field size (BetRight: position 3 needs ≥8
runners). The EV engine drops an insured position when the ACTIVE runner
count is below its minimum; the settlement-side credit-gap arithmetic
honours the same rule so detector and door agree. The picker shows the
degraded terms plainly ("3rd not covered — 7 runners").
**Option B (cheaper):** no schema change; picker shows a warning chip at
≤7 runners on BetRight-variant promos, EV left optimistic-wrong.

Option A is recommended because the promo-terms lesson says scratchings
can degrade terms AFTER placement — a structured term lets the EV react
to the live active count; a warning chip can't keep the numbers honest.

**DECIDE D4:** Option A (catalogue term + EV honesty) or B (warning
only)?
**DECIDE D5:** if A — the check uses the live ACTIVE runner count
(scratchings degrade terms in real time, matching the lesson), yes?

## Item 4 — Deposit-source door + negative-float tripwire

**What it protects:** the S244 standing rule — "any Tim deposit at a
book = fresh bank money, always" — lives only in memory. Get it wrong
and holder floats drift (that's exactly the Sarie $300 correction).
And nothing anywhere flags a negative float today.

**Today:** money origin is expressed by which event kind you pick on
the movements door (funding = bank in; deposit = out of holder float) —
easy to pick wrong. No source field, no defaulting, no negative-float
check on the balances screen, banner, or daily check.

**Proposed:**
- **Door defaulting:** on the movements form, a deposit to a Tim
  account-at-book defaults to the paired write (funding + deposit — net
  effect "bank money into the book", float untouched); other holders
  default to plain deposit ("from float"). Override stays available;
  the chosen source lands in the notes so the trail reads plainly.
- **Negative-float tripwire (non-blocking):** any holder float < 0 →
  one line in the daily money check's NEEDS-YOUR-EYES block + a
  money-health line on the in-tool banner. Both seams already exist;
  neither has money awareness today.

**DECIDE D6:** the Tim default as a paired write in one door action
(recommend), vs just pre-selecting "funding" and leaving two manual
steps?
**Note:** the tripwire only makes sense after Item 8 clears the current
−$3,126 — otherwise it cries wolf from day one. Sequencing below.

## Item 5 — FB expiry stamping (TAB = 1 week)

**What it protects:** Sarie's $13 nearly died silently this week. TAB
free bets expire in 7 days; the tool banks them with no expiry, so the
pool shows money that may already be dead.

**Today (good news — this item shrank):** the ENTIRE surfacing chain
already exists — the credit payload has an expiry field, the pool
derivation already drops expired credits at read time and sorts
earliest-expiry-first, and the API exposes it. The only gap: **the
credit door writes expiry = none**, so nothing ever expires.

**Proposed:** a per-template expiry-days column (TAB templates = 7);
the credit door stamps credit-time + N days automatically; manual
credits (Item 6) take an optional explicit date. TopBar FB panel shows
the date so a dying FB is visible at a glance.

**DECIDE D7:** default lives per promo template (recommend — same place
the other terms live) vs per book?
**DECIDE D8:** backfill the two currently-banked FBs (Sarie $13 ~25
Jul, Leigh $33 if unspent)? Doable via the existing supersede-correct
pattern, or skip if you'll spend Sarie's this week anyway.

## Item 6 — Dead-heat manual-amount credit door (B1 finding F2)

**What it protects:** dead-heat / removed-runner bonus wins are refused
by the automatic credit door (correctly — the amount needs a human), but
today the only way to write the hand-computed credit is outside the app.
Off-app money writes are exactly what v3 exists to end.

**Proposed:** a manual-amount credit door beside the automatic one:
operator-supplied amount + mandatory reason, same idempotency guard
(one credit per triggering bet), clearly marked operator-manual in the
trail, visible in the daily check. It also becomes the natural home for
any future "book credited something odd" case the auto door refuses.

**DECIDE D9:** restrict it to bets the auto door refuses (dead-heat /
removed-runner shapes), or allow it as a general manual-credit valve
with reason? (Recommend general-with-reason — the promo-terms lessons
keep producing per-book oddities, and the trail + daily check keep it
honest.)

## Item 7 — Void-detector wiring

**What it protects:** a book/Betfair voiding a race AFTER we settled it.
The detector (built in B1) catches exactly that — it re-reads settled
bets' markets and flags any that now read voided — but it's dormant:
nothing calls it.

**Today:** read-only, correctly count-checked (500-bet cap with an
explicit truncated flag — no silent caps), 24h lookback, zero callers.

**Proposed:** run it inside the settlement worker on a throttle (hourly,
not every 60s cycle — each run re-reads Betfair). A hit raises the
in-tool banner + a daily-check line; **the fix action is Item 1's
re-class door** (terminal→void with reason), keeping the detector
read-only and the state change operator-attended. A truncated sweep
says so on the surface.

**DECIDE D10:** operator-attended fix via the re-class door (recommend —
matches attended-only money philosophy), vs auto-flip hits back to the
manual queue?

## Item 8 — Day-zero float semantics (question answered; no code change)

**The −$3,126 explained (grounded, not a bug):** the float derivation
subtracts every book deposit from the holder's float. The S232 seed
wrote your real book balances as day-0 openings, but the bank money that
originally put that cash into the books was never booked into the
floats — so the floats read as "drained" by money that never notionally
passed through them. Everything still reconciles to the cent because
books + floats together net correctly; only the float sub-total is
skewed.

**Proposed fix — an operator data action, not a build:** one signed
opening-balance funding pass (a funding event per holder, dated day-0,
sized to the seeded book cash that was bank-funded), through the
existing doors, exactly like the S244 per-holder corrections but
completed for all holders. After it, floats read true and Item 4's
tripwire can go live without crying wolf. I can prepare the per-holder
amounts for your sign-off from the day-0 seed events — the split
between "was bank money" and "was already circulating float" is a
real-world fact only you can confirm.

---

## Suggested build shape (after walkthrough)

One brief, one background build, per the ratified pattern — but
internally ordered:
1. **Independent smalls first:** Item 5 (expiry stamping), Item 6
   (manual credit door), Item 2 (auto-restore) — three thin doors on
   existing primitives.
2. **The coupled pair:** Item 1 (re-class door + audit-type migration)
   then Item 7 (detector wiring pointing at it).
3. **Ledger pair:** Item 8 (operator data pass, needs your amounts) →
   then Item 4 (door defaulting + tripwire).
4. Item 3 (insurance honesty) sized by D4 — Option A touches catalogue
   schema + EV engine + credit-gap arithmetic (the largest single item);
   Option B is an afternoon.

## Decisions for the walkthrough (all in one place)

- **D1** Re-class: any terminal→terminal, or →void only?
- **D2** Hard delete stays fenced as-is?
- **D3** Auto-restore on both void reasons, or scratched-runner only?
- **D4** Small-field honesty: catalogue term + EV (A) or warning chip (B)?
- **D5** If A: judge against live ACTIVE runner count?
- **D6** Tim deposit = one paired door action, or pre-selected kind only?
- **D7** FB expiry default per template, or per book?
- **D8** Backfill Sarie/Leigh's banked FBs with expiry?
- **D9** Manual credit door: restricted shapes, or general valve?
- **D10** Void-detector hits: fixed via re-class door, or auto to manual queue?
