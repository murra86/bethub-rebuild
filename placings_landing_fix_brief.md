# Placings-landing surgical fix — Code brief

**Status:** LOCKED — 2026-06-29 14:59 ACST (Session 198). Contract;
Code executes against it as written.
**Drafted:** 2026-06-29 (Session 198), Adelaide local
**Commissions:** one bounded Claude Code session against the live
racing-data-capture VPS.
**Serves:** the placings-landing blocker diagnosed in
`placings_landing_diagnosis_report.md` (RC-1 fetch starvation +
RC-2 cross-source overwrite). DR-033 (placings analytical;
settlement Betfair-only) — capture-side analytical only, no
money/settlement path.

---

## §1 — What this brief is and is not

**Is:** a surgical, two-part fix to the capture-side placings sync
so recoverable finishing positions actually land in `capture.db`,
without corrupting cross-sourced runner rows. Part A is a write-side
safety guard (must land first); Part B is the fetch-side fix that
ends the starvation. Single bounded Code session.

**Is not:** a schema change, a refactor, a rewrite of the sync
path, or a recovery run. The recovery itself (replaying the backlog
once the fix proves out) is a *separate* later step, not this brief.
Surprises become findings in the report, not mid-session escalations
or scope additions.

**Bet-safety:** analytical/capture-side only. Touches no v3 code, no
settlement, no money path, no Betfair operational pricing. The data
being fixed is backward-looking finishing positions used for model
calibration, never live bet placement (DR-033).

---

## §2 — Why this work exists

The S196 trickle fix proved the unjam mechanism but exposed the real
blocker: the Racing API holds the placings, yet the sync isn't
persisting them for the recoverable tail (dates from 2026-03-15
onward). The S197 diagnosis traced this to **two** bugs, not one:

- **RC-1 (dominant — fetch starvation).** The nightly oldest-first
  backlog walk burns its per-night attempt budget on the near-done
  early-March dates (stuck on a genuine ~8% residue that will never
  complete). The recoverable tail is reached only after the budget
  is spent. Worse: a date whose fetch is cut short part-way (quota
  exhausted mid-date) comes back with *some* races synced but no new
  placings, and the walk mis-reads that as "genuinely no results"
  and strikes it — manufacturing the very clock the freeze is now
  holding back.
- **RC-2 (narrower — cross-source overwrite).** Runner rows are
  keyed by saddlecloth number (`N:<number>`). Where the live-capture
  (Betfair) path pre-populated a row under a number that the Racing
  API assigns to a *different* horse, a successful result-write
  lands the finishing position on the wrong horse. Latent today only
  because RC-1 starves the payload before the write is reached — fix
  RC-1 alone and this class of corruption goes live.

The placings clock is currently STOPPED (`BACKLOG_FREEZE_RETIRE =
True`, landed S197). This fix is what lets the freeze come off
safely.

## §3 — Pre-reads

Required, in order:
1. `placings_landing_diagnosis_report.md` — the RC-1/RC-2 root cause
   and the §6 proposed fix this brief implements. Primary source.
2. This brief.

Reference-only (read on demand):
- `placings_landing_diagnosis_brief.md` — the diagnosis contract and
  the Phase-0 no-touch list.
- `placings_trickle_fix_report.md` — the trickle fix + F1 history.

## §4 — System access

- **Host:** racing-data-capture VPS (`root@187.77.183.9`), live.
- **Mode:** READ-WRITE, restricted to the named anchors in §6–§7.
- **Database:** `capture.db` at
  `/home/racing/racing-data-capture/data/capture.db`. Queried live
  for verification (§9), `mode=ro` for reads; the sync code itself
  writes through its normal connection. Never copy the DB file.
- **Working tree is DIRTY** — see §10 hard limits. Edit only the
  named anchors; no git operations of any kind.
- **Timestamps:** Adelaide local (ACST/ACDT) for every time-of-day
  reference in the report (DR-021).

---

## §5 — Grounded anchors (where each bug lives)

Confirmed against the live tree this session (S198). Line numbers
are anchors, not contracts — Code re-confirms by function name
before editing.

**`subscription/racing_api.py`** (clean tree):
- `sync_day()` (≈L172) — fetches `/australia/meets?date=` then,
  per meet, `/australia/meets/{meet_id}/races`. No pacing or budget
  awareness; a mid-date quota stop leaves `races_synced > 0` with
  the tail unfetched.
- `_sync_single_runner()` (≈L305) — computes
  `rkey = compute_runner_key(runner_number, name_norm)` and writes
  through it. **RC-2 lands here.**

**`storage/database.py`** (DIRTY tree):
- `compute_runner_key()` (≈L241) — returns `"N:<number>"` when a
  saddlecloth number is present, else `"S:<name>"`. The number-key
  is the RC-2 root.
- `upsert_runner()` (≈L385) — `ON CONFLICT(race_id, runner_key)`
  with COALESCE; this is where a wrong-keyed write overwrites an
  existing row.
