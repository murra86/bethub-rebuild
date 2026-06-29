# Operator workflow map

**Mapped + operator-validated:** Session 185, 2026-06-24 ACST.
**Scope (v1 — A):** Strategy 1 (Safety Net insurance, the 2nd/3rd
refund variant) plus the free-bet conversion cycle. This is ~95%
of the current operation. Other workflows — boosted-winnings /
boosted-odds lays, non-promo turnover offsets, and the future
Strategy 2–4 shapes — are out of scope here and get mapped in
their own sessions.
**Status:** operator-domain truth. Slow-changing. Feeds v2
refinement and next-iteration design.

---

## 1. What this is

A map of the *current real betting workflow at the activity
level* — what the operator is physically doing, the systems
underneath each activity, the connections between them, and the
friction / design signals that fall out. It is deliberately
heavy on the operational detail (what the hands are doing) and
light on the software internals (concept-level only).

It exists to do three things: capture the workflow as it
actually runs today, give a shared reference for refining v2,
and shape the design of the next iteration of the tool —
including spotting improvements and making fixes easier to
reason about.

---

## 2. The bet-day shape (the routing model)

The defining tension: the operation is **forced serial by
infrastructure, the opportunity is parallel, and the clock is
fixed.** Only one IP connection can be live at a time, so
AdsPower accounts are worked one at a time with a switch cost
between each. But races jump on a schedule the operator doesn't
control, and the operator often wants the same race across
several accounts. So a bet day is a continuous fight between a
switching bottleneck and the jump.

**There is no account queue or fixed order.** The operator is
continuously re-solving *"what's the cheapest next move from
where I'm standing right now?"* — where cost is dominated by
AdsPower-switch cost and races are expiring on a clock. Stay in
the current AdsPower profile if it's useful next; jump to
whichever account has the earliest promo race; drop to the phone
for the own-name account opportunistically. Missing a race to
time pressure is a known, accepted outcome of this.

**The phone is the one parallel lane** — the own-name account is
placed by hand on the phone so the computer stays free for
AdsPower. This is what gets hectic near the jump: juggling a
computer-account and a phone-account at once.

### Physical setup

- MacBook Pro, two external monitors.
- Laptop screen (in front): utility.
- Primary screen (in front): the soft book — or the phone.
- Vertical monitor (to the right): the bet tool.
- Phone: own-account bets, freeing the computer for AdsPower.

### The account-switch gate (the dominant cost)

Switching from one AdsPower account to the next:

1. Close the current AdsPower tab.
2. Wait for it to disconnect.
3. Change to a different router on the MacBook.
4. Open the next account's AdsPower browser.
5. Re-embed / reconnect.

Pure overhead that buys nothing toward a bet. It scales linearly
with the number of accounts and it eats the pre-jump window.
Every time a free bet needs converting later, this same gate is
paid again to get back into that account.

### Pre-day

The operator already knows the day's promos going in — from
habit, from knowing which days books run which specials, and
sometimes from emails. Opens them, looks at which races carry the
specials, and gets a sense of the times across the day so the
day can be prioritised. Promo *scheduling* is currently held in
the operator's head (see §5).

---

## 3. Core cycle 1 — the insurance back-bet loop

**Unhedged.** The operator wants the runner to win — that's the
profit outcome — and the 2nd/3rd refund is the safety net, not a
hedge. There is **no exchange leg in this loop.** (All the
insurance-strategy lays live in the conversion loop, §4.)

Worked example: a race with ~8 minutes to jump, three accounts
wanted on it. The operator generally ends up on **different
runners across the accounts** — prices drift in the intervening
time, and spreading runners helps account care and casts a
wider net (slightly risk-averse).

The loop, per account, repeated across accounts:

| Activity | System underneath | Connection | Friction |
|---|---|---|---|
| Switch into the account | AdsPower + router + MacBook | Hard serial gate — nothing starts until connected | The dominant cost; scales with account count |
| Promo prep | Bet tool race page | Sets the EV column's mode (§5) | Per-race, live; reconfigured as races change |
| Read + monitor the market | Soft book + bet tool | Soft-book odds → tool odds column → EV | Manual odds-mirroring under the clock (risk surface) |
| Pounce — place the back | Soft book | EV column = the take/skip call | Decision under time pressure |
| Cover behaviour | Soft book | Account-health layer | — |
| Log the bet | Bet tool | Re-key the just-placed bet into BetHub | Manual re-entry at the jump |
| Switch out → next move | AdsPower + router | Back to the routing decision | Pays the gate again |

Detail on the two manual surfaces, because they're where errors
are born:

- **Read + monitor (pre-bet).** The operator loads several
  runners' odds into the tool's race page and **hand-updates the
  soft-book odds in the tool's odds column as prices shift** —
  watching them move, aware of time-to-jump and the other
  accounts waiting — then pounces. So the take/skip moment isn't
  one read; it's a live monitoring loop.
- **Log the bet (post-bet).** Place the soft-book bet, go to the
  tool race page, click Log Bet, enter the information, submit,
  resume betting.

**The phone lane** runs alongside for the own-name account — same
workflow, different device, still logged through the tool.

---

## 4. Core cycle 2 — the free-bet conversion loop

