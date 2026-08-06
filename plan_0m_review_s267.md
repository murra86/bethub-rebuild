# ADVERSARIAL REVIEW — plan_0m_reviewlist_s267.md (S267, 5 Aug 2026)

## VERDICT PER PHASE

| Phase | Verdict | Reason |
|---|---|---|
| **M1** | **NO-GO as written** → GO-WITH-CHANGES after the 5 blockers | No `--reverse` exists; the script does things the plan says it does not |
| **M2** | GO-WITH-CHANGES | 6 markets, low risk — but **no code exists**, and its population sits inside M1's, so it is not independent |
| **M3** | **NO-GO** | Re-dating can violate `UNIQUE(race_date, venue_normalised, race_number)`; handing the row to the nightly gate schedules a **row-deleting** merge; no code exists |
| **M4** | **NO-GO** | One paragraph for the only phase that writes `runners`; the named authority is circular |
| **M5** | GO | "Leave it and write it down" — but it silently absorbs ~167 markets the brief called the *largest correctable class* |

## BLOCKING

**B1. There is no `--reverse`. The plan's precondition for M1 is false.**
`scripts/reviewlist_correct.py:301-306` — argparse exposes only `--db` and
`--apply`. Nothing reads `market_stamp_corrections` outside an assertion in
`tests/test_reviewlist_correct.py:137`. Two sibling scripts DO have one
(`correct_country_stamps.py:170-210`, `migrate_intl_venue_keys.py:564-709`),
so its absence is an omission, not a design choice. Plan acceptance #3 is
**not merely unverified, it is unexecutable**.

**B2. `apply_clear()` DELETEs rows. The plan says it does not — twice.**
`reviewlist_correct.py:259-264` deletes from `betfair_snapshots` and
`bookmaker_snapshots`, against plan `:39-41` ("No deletions") and `:117`
("Deletions of any kind" out of scope). It also does four things beyond
clearing the stamp: `:276-279` NULLs `runners.betfair_selection_id` **and**
`betfair_sort_priority`; `:282-285` NULLs `scheduled_start` when S2 fired;
`:283` overwrites `match_method`; `:259-264` deletes snapshots. **A
reviewer reading only the plan approves a materially smaller write than
will execute.**

**B3. The adjudication answers the wrong question, and one false signal
convicts.** `:202-207`: `keepers = [f for f in frags if not
wrong_marks[f["id"]]]` — **the keeper is chosen by absence of evidence, not
presence of it.** A fragment with all-abstain is a valid keeper; a single
"wrong" mark on the other condemns it.

What S1/S2/S3 measure (`:131-157`) is *internal self-consistency of a row's
date against its own start and snapshot times* — not *"this row does not
own this market"*. The brief's entire premise is that DR-036 **mis-dated
the true owner** (`mini_brief:20-24`). A signal set that condemns the
mis-dated row condemns the bug's victim whenever the victim is the owner.

**S3 is explicitly disqualified evidence and is used unguarded.**
`mini_brief:88-92`: *"both rows show captured on 566 markets… so 'which row
has capture' is NOT sufficient adjudication evidence on its own; ownership
must come from Betfair-side truth."* Worse, `_snap_day()` (`:160-175`) takes
`MAX(snapshot_time)` across both snapshot tables — so on a **contaminated**
row (~249 of 679, `mini_brief:135-136`) the latest snapshot is the foreign
day's, S3 fires "wrong", and the contaminated row is condemned.
Contamination is precisely the signature of the row that *received* real
data. The F2 corroboration rule (`:209-217`) applies **only** when the
wrong-mark set is exactly `["s1"]` — no corroboration for S3-only or
S2-only clears.

**Damage on inversion:** the true owner loses `betfair_win_market_id` → no
BSP (`api/routes/results.py:39-45`), dropped from `/soft-odds` and
`/results/by-market` (`api/market_resolution.py:70`), dropped from the
morning sweep (`scripts/morning_sweep.py:352-357`), and the historical
importer's strongest strategy `(market_id, selection_id) → runner_id`
(`import_betfair_historical.py:474-482`) resolves the market to the
**impostor race**, silently attaching real BSP to the wrong race at
confidence 1.0.

