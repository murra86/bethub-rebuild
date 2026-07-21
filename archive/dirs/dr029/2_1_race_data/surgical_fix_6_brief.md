# DR-029 §2.1 — surgical Code session 6 brief (Fix 6: venue-harmonisation broadening + alias-table extension + consolidated dry-run merge)

**Brief authored:** 2026-05-01 (Session 47, operator-Claude, Adelaide).
**Audience:** Claude Code, single bounded session.
**Brief executes against:** `racing-data-capture` source tree on VPS `root@187.77.183.9`, source root `/home/racing/racing-data-capture/`. Live `capture.db` at `/home/racing/racing-data-capture/data/capture.db`.

---

## 1. What this brief is and is not

Surgical-fix brief for DR-029 §2.1 surgical fix 6. Code:

- (§6A) Broadens `matching/race_matcher.normalise_venue`'s prefix and suffix patterns to harmonise venue classes that Fix 5's strict lift didn't reach.
- (§6B) Extends `BETFAIR_VENUE_ALIASES` for renamed-venue cases the regex cannot resolve. Targets are determined empirically, not from this brief.
- (§6C) Produces a **consolidated** dry-run retroactive merge plan covering both Fix 5's clean merges AND Fix 6's clean merges, replacing `fix_5c_proposed_merge.json` as the single contract for the future merge-execution session.

**Single bounded Code session.** Surprises become findings in the report, not blockers. Remediation routes to operator-Claude triage, not Code's report. Code does not execute the merges. Code does not edit `bookmakers/sportsbet.py`.

---

## 2. Why this work exists

Fix 5 (Session 46 brief, executed 2026-05-01) lifted sponsor-with-hyphen and locality-prefix logic from `bookmakers/sportsbet.py:_clean_venue` into `matching/race_matcher.normalise_venue`. The lift produced 186 clean retroactive merges out of 1,339 normal-race orphans (13.9%) — a real but partial fix. Code's report (`surgical_fix_5_report.md` §6, §7e) named the limitations: the existing `_clean_venue` regex requires a hyphen for sponsor stripping (catches `sportsbet-ballarat`, misses `ladbrokes geelong`), and only handles named cardinal localities (catches `southside cranbourne`, misses `royal randwick` and `aquis park gold coast`). Suffix near-misses were also surfaced — `morphettville parks`, `rosehill gardens` — and the `ladbrokes pioneer` / `ladbrokes cannon` class where the LC-side venue is renamed entirely.

Pre-flight grounding for this brief (Session 47, operator-Claude, 2026-05-01) cross-tabulated Fix 5's no-match classes against live `capture.db` LC-side counterpart inventory. Findings:

- Sponsor-without-hyphen broadening: unlocks 255 of 526 unstripped-naming records (48.5%).
- Sponsor-park broadening: unlocks 103 of 104 (99.0%).
- Suffix near-misses (` gardens`, ` parks`): unlock 68 of 501 no_lc_counterpart records (13.6%).
- Total estimated unlock: ~426 additional clean merges. Combined with Fix 5's 186 → ~612 clean merges out of 1,339 normal-race orphans (45.7%).

The remaining ~727 normal-race orphans split into (a) renamed-venue classes addressable via §6B alias-table extension (e.g. `ladbrokes pioneer` → unknown LC target, must be probed), (b) deeper no_lc_counterpart cases where the live-capture path didn't capture the race at all (out of scope), and (c) structurally unmergeable cases (no Betfair market existed).

Fix 6 closes the venue-harmonisation arc to its empirically achievable ceiling. Beyond Fix 6, further unlock requires deeper data investigation outside §2.1's surgical-fix scope, or acceptance that some orphan classes are structurally unmergeable.

---

## 3. Pre-reads

Required:

- `dr029/2_1_race_data/surgical_fix_5_report.md` — the immediate predecessor's findings, especially §3 (B1/B2/B3 baselines), §6 (§5C results), §7 (anomalies surfaced).
- `dr029/2_1_race_data/fix_5c_proposed_merge.json` — Fix 5's dry-run plan, superseded by Fix 6's output but read for schema reference and for Fix 5's 186 clean-merge records (which Fix 6 includes in its consolidated output).
- `dr029/2_1_race_data/surgical_fix_5_brief.md` — Fix 5's brief, for cross-reference if scope questions arise about what Fix 5 deliberately excluded.

