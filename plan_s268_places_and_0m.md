# S268 — two plans for review

Written 6 Aug 2026, ~08:45 ACST. Both are PLANS. Nothing applied.

---

# PLAN A — Places on the day (`s267-place-only`)

## What it is

`_check_settlement` only ever polled the Betfair WIN market, so
`result_status = 'PLACED'` could only come from the nightly subscription
sync at 05:30 Adelaide. In a Betfair PLACE market the place-getters
settle as `WINNER` — same `get_market_results` call, against a market id
we already store (195 of 282 AU races on 5 Aug carried one).

Two commits off `7fb7bef`:
- `026477b` — the change itself (`capture/orchestrator.py`, +56)
- `6e21a05` — records the measured lag as a known limit
- `tests/test_place_settlement.py`, +142

**Measured live over 4 races (S267):** Bendigo win 2.4 min / place — the
lag figures are in `SESSION_267.md §6`.

**Honest limit, already documented in the commit:** this gives the SET of
place-getters, not their ORDER. 2nd vs 3rd still waits for the
subscription's `finish_position`.

## Why it is safe by construction

- **Additive.** If the place market has not closed, the call returns
  nothing and every non-winner stays `LOSER` exactly as today. The
  overnight feed still fills it.
- **Completion flow untouched.** `_check_settlement` stays one-shot and
  marks the race COMPLETE off the WIN market alone. A slow or missing
  place market costs freshness, never capture.
- **Errors contained.** A place-market exception is caught and logged
  without touching win settlement.

## THE HAZARD NOBODY HAS NAMED YET

Both branches were cut from `7fb7bef`, which is **before** this morning's
sandown fix (`efcde0d`). `git diff master..s267-place-only` therefore
shows my S268 census fix as a *deletion* of 12 lines in
`scripts/liveness_check.py`.

A true three-way merge is safe — the branch never touched those lines, so
master's version wins. **A rebase-and-force, a squash onto the old base,
or any wholesale file copy silently reverts the fix and brings back the
45-minute country-stamping alarm.**

→ Merge. Do not rebase. Verify the `country = 'AU'` clause survives in
the merged file before pushing, and re-run the live check.

## Steps

1. `git merge master` into `s267-place-only` (bring the branch forward),
   resolve nothing — expect a clean merge.
2. **Verify the sandown clause is still present** in
   `scripts/liveness_check.py` post-merge. Grep for `country = 'AU'`.
3. Full suite local: `python3 -m pytest tests/ -q` — expect 624 + the
   place tests, all green.
4. Fast-forward `master`, push to VPS (`origin`) and GitHub.
5. **Gap-aware restart** — `scripts/collector_restart.py`, never bare
   `systemctl restart racing-capture` (S259 pattern; the bare restart is
   what cost 2h16m in S266).
6. Watch one settlement live and confirm `PLACED` appears within minutes
   rather than at 05:30.

## Timing

Any time. The write is per-race at settlement, tiny, and additive. No
maintenance window needed. Restart must be gap-aware.

## Acceptance

- A race settling after the restart has its place-getters marked the same
  day, minutes after the jump.
- No change to win settlement timing or to COMPLETE marking.
- Country-stamping check still green (proves the merge did not revert).

---

# PLAN B — 0m, the 679 stuck duplicate races

## Standing

This is the ONLY thing that will clear them. The twin backlog is
otherwise at zero: the 679 are exactly the refused classes (540 identity
gate + 139 settled-audit), set-identical to the S263 census, no new twin
since 28 July.

**An adversarial review already exists** (`plan_0m_review_s267.md`, 207
lines) and returned **NO-GO as written** on M1 with five blockers. Two
are now closed by `b983212`:

- **B1 `--reverse` did not exist** → built. `reverse_run` restores the
  five race columns, the DELETED snapshot rows *with their original ids*,
  and the runner stamps. Nine tests prove the round trip returns the DB
  to its starting state. `betfair_sort_priority` — nulled but never
  pre-imaged, so unrestorable — is journalled now.
- **B4 the dry run could not say what the clears rested on** →
  `--report` emits one CSV line per market with both fragments' verdicts.

**Measured against live:** of 369 proposed clears, **only 11 (3%) rest on
the s3 signal alone** — the snapshot-day signal the mini-brief
disqualified as sole authority. 167 multi-signal, 118 s1-only, 73
s2-only. **Excluding s3-only costs 11 markets and removes the review's
central objection (B3).**