**B4. The dry run cannot tell you how many of the 369 rest on the
disqualified signal.** `:359-366`: `leave_reasons` is populated only for
leaves. Clears increment a bare counter; `verdict["why"]` is discarded. No
CSV, no per-market line, no evidence file. So "how many of the 369 are
S3-only?" — the question that decides whether B3 is theoretical or
systematic — is unanswerable today. This also makes plan `:46-48`'s
"hand-verify a 10-market sample" unsupported: 10/369 is 2.7%, there is no
artifact to sample, and **the plan proposes verifying against a standard
the tool does not implement** (`:48` names Betfair settled winner → market
event time → selection-id congruence; none is S1/S2/S3). The mini-brief
required a classify script emitting `data/twin_reviewlist_YYYYMMDD.csv`
with per-market confidence (`:191-200`) AND an operator review step
(`:201-202`). Neither exists; the plan silently drops both.

**B5. Zero ops rails. Every other write script here has them.**
`reviewlist_correct.py` has no disk gate, no WAL checkpoint, no lock
watchdog, no yield-to-capture, no deadline, no preflight, and never calls
`verify_no_orphans`. Compare `merge_market_twins.py:15-45,190-191,209,250,264-282`
and `migrate_intl_venue_keys.py:49-51,200-206`. This matters: `:249-258`
reads every column of every snapshot row for the loser race — including
`back_depth_json`/`lay_depth_json` — and `:295-296` serialises the set into
one JSON string. **Megabytes per row × 369, into a live 5 GB DB with no
disk check and no checkpointing**, while the collector holds read
snapshots. And the guard cannot cover you: `repair_lock_guard.py:46`
hard-codes `REPAIR_PROCESS = "merge_market_twins.py"` — started alongside
this script it logs "nothing to guard" and exits 0.

## NON-BLOCKING

- **N1** `betfair_sort_priority` nulled (`:278`) but not journalled
  (`:274-275`). Irreversible. Downgraded: no reader anywhere; heals
  fill-if-null. Fix the pre-image anyway.
- **N2** `snapshot_batch_summary` left describing deleted snapshots;
  `twin_merge.py:488-507` handles this explicitly, this script does not.
- **N3** `betfair_historical` rows left pointing at the cleared race.
  `_CHILD_TABLES` (`twin_merge.py:51`) includes it; this script does not.
- **N4** Acceptance #2 ("orphan scan zero") is vacuous — M1 deletes no
  `races`/`runners` rows so it cannot fail, and the script never calls it.
- **N5** Creating `market_stamp_corrections` violates `mini_brief:220-223`
  ("**No schema changes of any kind**" — 0n holds the schema-lock).
  Defensible, but the plan should say so.
- **N6** `match_evidence` left stale (journalled, reversible).
- **N7** S1's envelope is weak: `build_envelopes` (`:116-128`) takes
  MIN/MAX over all single-row markets on a date globally, including
  international and including mis-dated markets. Real consecutive-day
  ranges likely overlap heavily, making F2's test nearly free. The test
  seeds *disjoint* ranges (`tests:79-81`), which reality is not.
  **Unverified — measure before any S1-only clear.**
- **N8** **Re-stamping is NOT a risk** (credit where due). No "unmatched
  races" backlog query exists. Both accidental re-stamp paths
  (`identity_sweep.py:304-330`, `database.py:401`) are fenced by a ±26h
  catalogue window that the script's 14-day age fence puts out of reach.
  Cleared rows drop cleanly out of `find_twin_markets`. Risk closed.
- **N9** Dry run confirmed side-effect-free (`:288` gated on `args.apply`).
- **N10** Crash-resume works by accident (cleared markets drop out of the
  census). Worth stating explicitly.

## FACTUALLY WRONG IN THE PLAN

| Plan says | Truth |
|---|---|
| "No deletions, no merges, no runner moves" (`:39-41`, `:117`) | Deletes snapshots; writes `runners` (`:259-264, 276-279`) |
| "A `--reverse` path must exist… confirm it does" (`:52`) | It does not (`:301-306`) |
| "clears the market-id stamp from the non-owner fragment" (`:41`) | Also nulls `scheduled_start`, selection ids, sort priorities; rewrites `match_method` (`:276-286`) |
| "M1+M2+M3 clear roughly 400–420" (`:98`) | 369 + 6 + (10–30) = **385–405** |
| adjudication verified against Betfair settled winner etc. (`:43-48`) | The script implements none of those three |
| `'not_refused': 138` presented undecoded (`:16`) | These markets **were** refused — at the *settled-count* gate, not the identity gate. The label is actively misleading |
| gate untouched (claim 7) | **HOLDS** — `:56` imports `_gate_ok`/`_named_keys` read-only and mutates neither |