- `update_runner_result()` (≈L455) — writes `finish_position`
  (COALESCE) by `runner_id`; the corrupting write if the id was
  resolved from the wrong key.
- Schema: `runners` has `UNIQUE(race_id, runner_key)` and
  `runner_key TEXT NOT NULL` — the fix works *within* this
  constraint (no migration).

**`scripts/backfill_race_metadata.py`** (DIRTY tree):
- `run_backlog_pass()` (≈L190) — the oldest-first walk; classifies
  each date as progress / resultless / wall. **RC-1 lands here.**
- The resultless branch (≈L266) strikes on `error is None and
  races_synced > 0 and gained == 0` — cannot tell a mid-date quota
  stop from a genuinely empty result.
- `BACKLOG_FREEZE_RETIRE` (≈L109) — the Phase-0 freeze; flips to
  `False` as the *last* step, after the fix proves out.

---

## §6 — Fix A (write-side guard) — LANDS FIRST

**Goal:** a result-write can never land a finishing position on a
runner row whose horse identity differs from the API runner being
synced. Match on **horse identity (name)**, not saddlecloth number.

**Anchors:** `_sync_single_runner()` in `subscription/racing_api.py`;
a new identity-lookup helper in `storage/database.py`. No schema
change; works within `UNIQUE(race_id, runner_key)`.

**The rule (decision table).** Before the result-write, reconcile
the API runner against rows already in that race:

| Existing row state | Action |
|---|---|
| No row in the race matches this horse by name | Upsert under `N:<number>` as today (new runner). |
| A row matches by name **and** sits under the same key | Same horse — write as today (common case). |
| A row matches this horse by name but under a **different** key | Target **that** row — write the result to its id. Do **not** create/overwrite a `N:<number>` row. |
| A row occupies `N:<number>` but is a **different** horse (name mismatch) | Do **not** COALESCE-overwrite it. Write the API horse under its name key (`S:<name>`) instead, OR skip-with-finding if that key also collides. Never overwrite a differently-named incumbent. |

**Name match must be drift-robust (F-c).** The existing
`normalise_runner_name()` only does `.strip().lower()`. The
identity match must additionally strip punctuation and collapse
internal whitespace (e.g. `O'Reilly's Lad` ≡ `oreillys lad`) so
cross-source spelling/punctuation drift doesn't false-miss. Add this
as a dedicated robust-compare helper used **only** for the
reconcile; do **not** change the stored `runner_key` derivation
(that would be a schema-affecting key migration — out of scope).

**Why first:** RC-2 is latent only because RC-1 starves the
payload. Part B (below) deliberately feeds that payload through. If
the guard isn't in place before the payload flows, the recovery run
corrupts cross-sourced rows. Guard first, always.

---

## §7 — Fix B (fetch-side) — LANDS SECOND

**Goal:** the recoverable tail actually receives a budgeted, fully
fetched payload, and genuine-residue / quota-truncated dates stop
both starving that budget and manufacturing false strikes.

**Anchors:** `run_backlog_pass()` and (lightly) the `sync_day()`
return contract. No schema change.

**B1 — classify empty/partial fetches as transient (no strike).**
Today the walk strikes a date on `error is None and races_synced >
0 and gained == 0`, which cannot tell a quota-truncated or
positionless fetch from a genuinely resultless one. Fix:

- Extend `sync_day()`'s return dict with two additive signals: a
  `truncated` flag (set true if any per-meet fetch raised /
  quota-stopped, so the date was not fully fetched) and a
  `positions_seen` count (how many runners carried a finishing
  position this pass).
- In the walk, strike a date as **resultless only** when the fetch
  completed cleanly (`truncated == False`) **and** `positions_seen
  == 0`. If `truncated == True`, classify **wall/transient** (no
  strike) — the same recoverable bucket as an error.

**B2 — end the starvation; reach the tail.** The oldest-first walk
must not let the frozen early-March residue monopolise the per-night
attempt budget (`BACKLOG_MAX_ATTEMPTS`). Minimal mechanism: a date
that is currently struck-and-held-by-the-freeze gets at most **one**
probe per night, after which the walk continues to fresher
recoverable dates rather than spending consecutive attempts on
residue. Code may implement this as a reorder (frozen-struck dates
to the back) or a per-night single-probe cap — whichever is
cleaner; name the choice in the report.

**Outcome contract (must hold):** on a normal night, the first fresh
recoverable date in the tail (2026-03-15 onward) receives a
budgeted, untruncated fetch and its positions land.

**Last step — lift the freeze.** Once Parts A and B verify clean
(§9), flip `BACKLOG_FREEZE_RETIRE` to `False` (≈L109,
`backfill_race_metadata.py`). Struck dates self-clear on their first
real fill. This is the final edit, not the first.

---

## §8 — Sequencing within the session

1. **Baseline the dirty tree.** `git status --short` and `git diff`
   on `storage/database.py` and `scripts/backfill_race_metadata.py`.
   Record the pre-existing modified regions so intended edits are
   distinguishable from in-flight work. (`racing_api.py` is clean.)