Reference-only (read on demand):

- `dr029/2_1_race_data/source_review_report.md` — race-key match logic anchor.
- `dr029/2_1_race_data/vps_drift_check.md` — dirty-tree state at Session 36; current state has drifted (+3 files since), see §10 below.
- `dr029/dr029_scope.md` §2.1 — scope item this brief serves.

---

## 4. System access

- **VPS source tree:** `root@187.77.183.9` via SSH. Source root `/home/racing/racing-data-capture/`. Read-write on the named anchor only (`matching/race_matcher.py`).
- **Live `capture.db`:** at `/home/racing/racing-data-capture/data/capture.db`. **Read-only** for §6A's measurement queries and §6B's empirical alias probing. **Read-only** throughout §6C's dry-run merge plan generation. No DB writes.
- **No production restart.** No service restart. Function changes are uncommitted; effective at next natural process restart, not this session's concern.
- **Adelaide local timestamps per DR-021** for every time-of-day reference in the report.

---

## 5. §6A — Regex broadening of `normalise_venue`

### 5.1 Anchors

- File: `matching/race_matcher.py`.
- Function: `normalise_venue` (current body at approximately lines 63-95 post-Fix-5 lift).

### 5.2 Edits

Extend `normalise_venue` to apply the following stages **in order**, after the existing Fix 5 sponsor-with-hyphen and locality-prefix strips, and before the existing `name.strip().lower()` step:

**Stage 1 — sponsor-park strip (most specific, runs first).** Strip the pattern `^(aquis|bet365|picklebet|sportsbet|ladbrokes)\s+park\s+` (case-insensitive). Examples: `aquis park gold coast` → `gold coast`, `bet365 park kyneton` → `kyneton`, `bet365 park kilmore` → `kilmore`. Specificity matters — this stage runs before Stage 2 because Stage 2 would otherwise strip just `bet365` and leave `park kyneton` standing.

**Stage 2 — sponsor-without-hyphen strip.** Strip the pattern `^(sportsbet|ladbrokes|bet365|neds|picklebet|tab|tabtouch|unibet|palmerbet|betdeluxe|betr|aquis|royal|thomas\s+farms\s+rc)\s+` (case-insensitive). Examples: `ladbrokes geelong` → `geelong`, `royal randwick` → `randwick`, `thomas farms rc murray bridge` → `murray bridge`, `bet365 echuca` → `echuca`. Note `thomas\s+farms\s+rc` includes the multi-word case.

**Stage 3 — suffix near-miss strip.** After parens-strip and after the existing suffix-strip loop, add stripping for ` gardens`, ` parks` (with trailing s — distinct from existing ` park`). Examples: `rosehill gardens` → `rosehill`, `morphettville parks` → `morphettville`. Other suffixes (` heath`, ` inner track`, etc.) are NOT in scope for Fix 6 — their LC-side counterparts were not empirically validated as existing in pre-flight; Code does not speculatively add them.

### 5.3 Stages held distinct

The three stages run in order; do not collapse them into a single mega-regex. Keeping them distinct preserves debuggability and matches how `_clean_venue`'s lift already organised by category. Each stage carries an inline comment naming its target class.

### 5.4 Hard limit on Stage 2 vocabulary

The Stage 2 sponsor list is the empirically validated set from Session 47 pre-flight (Fix 5 report §6 top-venues + LC-side counterpart confirmation). Code does NOT add other sponsor names speculatively — `topsport`, `winners`, etc. — even if they appear in `bookmakers/sportsbet.py:_clean_venue`. The list is empirically anchored, not transcribed.

### 5.5 Functional verification

Use a `/tmp/verify_normalise_venue_fix6.py` snippet that imports the post-edit `normalise_venue` and runs it against the empirical sample list below. Confirm each input produces the named output. The snippet stays in `/tmp/`; no `tests/` directory edit (per DR-029 named-debt boundary).