`not_refused` was renamed `settle_class_skipped` — those markets WERE
refused, at the settled-count gate.

## What is STILL open from the review

- **B2** — the plan text says "no deletions"; `apply_clear()` deletes
  snapshot rows and writes `runners`. **The plan text must be corrected
  to describe the actual write set** before anyone approves it.
- **B5** — zero ops rails. No disk gate, no WAL checkpoint, no lock
  watchdog, no yield-to-capture, no deadline, no preflight, never calls
  `verify_no_orphans`. And `repair_lock_guard.py` hard-codes
  `REPAIR_PROCESS = "merge_market_twins.py"`, so started alongside this
  script it logs "nothing to guard" and exits 0.
- **Sequencing vs the Betfair historical import.** The importer's
  strongest matcher is keyed on exactly the two columns M1 nulls, and
  `UNIQUE(bf_win_market_id, bf_selection_id)` means a wrong attachment
  cannot be fixed by re-import. **Run order is decisive.** The import
  timer next fires 11 Aug.
- **The rekey interaction.** M1 moves 369 rows from the market-keyed set
  into the market-LESS set — i.e. into `migrate_intl_venue_keys`'s scope,
  whose safety proof rests on non-AU market-bearing rows being zero, and
  whose collision path MERGES with a `--reverse` that cannot un-merge.
  Probably zero overlap (the brief's venues are all AU). **One query.
  Nobody has run it.**
- **No restore drill.** No test reads `market_stamp_corrections` back
  against a real database.
- **No read-side before/after.** Acceptance checks each race is still
  *served*, not that it serves the same content.
- **No stop rule.** 369 markets in one loop with no abort threshold.

## Proposed scope: M1 ONLY, minus s3-only

**358 markets** (369 − 11). M2/M3/M4 have **no code** and M3/M4 were
NO-GO on substance, not on polish. They are not in this plan.

Census after M1: ~310 remain. **Say this out loud** — the review's
sharpest non-technical point is that the plan's narrative called the
remainder "classes it was not built for" while ~124–174 of them are the
*largest correctable class*. This plan does not clear those and does not
pretend to.

## Steps

1. **Correct the plan text** to the actual write set: clears the market
   stamp, DELETES snapshot rows, NULLs `betfair_selection_id` +
   `betfair_sort_priority`, NULLs `scheduled_start` where S2 fired,
   overwrites `match_method`. All journalled and now reversible.
2. **Exclude s3-only clears.** 358, not 369.
3. **Run the rekey-overlap query.** If any of the 358 is non-AU, stop.
4. **Port the rails** from `merge_market_twins.py`: disk gate, WAL
   checkpoint, yield-to-capture, deadline, preflight, `verify_no_orphans`.
   Teach `repair_lock_guard.py` this process name.
5. **Restore drill on a COPY of the live DB.** Apply a batch of 25,
   `--reverse` it, diff the copy against its pre-image. Byte-identical or
   stop.
6. **Batch 25 → verify → continue**, with a per-market ledger and a stop
   rule: any batch whose read-side coverage comparison moves, abort.
7. **Read-side before/after** per market: runner counts and stamped
   selection counts, not merely "still served".

## Timing

- **After 04:40 has settled** and inside a maintenance window — the write
  profile is unbounded (megabytes of depth JSON per row × 358) against a
  live 5 GB DB the collector is writing.
- **Before the 11 Aug Betfair import fires**, or with the import's
  interaction proven safe first.
- Today is a quiet Thursday, which is what it has been waiting for — but
  the rails and the restore drill come first, and they are the bulk of
  the work.

## Honest assessment

Steps 1–5 are the real job; step 6 is the easy part. This is not a
"run the tool" afternoon. If the operator wants the 679 gone today, the
answer is that the safe version takes most of a working session and
clears 358 of them, not 679.

---

# ALSO FOUND, not part of either plan

The **intraday results timer is running on the VPS from source that
exists only on `s267-0m-prep`** — not on master, not in the VPS git
checkout. It is the thing that took today's places from 0 to 214. A
redeploy from master would not rebuild it and nothing on master describes
what is running. It should be merged regardless of what happens to 0m.