Triggered when an insurance bet places 2nd/3rd. **This is where
all the insurance-strategy lays live.**

Worked example: the three accounts above landed on three
different runners — A won, B placed 2nd, C ran last. A and C
self-resolve (a glance at the result settles them). **B is the
one that needs action** — it becomes a free bet.

**The hinge:** in the bet log, mark the bet as **triggered** →
the tool credits the free bet to the associated account. One
click that converts an insurance loss into a free-bet asset.

The conversion itself, usually batched into a lull (because it
pays the AdsPower gate again):

| Activity | System underneath | Connection | Friction |
|---|---|---|---|
| Mark bet triggered | Bet tool (bet log) | Credits the free bet to the account | The cross-cycle hinge |
| Switch back into the account | AdsPower + router | Re-enter to spend the free bet | Pays the gate again |
| Find a good price | Soft book + bet tool | EV column in conversion mode | Hunting across a race or two |
| Place the free bet at the soft book | Soft book | — | Wait for confirmation |
| Lay the same runner | Bet tool → Betfair modal | Soft-book free bet ↔ exchange lay | Manual, but the modal makes the order easy |

The **"good price" call**: a free bet converting around **70%**,
usually a **$6+ runner** — read straight off the EV column in its
conversion mode (lowest lay price + the race/venue commission
rate). The operator trusts that number and fires.

Settlement is **lagged by design** (see §5) — so a conversion may
happen well after the qualifying race, sometimes the next day.

---

## 5. Cross-cutting layers

### The EV column (one column, mode-selected)

There is **one EV column** on the race page. The promo buttons at
the top are a **mode selector**: pick Free Bet and the column
computes free-bet-to-cash conversion; switch to Insurance 2nd/3rd
and the *same* column recomputes for that promo against the same
race. The column always reflects "the currently applied promo,
for this race." It is the decision surface for **every** promo
type the operator runs — which is exactly why total trust in it
is load-bearing, and why calculation correctness is the
highest-stakes thing in the tool.

### Promo prep (per-race, live)

Not a start-of-day pass. As races come up: click the buttons at
the top of the race page, enter fields where required, and rely
on the promo EV. Reconfigure between promos as the day
progresses — e.g. 12:32 is an insurance 2nd/3rd up to $50 bonus
cash, 12:43 is an insurance 2nd $50 real cash; or one race (a
Melbourne Cup) carries five different promos needing
reconfiguration between them.

### Settlement checking (lagged by design)

Wins and last-place runners self-resolve on a glance at the
result. The 2nd/3rd refund is the one that needs an action (mark
triggered). Under burst pressure the checking slips to the next
lull, sometimes to the next day. **Design signal:** open cycles
have to be held by the tool, not the operator's memory.

### Account-health behaviours

- Different runners across accounts (wider net + account care).
- Cover browsing — an article, some site activity — after a bet.
- Per-account isolation: AdsPower fingerprint + router/IP, one
  live connection at a time.

### Promo scheduling (currently in the operator's head)

Mostly tracked mentally across the day. Named by the operator as
the thing the tool should take over.

### End-of-day cleanup

No formal close — the day trails off as the promo races end.
Throughout the day the operator is pushing and pulling between
placing, settling, and cleaning up free bets. Before closing
off, a deliberate pass to get things in order and **use all the
free bets so none sit dormant.**

---

## 6. Friction & design-signal register

The bridge from "what happens" into "what the tool should do."
Five signals, then the named manual re-entry points.

1. **AdsPower-switch cost dominates routing.** Everything bends
   around it; it's paid again on every conversion. The biggest
   single lever — anything that reduces or parallelises switch
   cost compounds across the whole day.
2. **Open cycles must be held by the tool, not the operator's
   head.** Settlement / refund-checking is lagged, sometimes to
   the next day. The tool should surface "awaiting result" and
   "free bet ready to convert" as standing queues.
3. **Manual odds-mirroring is the hidden risk surface.**
   Hand-copying shifting soft-book odds into the race page during
   a burst is where wrong-runner / wrong-odds errors are born —
   and it sits **upstream of the EV the operator fully trusts.**
   Bad odds in → wrong EV fired on.
4. **The EV number carries the whole operation.** Both cycles,
   total trust. Calculation correctness is the highest-stakes
   thing in the tool.
5. **Promo scheduling lives in the operator's head.** Named as a
   thing to move into the tool.

**Named manual re-entry points** (each a time + error cost under
the clock):

- **Odds-mirroring (pre-bet)** — maintaining the soft-book odds
  in the race page column as prices move.
- **Log Bet (post-bet)** — re-keying the just-placed bet.
- **Late-entry fallback** — when it's truly hectic, bets logged
  later rather than at the time. A known data-quality cost: the
  operator tries to capture at (or near) the time of bet for
  clean analytics later.

**Future-relief items the operator has already named** (parked —
out of this doc's scope to design, noted so they're not lost):

- Auto-placing / auto-settlement of bets.
- Tool-side promo scheduling.

---

*Operator workflow map v1. Scope A (insurance + free-bet
conversion). Mapped and operator-validated Session 185. Extend
with the remaining strategy workflows in their own mapping
sessions.*