Sample list (input → expected output):

```
ladbrokes geelong              -> geelong
royal randwick                 -> randwick
thomas farms rc murray bridge  -> murray bridge
sportsbet mount isa            -> mount isa
bet365 echuca                  -> echuca
bet365 terang                  -> terang
sportsbet oakbank              -> oakbank
bet365 swan hill               -> swan hill
sportsbet longreach            -> longreach
aquis park gold coast          -> gold coast
bet365 park kyneton            -> kyneton
bet365 park kilmore            -> kilmore
rosehill gardens               -> rosehill
morphettville parks            -> morphettville
sportsbet sandown lakeside     -> sandown lakeside
  (Stage 2 strips sponsor; ` lakeside` is NOT in suffix scope)
southside cranbourne           -> cranbourne
  (Fix 5 lift still works post-Fix-6)
sportsbet-ballarat             -> ballarat
  (Fix 5 lift still works post-Fix-6)
warwick farm                   -> warwick farm
  (already canonical, unchanged)
flemington                     -> flemington
  (already canonical, unchanged)
```

If any input doesn't produce the expected output, that's a finding (regex composition issue) — Code surfaces in §7 of the report rather than chasing.

---

## 6. §6B — `BETFAIR_VENUE_ALIASES` extension

### 6.1 Why the alias table needs extending

Pre-flight surfaced two record classes the Stage 2 regex strips correctly but where the **stripped name still doesn't match any LC counterpart**:

- `ladbrokes pioneer` (53 records) → strips to `pioneer` → LC has 0 rows for `pioneer`.
- `ladbrokes cannon` (44 records) → strips to `cannon` → LC has 0 rows for `cannon`.

These are renamed venues — the Racing API name is `Pioneer` (or `Pioneer Park`) but the LC-side captures the venue under a different name entirely. Common pattern: the venue is known by city/region rather than track name on bookmaker feeds. Example hypothesis: `Pioneer Park` is in Rockhampton, so LC may carry `rockhampton`. `Cannon Park` is in Townsville, so LC may carry `townsville`.

These cannot be solved by regex broadening; they require explicit alias entries.

### 6.2 Empirical probe to determine actual alias targets

Before adding any alias entry, Code probes `capture.db` to determine what the LC-side venue name actually is for the relevant dates and race numbers. Methodology:

1. Pull the RA-side orphan records for `ladbrokes pioneer` and `ladbrokes cannon` (date, race_number, scheduled_start).
2. For each record, query LC-side races with `betfair_win_market_id IS NOT NULL AND has_subscription_sync = 0` filtered to the same date and race_number, and check `scheduled_start` proximity (within 5 minutes UTC).
3. Tally the LC-side `venue_normalised` values that match. If a single LC venue dominates (e.g. ≥80% of matches), that's the alias target.
4. If multiple LC venues split the matches without a clear dominant target, that's a finding — surface in §7 and do NOT add an alias for that class. Better to leave records orphaned than mis-merge.

### 6.3 Alias additions (subject to §6.2 confirmation)

If §6.2 produces a clear dominant target, add to `BETFAIR_VENUE_ALIASES`:

```python
'pioneer': '<empirically_determined>',  # was Ladbrokes Pioneer Park, RQ
'cannon': '<empirically_determined>',  # was Ladbrokes Cannon Park, NQ
```

The alias mapping fires AFTER the Stage 1/2/3 regex strips, so the input `ladbrokes pioneer` becomes `pioneer` via Stage 2, then resolves to the empirically-determined target via the alias table.

### 6.4 No speculative alias additions

Code adds aliases ONLY for the two classes named in §6.1 and ONLY if §6.2's empirical probe produces a clear dominant target. No other alias additions. If pre-flight probing surfaces additional renamed-venue classes (e.g. `ladbrokes wodonga` carries 16 records but wasn't pre-validated), Code surfaces in §7 as a finding for operator-Claude follow-up — not a Fix 6 in-session addition.

### 6.5 Functional verification

Extend the §5.5 verification snippet with the alias targets:

