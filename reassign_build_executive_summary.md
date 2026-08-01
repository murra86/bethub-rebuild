# Wrong-account fix — executive summary (S254, 26 Jul 2026)

## The problem
On frantic bet days, a bet occasionally gets logged on the wrong person's
account. Two real incidents (Leigh/Tim 26 Jul, Kate/Leigh 18 Jul) each cost
hours of hand-fixing with backups, reviews, and ceremony — and sat
undetected for days first.

## What was built (one day, four commits)
1. **Detection** (`b230eab`): the daily money check now runs seven
   coherence sweeps. Any bet/bonus/account mismatch is flagged the
   morning after it happens. Both real incidents would have been caught
   same-day. Today's ledger: zero flags.
2. **The button** (`31d6c66`): "Reassign account…" in the BetLog. Clean
   same-book mistakes become a 30-second self-serve fix — shows the money
   that moves before you confirm, works on settled bets, reversible,
   fully audited. It is now the ONLY way to move a bet (the old unguarded
   dropdowns are gone, and a live gap in them — moving a bet into the
   Betfair lane — was found and closed on the way).
3. **The guided correction tool** (`cf2c691`): for bets with live bonus
   money attached, `ops.correct_promo_chain` walks the fix step by step:
   plans first (writing nothing), confirms in plain language, survives
   interruption and resumes, lists the credit ids it needs from you, and
   only ever APPENDS corrections — ledger history is never rewritten.
4. **First-use polish** (`0169dd4`): every refusal message tells you what
   to do next; ids are paste-ready; the morning check even catches a
   database restored from a pre-build backup.

Where things live: the button in the BetLog; the tool via
`uv run python -m ops.correct_promo_chain` (see
`operator_workflow_map.md` §7 for the operator guide; refused shapes go
to the runbook in `bet_reassignment_door_plan.md` §3e).

## How it was proven
- **Three plan revisions before any code** — two adversarial review
  rounds killed v1 (would have refused both real incidents) and rewrote
  v2 (its key step couldn't execute; its Kate/Leigh prescription would
  have silently double-funded a bet). Nothing weakened any locked rule:
  corrections are new ledger entries, per operator direction.
- **Built test-first throughout**; every safety rule has a test that
  fails if the rule is removed (proven by mutation).
- **The acceptance bar was the real incident**: the 26 Jul Leigh/Tim
  mix-up, replayed from the pre-fix backup through the new tool — once
  straight, once killed mid-fix and resumed — must land every money
  number exactly where the hand-verified fix put them. It does, to the
  cent, on every account, purely append-only.
- **A final four-reviewer whole-system pass** re-proved everything at
  the final code state (including a real button-move-and-reverse on a
  copy of the live ledger, byte-identical restoration) and confirmed:
  **no path exists by which money lands wrongly and silently.** Its
  operability findings were fixed and committed same-day.
- Final state: 1,852 backend tests, full frontend build, database
  migration run on live with locked backups at every step.

## Confidence
**High — this is a rigorous, permanent fix for the wrong-account error
class.** Every claim above is backed by a replayed real incident or a
mutation-proven test, not by inspection alone. Two honest caveats:
1. No *live* first use yet — recommend doing the first real reassign
   together, as with other money features.
2. v1 scope lines, all fail-closed and signposted: cross-book moves,
   expired bonus chains, and a wrong-account *spend* bet whose qualifier
   is correct all refuse to the review runbook rather than self-serve.
   None has ever occurred; they become buttons only if they start
   happening.

## Cost of errors, before vs after
- Before: days undetected → hours of supervised hand-fixing, app down,
  raw database surgery.
- After: flagged next morning → 30 seconds (button) or minutes (guided
  tool), app up, history preserved.

*Record: SESSION_254.md §4h–§4m; plan of record
`bet_reassignment_door_plan.md` (stamped BUILT & SHIPPED); commits
`b230eab`, `cf2c691`, `31d6c66`, `0169dd4`.*
