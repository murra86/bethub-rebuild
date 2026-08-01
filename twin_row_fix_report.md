# Twin-row fix — done and live (0l, Session 259, night of 29–30 Jul)

## What this means for your betting day

- **The blank-odds-column problem is fixed for good.** Yesterday's broken
  Randwick races were re-tested live after the fix: every runner now shows
  with its prices and scratchings. Any future meeting that gets split the
  same way will still price correctly — the app now reads across the split
  instead of landing on the empty half.
- **The capture data-loss problem is fixed.** The collector can no longer
  run two trackers over one race (that was losing the final minutes of
  odds and corrupting settlement, like Randwick R3 on Tuesday). One race,
  one tracker, one row — enforced when rows are created, not patched later.
- **The duplicate history is being cleaned up.** Every duplicated race
  since March is being merged into a single correct row, with a full
  before-image of everything changed kept in the database, plus a verified
  backup taken first (`capture.db.bak-s259-pre-twinrepair-20260729-122248`).
  Recent weeks are already done. The full clean-up runs overnight and
  stops itself at 4:30am so it never touches the racing day; it resumes
  the next quiet night automatically until finished (1–2 more nights).
- **The overnight "Stamped coverage" alert spam (9 emails Tuesday night)
  should stop** — those alerts were the duplicates talking.

## How it was checked (confidence: HIGH)

- Three independent adversarial design reviews before any code was
  written; every issue they raised was fixed in the design first.
- 252 automated tests green (54 new ones written to fail first).
- A full dress rehearsal ran on a copy of the live database before the
  real thing; every safety check came back clean (nothing orphaned,
  nothing lost).
- A canary pass on the last 10 days ran first: 55 of 58 duplicates
  merged cleanly. The other 3: 1 was correctly left alone (too close to
  a race), and 2 were REFUSED by the safety guard because the runner
  names didn't match — meaning those two aren't duplicates at all but a
  different, rarer labelling error. The system refuses to guess; they're
  parked on a review list (below).
- The fix never guesses about horses: prices only ever attach to a runner
  when the horse's NAME agrees across the duplicate rows. If identity
  can't be proven, the app shows a blank rather than a wrong price.

## Nothing needed from you

Tomorrow's racing runs on the new code automatically. If you want a
2-minute eyeball: open any race and check the TAB column looks normal.

## Small follow-ups (mine, not yours)

- Confirm the overnight repair finished across the next nights and
  re-run the duplicate census (expect: zero).
- Review the 2 refused Wagga greyhound markets (wrong market label, not
  twins) — likely a tiny one-off correction.
- One analytical dataset (model.db, parked research) should be
  re-extracted before it's next used — its race ids pre-date the merge.

Technical detail: `twin_row_fix_brief.md` (design + review record),
`sessions/SESSION_259.md` (build record), capture repo commit `6566641`.

## Independent verification (added Wednesday morning, at your request)

Two fresh, independent checks ran over everything above.

**Every row of data is accounted for — nothing was lost or changed that
shouldn't have been.** A verifier compared the repaired database against
the untouched backup, row by row: all price history totals match the
backup exactly, every merged row is fully journalled, every refused
market is byte-identical to how it was before, and the only two runner
entries removed in the whole repair were verified empty duplicates.
Confidence: HIGH — these are measured counts, not spot checks.

**The code check found no critical faults, and two worthwhile
improvements which are already fixed, tested, and will be live for
tonight's run:** the repair now refuses (rather than notes) a merge
whose results look contaminated, and it keeps the most complete closing-
price record when duplicates disagree. A follow-up check confirmed the
second issue caused **zero damage** in what already ran — all 2,136
affected races were re-checked against the backup and every one was
already correct.

**Two honest corrections to the earlier summary:**
- The Pinjarra example I cited is still in the remaining backlog (the
  first night stopped before reaching it) — it merges tonight.
- The verification found 12 old races (from the March–April mess) where
  the two duplicate rows had recorded *different* race results — a
  pre-existing recording fault, not merge damage. Both versions are
  preserved, tonight's run now refuses that class, and they're on the
  review list with the other oddballs (~200 mislabeled markets).