```
ladbrokes pioneer  -> <empirically_determined target>
ladbrokes cannon   -> <empirically_determined target>
```

If §6.2 produced no clear target for one or both, those entries are absent from the snippet and §7 surfaces the finding.

---

## 7. §6C — Consolidated dry-run merge plan

### 7.1 Scope

Re-run the entire retroactive match against the post-Fix-6 `normalise_venue` and produce `dr029/2_1_race_data/fix_6c_proposed_merge.json`. This file **supersedes** `fix_5c_proposed_merge.json` — the merge-execution brief reads only `fix_6c_proposed_merge.json` as the contract.

The previous file `fix_5c_proposed_merge.json` is NOT deleted, modified, or moved by Code. It stays in place as a historical reference. Operator-Claude handles any future cleanup.

### 7.2 Methodology

Same as Fix 5's §5C, with three changes:

1. The harmonised normaliser is the post-Fix-6 function (regex stages 1/2/3 + alias-table extension).
2. The day-shift broadening rule from Fix 5 carries forward unchanged — applied only to `{sunshine coast, orange, ballina, rockhampton}` per Fix 5 §5B confirmation.
3. The `is_trial=1` and `is_jump_out=1` short-circuit from Fix 5C carries forward unchanged — these orphans get the deterministic "no_match — Betfair does not market trials/jump-outs" reason.

### 7.3 Output schema

Same record schema as `fix_5c_proposed_merge.json`. Per-record fields:

- `orphan_race_id`, `race_date`, `venue_raw`, `venue_stored_normalised`, `venue_harmonised`, `race_number`, `scheduled_start`, `is_trial`, `is_jump_out`, `race_name`.
- `outcome`: `clean | ambiguous | no_match`.
- `target_race_id` (clean), `candidate_race_ids` (ambiguous), `reason` (no_match).
- `match_method` (clean): `exact_key`, `day_shift_broadened`, or `alias_resolved` (new — for the §6B alias-table cases).
- `target_race_date` (day-shift clean): the LC-side row's actual `race_date` for the merge.

Generation metadata block at file top:

- `generated_at_acst` — Adelaide local ACST/ACDT timestamp.
- `fix_session` — `"DR-029 §2.1 surgical fix 6C — consolidated dry-run merge plan (supersedes 5C)"`.
- `method` block describing the three regex stages, alias table additions, day-shift rule.
- `totals` block with breakdown: `orphan_races_inspected`, `clean`, `ambiguous`, `no_match_trial`, `no_match_jump_out`, `no_match_unstripped_naming` (residual), `no_match_no_lc_counterpart` (residual), `no_match_other`.

### 7.4 Expected counts (anticipation, not contract)

Pre-flight estimates suggest:

- `clean` ≈ 612 (Fix 5's 186 + Fix 6's ~426 — pre-flight estimate, not exact).
- `no_match_trial` ≈ 1,076 (unchanged).
- `no_match_jump_out` ≈ 834 (unchanged).
- `no_match_unstripped_naming` ≈ 271 residual (sponsor-no-hyphen records where Stage 2 strips correctly but LC has no counterpart — e.g. `sandown lakeside` after `sportsbet` strip).
- `no_match_no_lc_counterpart` ≈ 433 residual (501 minus the 68 unlocked by suffix broadening).
- `no_match_other` ≈ small residual.
- `ambiguous` ≈ 0 expected (Fix 5C had 0; the broader regex doesn't add ambiguity).

Code reports actuals; if actuals diverge from expected by more than 20% in either direction on any class, surface in §7 of the report as a finding.

---

## 8. Sequencing within session

§6A → §6B → §6C, in that order. Reasoning:

- §6A landing first means §6B's empirical probe has the post-Fix-6 normaliser available for testing.
- §6B before §6C means §6C's consolidated plan reflects both the regex broadening AND the alias-table extension.
- §6C runs last because its retroactive match depends on both prior stages being in place.

If §6B's empirical probe produces no clear alias target for either class, §6C still runs — those records simply remain in the `no_match` class with the reason `no_lc_counterpart` (rather than `alias_resolved`).

---

## 9. Empirical verification

### 9.1 Pre-edit baseline (B1 / B2 / B3 cross-tabs)

Re-capture from the live DB before any edit. Confirm:

- B1: race-level cross-tab of (`has_subscription_sync`, `has_betfair_win_market_id` IS NOT NULL) — the 4-cell breakdown.
- B2: runners with both `finish_position` AND `betfair_selection_id`.
- B3: top-20 RA-only orphan venues by volume.

These are EXPECTED to be substantially the same as Fix 5's §3 (Code re-runs to confirm baseline hasn't shifted in the ~1 hour between Fix 5 and Fix 6 sessions; if it has, surface in §7 as anomaly).

