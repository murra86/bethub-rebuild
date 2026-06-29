# Session 36 — Code report read + Fix 3 brief drafted

**Open:** 2026-04-30 15:56 ACST
**Close:** 2026-04-30 16:17 ACST
**Duration:** ~21 min
**Shape:** read-and-decide → diagnostic pivot → brief-drafting

## Required reads completed

- `work_in_progress.md` (project state through Session 35 close)
- `sessions/SESSION_35.md` (full Session 35 outcomes — fixes 1+2 brief locked at "go with your recommendations")
- `dr029/2_1_race_data/surgical_fix_1_2_report.md` (Code's execution report — full read)
- `dr029/2_1_race_data/surgical_fix_1_2_brief.md` (read-against-the-brief discipline)
- `dr029/2_1_race_data/source_review_report.md` (re-read in full mid-session for §5.3 anchors during Fix 3 brief drafting)
- Pre-flight directory listing of rebuild folder root — clean (seven canonical .md at root, dr029/2_1_race_data/ holds seven artefacts including the new surgical_fix_1_2_report.md)

## Headline read of Code's report

**Fixes 1 and 2 executed cleanly as instructed but the headline goal didn't move.** The reworked `racing-metadata-backfill.service` ran end-to-end against `get_unsynced_dates()` and processed all 60 unsynced dates `status=0/SUCCESS` in 26 seconds. Fix 1's separate `backfill_subscription.py` run was elided as redundant (same `sync_day` code path exercised by Fix 2's smoke-test) — a clean reasoned deviation from the brief's §7 step 6.

But the cross-tab `with_both` (`finish_position` AND `betfair_selection_id`) **moved from 0 to 0**. Code traced the cause cleanly: `(race_date, venue_normalised, race_number)` upsert key collides between the live-capture path and the Racing API path because **`subscription/racing_api.py` doesn't run venue names through the sponsor/locality-prefix cleaner that `bookmakers/sportsbet.py:_clean_venue` does**. The Racing API path stores `southside cranbourne` while the Betfair-side stores `cranbourne`. Result: 1,266 NEW orphan Racing-API race rows + 9,151 NEW orphan runner rows, no race-key merges with existing live-capture rows.

Race-level merge stats post-fix:
```
has_subscription_sync | has_betfair_capture | count
0                     | 0                   | 17,377
0                     | 1                   |  8,327
1                     | 0                   |  1,266
1                     | 1                   |      0   ← zero merges
```

**The brief's §10 hard limit fired exactly as designed:** Code didn't try to chase the fix into venue-normalisation territory; surfaced the finding cleanly and stopped. Clean state to recover from, not a tangle.

## Routing call landed

**Option C** locked: Fix 3 (BSP write-back) next, Fix 4 (cadence) after, **Fix 5 (venue harmonisation + retroactive race-key merge) added** as a fourth surgical fix to close out the arc. Considered:

- **A** — venue-harmonisation first, BSP/cadence after. Strongest case operationally (closes the headline goal first), but: lift to `normalise_venue` ripples to all callers; retroactive merge needs fuzzy logic for the `warwick farm`-style edge cases where venues align but rows still don't merge; probably needs its own brief plus careful operator-Claude review. Bigger than today's fix was.
- **B** — accept partial resolution. Effectively "the join doesn't matter" — declined; every analytical strategy depends on it.
- **C** — keep momentum on the easier fixes (Fix 3, Fix 4 are independent of the venue thing), tackle the harder one last. Operator's call.

Operator initially asked for plain-language re-explanation of all options ("nothing technical"). Re-explained per Session 31 standing instruction; operator picked C. My initial response had drifted into too much technical density — corrected mid-session, held cleanly thereafter.

## Mid-session pivot — VPS dirty-tree diagnostic

Code's report flagged the VPS git working tree as dirty (eight modified files plus untracked `api/` subtree and `bookmakers/tabtouch.py`). Surfaced this back to operator as a finding worth grounding before drafting Fix 3 brief — operator confirmed "I don't think so" on whether the changes were theirs.

Diagnostic script written to `/tmp/vps_drift_diagnostic.sh` via `Desktop Commander:write_file` (Session 30 standing — temp-file route over interactive REPL paste; Session 34 standing — Mac-side filesystem operations route through Desktop Commander not bash sandbox). First run failed: bash sandbox has no `ssh` binary (expected per filesystem standing). Re-routed via Desktop Commander's `start_process` calling the script from the Mac shell where SSH key is configured. Second run clean — captured `git status`, last commit (2026-03-04), file-by-file `git diff --stat`, mtimes, full diffs of the three Fix-3-or-Fix-5-relevant dirty files (`capture/orchestrator.py`, `config/settings.py`, `matching/race_matcher.py`), untracked `api/` subtree inventory.

**Diagnostic outcome saved at `dr029/2_1_race_data/vps_drift_check.md` (109 lines).** Plain summary: dirty tree is operator's own forgotten in-flight work — TABtouch added as ninth scraper with full orchestrator wiring; FastAPI read-side service started; Sportsbet re-enabled with sponsor/locality-prefix venue cleaner (which is exactly the source-of-truth Fix 5 will lift); defensive `IntegrityError` handler; health-check expansion. Last commit 2026-03-04, mtime spread 2026-03-11 → 2026-04-09. Substantive real work, not noise, not concerning.

**Implication for Fix 3:** of Fix 3's four anchor files (`betfair/client.py`, `betfair/models.py`, `capture/orchestrator.py`, `storage/database.py`) only `capture/orchestrator.py` is dirty. The dirty regions (around lines 35, 84, 332-340, 370-378, 397-403, 748, 800-810) don't intersect Fix 3's edit target (`_take_betfair_snapshot` lines 502-517 + tuple build 537-565). Fix 3 brief carries explicit "honour the dirty tree" hard limits: read working-tree state, edit only named anchors, no `git add`/`commit`/`stash`/`restore`/`reset`, verify post-edit `git diff` grew without unexpected reshapes.

## Substantive deliverables

1. **`dr029/2_1_race_data/vps_drift_check.md`** — 109 lines. Diagnostic record of the dirty VPS git tree, characterisation, implications for Fix 3 / Fix 4 / Fix 5, recommendation for the surgical-fix arc.

2. **`dr029/2_1_race_data/surgical_fix_3_brief.md`** — 263 lines, 24,988 bytes, SHA256 prefix `306e6178`. Eleven numbered sections: what-this-is-and-isn't / why this fix is independent of Cluster 1's residual / pre-reads / VPS access (read-write, working-tree state load-bearing) / four named changes (a)-(d) / sequencing / empirical verification / output spec / orphan-column finding (informational) / hard limits including dirty-tree / what-happens-after.

3. **`work_in_progress.md` §16** — VPS in-flight work review parking-lot item, alongside Decodo / digest-review (§15). Not gating DR-029.

## Calls made in the Fix 3 brief

1. **Four changes in dependency order — (a) add `bsp_price` field → (b) fix pre-jump projection from `SP_TRADED` to `SP_AVAILABLE` → (d) extend writer INSERT and snapshot tuple → (c) post-suspension SP_TRADED fetch.** Doing them in this order means each lands cleanly without breaking anything; reversing would leave the post-suspension fetch trying to write to a non-existent dataclass field.

2. **Wait for natural 08:30 ACST service restart over manual restart.** Manual would be fine but costs in-flight tick state. Brief recommends the natural restart pickup; verification queries against `capture.db` post-restart confirm the fix lands. Code may deviate if mid-session verification matters more than tick continuity.

3. **BSP write-back can't be fully verified in-session.** SP projections (sp_near / sp_far) start populating immediately on next service tick — verifiable mid-session for any race in INTENSIVE phase. BSP only gets captured when a market actually transitions OPEN→SUSPENDED (real race jumping during session window). Carved out as a Session-37 verification step rather than blocking.

4. **Hard limits include explicit dirty-tree handling.** §10 spells out: no `git add`, no `git commit`, no `git stash`, no `git restore`, no `git checkout` (file-targeted), no `git reset`. After each edit run `git diff <file>` to confirm only intended changes were added; at session close run `git status` to confirm dirty file list unchanged.

5. **Three pre-reads** (this brief, drift check, source-review report §5.3) plus a one-page read of the surgical-fix-1+2 report's §1 + §5. Lean. Reference-only docs noted but not required.

6. **Independence from Cluster 1's residual stated explicitly in §2.** Fix 3's data lands on Betfair-side rows keyed correctly to themselves; the venue-merge problem doesn't touch this fix. When Fix 5 closes Cluster 1, the BSP / sp_near / sp_far data will already be sitting on the right rows. Nothing replays.

7. **Fix 5's source named explicitly in §11.** The dirty `bookmakers/sportsbet.py:_clean_venue` is what Fix 5 will lift to harmonise `matching/race_matcher.normalise_venue`. Operator's in-flight work becomes the foundation of the harmonisation fix — net positive, made visible.

## Operator review

Direction-on-finding question initially asked in technical density; operator pushed back ("explain in plain operational gambling language, please"). Re-framed per Session 31 standing instruction: two parallel stacks of races for the last 60 days, one with Betfair price history, one with finish positions, neither talking to the other; venue-name decoration causes the upsert to create new rows instead of merging. Three options re-explained without jargon. Operator picked **C**. My honest reflection: my initial response had drifted toward over-explanation of mechanism; the standing instruction caught it.

Dirty-tree handling: operator confirmed "I don't think so" on ownership; diagnostic surfaced the answer (yes, it IS theirs, just forgotten); plain summary covered the changes operationally rather than as a code listing. Operator approved adding the parking-lot item to WIP §16 and approved proceeding with brief drafting.

Six-question equivalent review on the brief itself: not run because operator said "please provide me with the prompt and close" after seeing the brief was ready. Implicit acceptance of the Session 35 precedent ("go with your recommendations") for surgical-fix briefs.

## Standing instructions held

- **Plain-language operational/gambling-framed framing (Session 31, extended Session 34 to session-shape work).** Drift surfaced once mid-session — operator pushback "nothing technical, I don't get it" — corrected and held cleanly thereafter. Session 36 outcome: standing instruction continues to be load-bearing; operator-side correction is reliable when it surfaces; my discipline at the framing layer remains the watch-item.
- **Operational/analytical line discipline drift watch (Session 32).** No drift surfaced this session — Fix 3 brief stays entirely VPS-side analytical line, BSP capture is for analytical reads, no operational-line surface invoked.
- **Filesystem discipline (Session 34 lesson).** Used Desktop Commander's `write_file` for both the drift-check doc and the Fix 3 brief; verified post-write via `wc -l` + `wc -c` + `shasum`. Bash sandbox correctly identified as unable to reach VPS (no `ssh`); pivoted to Desktop Commander `start_process` calling Mac shell. Two namespace lessons re-confirmed: bash sandbox `/tmp` ≠ Mac `/tmp`; bash sandbox has no SSH binary.
- **REPL discipline (Session 30).** Used `Desktop Commander:write_file` for the diagnostic shell script (75 lines), invoked via `start_process(bash /tmp/...)` — temp-file route held throughout.
- **Pre-flight directory listing (Session 14 standing).** Held at orientation completion. Re-confirmed pre close-out.
- **DR-027 / DR-028 / DR-029 named in orientation summary.** Held.
- **Open-and-close-out economy directive (Session 21).** This session: closing summary omitted in chat per directive (Session 37 opening prompt produced); standing instructions live in WIP not in opening prompts; opening prompt drafted as a pointer not a summary.

## Tool routing

Session 36 = Claude Chat (delivered).
Out-of-session post-36 = Claude Code, Fix 3 BSP write-back execution against the brief.
Session 37 = Claude Chat, read of `surgical_fix_3_report.md` and decision on Fix 4 cadence brief drafting (plus pre-flight verification of the 23:30 ACST nightly metadata-backfill run from tonight).

## Eleventh consecutive non-early-close session

Sessions 26-36 inclusive. Each scope-completed-as-load-bearing — Session 36's load-bearing work was the read-and-decide on the Code report PLUS the dirty-tree diagnostic pivot PLUS the Fix 3 brief drafting. The pivot was not anticipated in the opening prompt; surfaced as a finding mid-orientation, handled cleanly. Total ~21 min.

## Close-out

Three new files written via Desktop Commander, all verified post-write. WIP §16 added via `Desktop Commander:edit_block` find/replace (single-block replacement at the §15 anchor). Session 36 log written. SESSION_36_OPENING_PROMPT.md to be moved to `.close_out_backups/` per established convention. Pre-close-out checklist held: pre-flight directory listing run; both Code-output files (the surgical-fix-1+2 report, plus the brief Code executed against) read against the brief; Fix 3 brief drafted; WIP updated; close-out timestamp anchored on actual clock per DR-021.

No silent failures. Session 34 lesson on `create_file` vs `write_file` held — `write_file` used exclusively for the rebuild folder.
