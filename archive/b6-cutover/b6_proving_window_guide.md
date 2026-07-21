# The proving window, in plain language — what the three ticks are and how to get them

**Drafted:** 2026-07-07 20:08 ACST, Session 233 (headless runner, first action per S232 close).
**Who this is for:** the operator, during normal play. No jargon; every technical term unwrapped.
**What it covers:** gate 9 — the last of the ten cutover checks before BetHub v3 becomes the
official record. The window is not extra work: it is your normal betting days, watched a
little more carefully, with three specific things that have to be seen happening for real.
**Grounding:** the safety-catch section below was checked against the live code (read-only)
this session — nothing in it is guessed.

---

## The big picture in four sentences

v3 already places and settles real bets — that was proven in June/July with real money.
What hasn't happened yet is v3 living through ordinary racing days without anyone holding
its hand. The proving window is that: you bet normally, and the window stays open until
three specific events have each been seen once, with every day signed off. There is no
deadline — it takes as long as those three things take.

Throughout the window, **v2 remains the official record** (the "system of record"). If
anything went badly wrong, v2 is still there, warm, ready to take over. v2's betting
screens stay closed so nothing gets entered twice — it just sits as the safety net.

---

## Tick 1 — one full clean AU racing day

**What "clean" means, concretely.** Take one ordinary Australian racing day where all your
betting ran through v3, and at the end of it every single bet can answer yes to all of
these:

- The bet found its home when you logged it — the right person's account at the right
  bookmaker was there in the picker, no improvising, no "I'll fix that later".
- Every Betfair bet matched (was accepted and filled on the exchange) the way you expected.
- Every finished race's bets settled — the win/loss landed on the right account with the
  right money movement.
- The end-of-day check (below) reconciles: v3's numbers agree with Betfair's own statement.
- Nothing is sitting in the "parked for manual review" queue that you can't explain. Parked
  items are allowed — the queue exists for a reason — but each one has to be understood.
- No workaround was needed at any point. If you had to step outside the tool to get
  something done, the day wasn't clean.

**What you do differently: nothing.** This is a normal day's play. The only addition is the
end-of-day check and a one-line sign-off.

**What the evidence is.** The end-of-day money check output for that day, plus your
one-line sign-off ("day clean" or similar) recorded in the running tally (see "How a day
ends", below). If the day wasn't clean, that's not a failure of the window — it's exactly
what the window is for. The problem gets fixed, and you wait for the next clean day.

**Day 1 carries one extra job (the gate-3 rider).** The rotation — 4 people, 9 bookmakers,
13 account-at-bookmaker pairings — was seeded on 7 July and verified on screen. The first
real racing day confirms it in anger: every bet you place that day should find its account
in the picker naturally. If they all do, the seeding check is re-confirmed in live use and
that rider closes with it.

---

## Tick 2 — one live trip of the safety catch

**What the safety catch is.** Before v3 sends any bet to Betfair, it checks that its live
price feed from Betfair is properly connected. If the feed is down — dropped out,
reconnecting, or still starting up — v3 **refuses to send the bet at all**. Nothing reaches
Betfair; no money is at risk; you get told why. That refusal is the safety catch (the
"interlock"). The point of it: never fire a bet blind, on prices you can't see moving.

**What actually trips it (checked against the code).** Every Betfair placement runs one
check first: is the price-feed connection in its healthy "subscribed" state? Any other
state — disconnected, connecting, logging in, reconnecting — and the bet is refused on the
spot with the message "Streaming connection unavailable; placement queue paused." The check
happens before anything is built or sent, so a refused bet leaves nothing behind to cancel.
The feed repairs itself automatically (it retries on a schedule until it's back), so once
it reconnects, the same bet goes through normally. Note this catch only guards bets sent to
Betfair (your lay/hedge side) — logging a soft-bookmaker bet by hand never touches Betfair,
so it never meets the catch.

**Natural trip vs deliberate drill — recommendation: do one drill.** A natural trip needs a
coincidence: the feed happens to be down at the exact moment you're firing a bet. Feeds do
drop now and then, but the odds of you catching one mid-placement in any given week are
poor — waiting for it could stall the window indefinitely, the same trap the panel already
avoided for partial matches. A deliberate drill is safe and honest: the feed really is
broken, the catch really does fire, and no money can move because the refusal happens
before Betfair is contacted. Suggested drill, five minutes on a quiet evening with no bets
pending:

1. With the app running normally, turn off the Mac's internet (Wi-Fi off).
2. Wait for the red banner to appear: "The live price feed is not connected."
   (Race lookups will also fail while offline — expected.)
3. Try to place a small Betfair lay the way you normally would. It should be refused
   with the feed-unavailable message. Nothing is sent.
4. Turn the internet back on. The feed reconnects itself; the banner clears; you're back
   to normal. Nothing to clean up on Betfair — there's nothing there.

If a natural trip happens first, even better — it counts the same way.

**What the evidence is.** Three things, all automatic:
- The refusal you saw on screen (the bet form's error plus the red banner).
- A line in the app's day-to-day log file saying the placement was refused because the
  feed was disconnected (`~/.bethub/logs/bethub-app.log`).
- An entry in the placement audit trail — the permanent journal that records every
  placement attempt, including refused ones (`~/.bethub/logs/placement-audit.jsonl`).
Note in the day's sign-off that the trip happened and the refusal behaved.

---

## Tick 3 — one real settlement beyond the −$4.91

**Why this one exists.** So far, exactly one bet has moved real money through v3's
settlement machinery end-to-end: the deliberate test lay in the June/July live proof, which
lost $4.91 by design. That proved the plumbing once, on a bet chosen to be a test. This
tick asks for the same thing on a bet that *matters* — an ordinary bet from your normal
play, settling with real money moving, so the money path is proven on a real result rather
than a rehearsal.

**What counts.** Any real bet settling with real money movement — won or lost, either
direction. It just can't be zero dollars and can't be the test lay. On a normal betting
day this happens by itself; there is nothing to arrange.

**Where it shows up.** In the BetLog (the bet's record flips to settled with its
profit-or-loss amount on the right account), and in that day's end-of-day money check,
where the movement reconciles against Betfair's own statement.

**One thing to watch while betting (a known watch-item).** If a Betfair lay only
*partially* matches — the exchange fills some of your stake but not all before the race
jumps — keep an eye on how v3 handles it. The handling code is written and reviewed but
has never been exercised by a real partial match. The designed behaviour is to park
anything it isn't sure about into the manual review queue rather than guess. If a partial
match happens and routes cleanly (settled right, or parked with a clear explanation),
note it in the sign-off — it closes a standing watch-item. If one never happens, that's
fine; it doesn't block anything (decided at Session 231: elective, never a blocker).

---

## How every window day ends: the money check and sign-off

Five minutes at the end of each racing day, every day of the window:

1. In Terminal, from the v3 folder, run: `uv run python -m ops.settlement_review`
   It only reads — it can't change anything.
2. Read what it says: the day's bets, what settled, what's pending, what's parked.
3. Cross-check against Betfair's own statement/balance for the day — do the movements
   agree?
4. Confirm the manual review queue is empty, or that you understand every item in it.
5. Record the running tally and your one-line sign-off in a durable place (written down,
   not memory). A signed-off day is what counts toward the window.

---

## When the window is done

All three ticks seen, every day in between signed off. Then two steps remain, neither of
them yours: a forensic review of all the money-handling code on the exact version that
will go live, and then the flip itself — the scripted morning where v3 becomes the official
record and v2 retires to warm standby for about two weeks. Nothing flips until you've seen
the window hold up and the review comes back clean.