### 9.2 Post-edit verification

Per §5.5 (regex sample) and §6.5 (alias sample). The cross-tab queries B1/B2/B3 are NOT expected to move post-edit — the edit changes the function, not stored values. Same expectation as Fix 5's §7 footnote.

### 9.3 Dirty-tree post-edit check

`git status --short` post-edit confirms only `matching/race_matcher.py` has new diff content (the existing 11-modified, 7-untracked list otherwise unchanged). `git diff --stat matching/race_matcher.py` confirms diff growth limited to the named anchors.

---

## 10. Hard limits

Non-negotiable. Code holds the line on all of these.

1. **Single bounded session.** Estimated 60-90 minutes. If work doesn't fit, that's a finding, not a continuation.
2. **Named anchors only.** Code edits ONLY `matching/race_matcher.py:normalise_venue` (regex stages) and `matching/race_matcher.py:BETFAIR_VENUE_ALIASES` (alias additions, subject to §6B empirical confirmation).
3. **No schema changes.**
4. **No DB writes.** All queries use read-only URI (`file:...?mode=ro`).
5. **No `git add` / `git commit` / `git stash` / `git restore` / `git checkout` (file-targeted) / `git reset`.**
6. **No DR-029 named-debt remediation.** No tests added (verification snippet stays in `/tmp/`). No migration framework. No orchestrator refactor.
7. **No mid-session escalation.** Code surfaces all surprises in §7 of the report; does not ping operator-Claude mid-flight.
8. **No edits to `bookmakers/sportsbet.py`.** Fix 5's boundary holds — sportsbet's `_clean_venue` consolidation is later operator-Claude work.
9. **No merge execution.** Fix 6 produces the dry-run plan only.
10. **No speculative regex broadening.** Stages 1/2/3 vocabulary is the empirically validated set from Session 47 pre-flight. Code does not add other sponsors, suffixes, or patterns mid-session.
11. **No speculative alias additions.** Only the two §6B classes, only if §6.2's probe produces a clear dominant target.
12. **No deletion of `fix_5c_proposed_merge.json`.** That file stays in place; `fix_6c_proposed_merge.json` is the new contract.

---

## 11. Dirty-tree handling

VPS working tree is dirty per Fix 5's report §7d. Current state (Session 47 pre-flight):

- 11 modified files: `betfair/client.py`, `betfair/models.py`, `bookmakers/base.py`, `bookmakers/pointsbet.py`, `bookmakers/sportsbet.py`, `capture/orchestrator.py`, `config/settings.py`, `matching/race_matcher.py`, `scripts/health_check.py`, `scripts/liveness_check.py`, `storage/database.py`.
- 7 untracked files: `api/__init__.py`, `api/db.py`, `api/routes/__init__.py`, `api/routes/health.py`, `api/routes/races.py`, `api/routes/snapshots.py`, `bookmakers/tabtouch.py`.

Of these, only `matching/race_matcher.py` is relevant to Fix 6. Its current diff carries Fix 5's +16/-1 plus a pre-existing tabtouch line. Fix 6's edits add to the existing diff; do not touch the tabtouch line; do not touch any other modified file.

Dirty-tree discipline:

- Read working-tree state at session start (`git status --short`).
- Edit only named anchors in `matching/race_matcher.py`.
- After each edit, `git diff matching/race_matcher.py` to confirm only intended changes added.
- At session close, `git status --short` to confirm dirty file list unchanged.
- No `git add`, `git commit`, `git stash`, `git restore`, `git checkout`, `git reset`.