**Arithmetic reconciles exactly:** 369 + 172 + 138 = 679 ✓; 172 = 167+3+2 ✓;
gate-failing 2-fragment = 369+172−3 = 538, +2 three-fragment = 540 ✓;
settle = 138+1 = 139 ✓; census after M1 = 310 ✓.

**What is NOT coherent is the narrative:** `:22` calls the remaining ~310
"the classes it was not built for", but M2+M3+M4 accounts for only
~136–186. The other ~124–174 — dominated by the 167 `no unique
keeper/loser` clean class-A pairs, which `mini_brief:149` sizes as the
**largest** correctable class — fall into M5 "leave". The plan never says
this out loud. Acceptance #1 ("no market silently skipped") cannot be met.

## MISSING ENTIRELY

1. **Sequencing against the Betfair historical import.** The importer's
   strongest matcher is keyed on exactly the two columns M1 nulls
   (`import_betfair_historical.py:474-482`), and
   `UNIQUE(bf_win_market_id, bf_selection_id)` (`:390`) means a wrong
   attachment cannot be fixed by re-import. Run order is decisive.
2. **The 04:40 deploy interaction is understated.**
   `migrate_intl_venue_keys.py:14-20` bases its safety proof on non-AU
   market-bearing rows being zero. **M1 moves 369 rows from the
   market-keyed set into the market-less set — i.e. into the rekey's
   scope.** The rekey's collision path MERGES and its `--reverse` cannot
   un-merge (`:39-42`). Probably zero overlap (brief's venues are all AU)
   but it is a one-line query nobody has run.
3. **A restore drill.** No test reads `market_stamp_corrections` back.
4. **Read-side before/after coverage comparison.** Acceptance #5 checks the
   union still *serves* each race, not that it serves the same content.
   Measure runner-count and stamped-selection counts per market.
5. **A stop rule.** No abort threshold, no batching — 369 markets in one
   all-or-nothing-by-accident loop.
6. **Any code for M2, M3, M4.** `mini_brief:191,203` names two scripts;
   neither exists.
7. **M4 is dangerously vague.** Omits: missing target race row;
   `runner_key` collisions; re-pointing snapshot/historical `runner_id`
   FKs; `UNIQUE(race_id, runner_id, snapshot_time)` collisions; conflicting
   `finish_position`. And the authority is **circular** — `:73` names the
   subscription field list as truth while `twin_row_fix_brief.md:69-73`
   names the subscription writer as **G8, the surviving twin generator**.
8. **M3's collision case.** Re-dating can collide with
   `UNIQUE(race_date, venue_normalised, race_number)` — the exact key the
   pair likely now shares. And handing the row to the nightly gate hands it
   to `merge_market`, which **DELETEs donor race and runner rows**. M3's
   "we do not merge here" is true only of M3's own transaction.
9. **Phase independence is asserted, not shown.** M2's 6 cross-code markets
   sit inside M1's adjudication scope; they survive M1 only because
   same-day pairs give identical S2/S3 verdicts and fall to "no unique
   keeper/loser". Lucky, not designed.

## MINIMUM CHANGES TO MOVE M1 TO GO

1. Build and test `--reverse` off `market_stamp_corrections`, including
   snapshot re-insert with explicit ids and a `sort_priority` pre-image.
   Prove on a DB copy **before** any `--apply`.
2. Add `--report` emitting one CSV line per market with per-fragment
   S1/S2/S3 verdicts and the wrong-mark set. Publish the
   S3-only/S2-only/S1-only breakdown of the 369 **before** deciding.
3. Either implement the Betfair-settled-winner test as a required
   corroborator for S3-only clears, or exclude S3-only clears from M1.
4. Port the `merge_market_twins.py` rails and teach `repair_lock_guard.py`
   this process name.
5. Fix the plan text to describe the actual write set; run in staged
   batches (25 → verify → continue) with a per-market ledger.

**Applying to 369 live markets without a reverse:** no. The whole-DB backup
means discarding every capture since it to undo one bad market. The journal
is the surgical undo the brief promised and it has no reader.

**Running on a live race day:** not as built. The 14-day age fence
correctly keeps the write set away from live races — that part is sound.
But the write *profile* is unbounded against a DB the collector is writing,
with no working lock guard. Maintenance window, after 04:40 has settled, in
batches, with rails ported.
