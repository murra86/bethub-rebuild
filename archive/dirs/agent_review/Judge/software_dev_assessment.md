🔴 1. Biggest structural flaw (this will bite you)
You’ve mixed an analytical data system with an operational dependency.
capture.db = designed for analytics (slow, tolerant, batch-like)
v3 = wants execution-time dependency (fast, reliable, always-on)
Those are different systems.
What happens in reality:
SSH tunnel drops (you’ve already seen this)
VPS hiccups
scraper stalls
latency spikes at exactly the worst time (pre-jump)
➡️ You log bets with:
stale snapshots
missing snapshots (bf_snapshot_unavailable = true)
inconsistent context across bets
And now your “source of truth” isn’t actually reliable.
👉 This is the core contradiction:
“No duplication + no caching” vs “mission-critical read dependency”
You can’t have both.
🔴 2. Periodic-only API — good idea, wrong execution
Your bracketing argument is correct (analytically).
But operationally:
Failure mode:
You place bet at T
Snapshots are at T-60s and T+60s
Market moved sharply in that window
➡️ Your “true context” is now ambiguous or wrong
And worse:
you don’t even know how wrong it is
Hidden problem:
You’re assuming:
“Cadence tuning solves this”
It doesn’t.
Because:
volatility ≠ time-based
markets jump in bursts, not smoothly
🔴 3. Bet schema simplification — dangerous if taken too far
You’re leaning toward:
“Store identifiers only, resolve everything from capture.db”
That’s elegant… until:
Failure mode:
capture.db changes (schema drift, bug, backfill issue)
or data gets corrected later
or snapshots are missing
➡️ historical bets change meaning retroactively
That is catastrophic for analytics + reconciliation.
The correct principle:
👉 Bet records must be immutable facts
At minimum, you need:
price taken
available price context
timestamped snapshot reference OR copy
Otherwise:
you are reconstructing history from a system that is not guaranteed stable
🔴 4. You’ve over-optimized for “no duplication”
DR-028 is too strict.
Specifically:
“No race-data caching, no denormalisation”
That’s architecturally pure but practically wrong.
Why:
Some data is:
volatile + external + not guaranteed reproducible
That data MUST be captured at decision time.
Examples:
best back/lay at execution
liquidity snapshot
field size at time of bet
If you don’t store it:
➡️ you lose the ground truth forever
🔴 5. The system assumes perfect VPS reliability (it’s not)
You’ve already proven:
tunnel down for 6+ days
no monitoring
no alerting
no operational discipline
Now v3 depends on it for:
every bet
every settlement
every review
Failure mode:
intermittent failures → silent degradation
not hard failures → worst kind
You’ll get:
partial data
inconsistent behaviour
hard-to-detect drift
👉 This directly conflicts with your #1 goal:
reduce detection time
You’ve introduced a new detection problem.
🔴 6. Missing system: operational pricing layer
You implicitly discovered this in the doc:
analytical vs operational pricing
But didn’t follow through.
You actually need:
System	Purpose
capture.db	analytics (slow, historical, rich)
live pricing layer	execution (fast, real-time, ephemeral)
Right now:
➡️ you’re trying to stretch capture.db to do both
It won’t.
🔴 7. Reconciliation surfaces — good idea, but overloaded
You’re using reconciliation to detect:
operator error
system error
data layer failure
That’s too much.
Failure mode:
You won’t know:
what caused the issue
where to fix it
👉 You need separation of concerns:
data integrity checks (system)
financial reconciliation (operator)
capture reliability monitoring (infrastructure)
⚠️ 8. AccountCare future DB — you’re underestimating this
You said:
“we’ll see later if it needs its own DB”
Pushback:
👉 If AccountCare affects:
decision-making
restrictions
behavioural state over time
…it will become:
high-write
stateful
cross-cutting
That’s a separate bounded context, not just “extra fields”
Risk:
You design integration for 1 boundary (v3 ↔ capture.db)
But future is:
v3 ↔ capture.db
v3 ↔ accountcare
maybe more
👉 Your integration discipline needs to scale now, not later.
⚠️ 9. Coherence check (your explicit ask)
This mostly holds together — but there is one drift:
You’re trying to satisfy 3 goals that conflict:
Zero duplication
Perfect historical reconstruction
Low operational friction + high reliability
👉 You can only fully achieve 2 of the 3
Right now:
design assumes all 3 are possible
they aren’t
🧠 What a sharper engineer would do
Short, practical version:
1. Split the systems properly
Live pricing layer (new)
capture.db (analytics only)
2. Relax DR-028 (slightly)
Allow targeted denormalisation:
Store on bet:
price taken
best available prices
liquidity snapshot
timestamp
Not everything — just irreversible context
3. Keep periodic API (but with a guardrail)
Add:
snapshot freshness confidence
volatility-aware flags
Not just time-based staleness
4. Add infrastructure layer (missing)
You need:
tunnel monitoring
auto-reconnect
alerting
health dashboard
Right now: zero
5. Treat capture.db as unreliable input
Design assumption should be:
“this system will fail regularly”
Then design:
retries
fallbacks
explicit degraded modes
🧩 Bottom line (blunt)
The design is thoughtful but slightly idealised.
Your real risk isn’t:
schema design
API shape
It’s this:
You are building a mission-critical system on top of a data source that has never been operated as mission-critical.
Fix that mismatch, and most of the design works.
Ignore it, and you’ll recreate v2 pain — just in a more sophisticated way.