---

## 12. Output spec

Single report at `dr029/2_1_race_data/surgical_fix_6_report.md`. Auxiliary file: `dr029/2_1_race_data/fix_6c_proposed_merge.json`.

### 12.1 Report sections

1. Headline (~2 paragraphs — what landed, what didn't, what's surprising).
2. What was done (per §6A / §6B / §6C, summary of edits and probe).
3. Pre-fix baseline (B1 / B2 / B3 re-capture + comment on whether shifted from Fix 5's snapshot).
4. §6A execution log — pre-edit dirty-tree, edit diff, post-edit dirty-tree, functional verification table.
5. §6B alias probe results — for each of `ladbrokes pioneer` and `ladbrokes cannon`, what LC-side venues matched and what target was added (or why no target was added).
6. §6C dry-run merge summary — totals, top-10 clean merges, top-10 newly-resolved (i.e. records that were no-match in Fix 5C and are now clean in Fix 6C), top-10 still-no-match.
7. Anything surprising — anomalies surfaced (especially if expected counts in §7.4 diverge by >20%, if §6B produced an unexpected pattern, if B1/B2/B3 baselines shifted from Fix 5's snapshot beyond what the overnight metadata-backfill explains).
8. Self-assessment — brief scope adherence, hard limits held, dirty-tree discipline, what moved, what did not move.

### 12.2 Length anticipation

300-400 lines. Slightly larger than Fix 5's 486 because §6A is shorter (single edit, three stages stated tersely) but §6B adds a probe-and-decide section.

### 12.3 What the report does not contain

- Recommendations for further fixes beyond what's empirically grounded.
- Speculation about whether/when to execute the merges (that's operator-Claude triage in the next session).
- Comparison against any baseline other than Fix 5's snapshot.
- Reproduction of `fix_6c_proposed_merge.json`'s record-level content (totals only; record detail lives in the JSON).

---

## 13. What happens after Code's session

Operator-Claude reads the report in the next session. Triage shape:

- §6A functional verification: did the regex broadening produce the named harmonisations cleanly?
- §6B alias probe: were the targets empirically clear, or did the probe surface ambiguity?
- §6C consolidated plan totals: how close to the ~612 expected? Any unexpected ambiguity?

Decisions the next session makes:

- Commission the merge-execution brief reading `fix_6c_proposed_merge.json` (default if §6C's clean count is healthy).
- Refine match logic if §6B surfaced ambiguity (a follow-up alias-probe brief).
- Pivot to the runner-level convergence finding (Fix 5 report §7b — `runners.with_both` still 0 despite race-level merges) before any merge execution.

The runner-level finding (Finding §7b in Fix 5) is **explicitly out of Fix 6's scope**. Fix 6 does not probe runner-key alignment, does not surface diagnostics for it, does not attempt to fix it. That's a separate brief, post-Fix-6.

---

## 14. Cross-references

- **Scope doc item:** `dr029/dr029_scope.md` §2.1 (race-data fit-for-purpose verification).
- **DRs invoked:** DR-029 (data-layer fit-for-purpose review before v3 build); DR-021 (timestamp anchoring, Adelaide local time); DR-027 (two-database architecture — capture.db is analytical-line, BetHub owns operational state); DR-028 (cross-database integration boundary discipline).
- **Prior report:** `dr029/2_1_race_data/surgical_fix_5_report.md` (especially §3, §6, §7e — the limitations Fix 6 addresses).
- **Prior brief:** `dr029/2_1_race_data/surgical_fix_5_brief.md` (for boundary cross-reference if scope questions arise).
- **Parking lot — explicitly excluded:** runner-key convergence (Fix 5 §7b finding), `bookmakers/sportsbet.py:_clean_venue` consolidation, additional sponsor regex vocabulary beyond the empirically validated set, additional suffix patterns beyond ` gardens` and ` parks`, additional alias targets beyond `pioneer` and `cannon`.

---

*End of brief.*