2. **Part A — the write-side guard (§6).** Implement, then verify
   the redirect behaviour locally before any backlog fetch runs.
3. **Part B — the fetch fix (§7, B1 then B2).** Implement.
4. **Empirical verification (§9).** Run against the named dates;
   capture before/after.
5. **Lift the freeze** (§7 last step) — only if 2–4 are clean.
6. **Report.**

If the guard does not verify clean, **stop before Part B** and
report — do not feed the payload through an unguarded write path.

## §9 — Empirical verification (capture before + after)

- **Recovery proof (RC-1).** Pick a known recoverable tail date
  (e.g. a 2026-03-15-or-later Townsville / Swan Hill meet from the
  diagnosis). Before: count runners with `finish_position` on file.
  After one budgeted pass: positions land (`gained > 0`), and the
  date is **not** struck.
- **Corruption proof (RC-2).** Use the Dubbo case named in the
  diagnosis (≈6/8 runners differ across sources). Row-by-row by
  horse name, confirm each finishing position landed on the
  correctly-named horse and that **no** Betfair-path incumbent was
  overwritten under a colliding number.
- **No-false-strike proof (B1).** Confirm a truncated/positionless
  fetch is classified transient (no strike), and a cleanly-fetched
  genuinely-resultless date still strikes (held by the freeze).
- **Budget-reaches-tail proof (B2).** Confirm the per-night walk
  reaches and fetches the first fresh recoverable tail date rather
  than exhausting attempts on early-March residue.
- **Freeze discipline.** `BACKLOG_FREEZE_RETIRE` stays `True` through
  steps 2–4; flipped `False` only at step 5. Prefer
  empirically-determined dates (query the DB) over hard-coded ones.

---

## §10 — Output spec

- **Single file:** `placings_landing_fix_report.md` at the rebuild
  folder root.
- **Sections:** what changed (Part A, Part B, freeze), the verify
  results (§9 before/after tables), the mechanism choice for B2,
  any findings, dirty-tree confirmation (`git status` unchanged),
  self-assessment.
- **Length:** ~200–350 lines. Tables over prose for the verify
  results.
- **Does not contain:** a recovery run, recommendations beyond the
  named fix, scope into other backlog/cutover items, or any schema
  proposal.

## §11 — Hard limits (non-negotiable)

**Scope:**
- **No schema change / migration.** No new columns, no change to
  the stored `runner_key` derivation, no constraint changes.
- **No recovery run.** This brief lands + proves the fix and lifts
  the freeze on the named dates only. Replaying the full backlog is
  the *next* step, not this session.
- **Named anchors only** (§5–§7). No drift into adjacent code.
- **No touch** to v3, settlement, money path, or Betfair
  operational pricing. Capture-side analytical only (DR-033).

**Dirty-tree discipline (working tree is dirty):**
- **No git operations of any kind** — no `add`, `commit`, `stash`,
  `restore`, `checkout` (file-targeted), or `reset`.
- `storage/database.py` and `scripts/backfill_race_metadata.py` are
  **already modified** (Phase-0 freeze guard + other in-flight
  work). Those pre-existing regions are **not drift** — do not
  revert, tidy, or touch them. Edit only the fix anchors.
- After each edit, run `git diff <file>` to confirm only the
  intended lines were added.
- At session close, run `git status --short` and confirm the dirty
  file list is unchanged except for the intended fix edits to the
  three target files.

**Session shape:**
- Single bounded session. If the work doesn't fit, that's a
  finding, not a continuation.
- No mid-session operator escalation — surprises become findings.

---

## §12 — What happens after Code's session

The next operator-Claude (Chat) session reads
`placings_landing_fix_report.md` and triages: confirm the guard and
fetch fix verified clean, confirm the freeze is lifted, and — if all
clean — commission the **recovery run** (replay the recoverable
backlog), which is the operator's "start the data recovery"
milestone. Code does **not** write the recovery brief; that is the
next session's work.

If the report shows the guard did not verify clean (Part B not
reached), the next session re-scopes the guard before anything is
fed through the write path.

## §13 — Cross-references

- `placings_landing_diagnosis_report.md` §6 — the proposed fix this
  brief implements (RC-1/RC-2, the sequencing, the freeze-flip).
- `placings_landing_diagnosis_brief.md` — Phase-0 contract; the
  freeze landed S197.
- **DR-033** (data-source roles) — placings analytical, settlement
  Betfair-only: the reason this whole fix is bet-safe by
  construction.
- **DR-027 / DR-028** (two-database boundary) — capture.db is the
  analytical store; this fix stays entirely capture-side.
- **Finding F-c** (diagnosis) — live `venue_normalised` / name
  drift; the reason §6's identity match must be punctuation- and
  whitespace-robust.
- **DR-021** — Adelaide local timestamps in the report.

*End of brief.*
