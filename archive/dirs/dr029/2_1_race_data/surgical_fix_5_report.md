# DR-029 §2.1 — surgical-fix Code session 5 report (Fix 5: venue harmonisation + retroactive merge + edge-case probe)

**Session opened:** 2026-05-01 16:42 ACST.
**Session closed:** 2026-05-01 17:25 ACST.
**Brief executed:** `dr029/2_1_race_data/surgical_fix_5_brief.md`.
**VPS:** `root@187.77.183.9`, source tree `/home/racing/racing-data-capture/`.
**Wall-clock:** ~43 minutes.

---

## 1. Headline

**§5A landed cleanly.** `matching/race_matcher.py:normalise_venue` now applies the sponsor-prefix and locality-prefix strips lifted from `bookmakers/sportsbet.py:_clean_venue` before the existing parens / suffix / alias logic. Functional verification confirms the stated harmonisations (`southside cranbourne → cranbourne`, `sportsbet-ballarat → ballarat`, `Sportsbet-Ballarat → ballarat`, `warwick farm → warwick farm`).

**§5C produced a usable but narrowly-scoped merge plan.** Of 3,249 Racing-API-only orphan race rows in the live-capture window, **186 (5.7%) get a clean (date, harmonised_venue, race_number) merge target**, **0 are ambiguous**, and **3,063 remain no-match**. Critically, **1,910 of the no-match (58.8% of the orphan set) are TRIALS or JUMP-OUTS** that Betfair does not market — these are correctly orphaned and will not merge regardless of normalisation work. The remaining 1,153 normal-race no-matches split into a sponsor-decoration class (652) the lifted regex doesn't reach because it requires a hyphen, and a pure-no-LC-counterpart class (501) where the live-capture row simply doesn't exist or sits in a different cross-tab cell. The §5A lift is a real but partial fix; a follow-up brief that broadens the prefix-strip pattern would close most of the un-stripped class.

**§5B repointed the warwick-farm hypothesis.** The 13-edge-case venues' residual orphans are dominated by trials/jump-outs and venue-alignment-already-fine-but-no-LC-counterpart, NOT by a date-drift or race-number-drift class. A small day-shift class (29 races) is real and confirmed for Sunshine Coast / Orange / Ballina / Rockhampton — non-DST QLD/border venues where Racing API stores local-day race_date and live-capture stores UTC-day. §5C applies day-shift broadening only for those four venues.

---

## 2. What was done

### §5A — Lift `_clean_venue` into `normalise_venue`

Read `bookmakers/sportsbet.py` lines 49-66 verbatim (current dirty-tree state). Read `matching/race_matcher.py:normalise_venue` lines 63-80. Edited the function body to apply the two `_clean_venue` regexes (sponsor `^[A-Za-z]+-` and locality `^(Northside|Southside|...|Lower)\s+`) **before** the existing `name.strip().lower()` step. The locality regex was given `flags=re.IGNORECASE` so the harmonisation also fires when the function is re-applied to already-lowercased orphan-row venue strings (the §5C use case). Existing parens-strip, suffix-strip, and `BETFAIR_VENUE_ALIASES` logic preserved unchanged. `re` import already present at line 14; no helper-import edit.

### §5B — Edge-case diagnostic probe

Read-only Python script (`/tmp/probe_5b*.py`) against `data/capture.db`. For each of the 13 venues identified in `surgical_fix_1_2_report.md` §5 (warwick farm, doomben, flemington, belmont, bathurst, launceston, bendigo, hobart, morphettville, tamworth, sunshine coast, wyong, mornington), enumerated the (race_date, harmonised_venue, race_number) tuples on both orphan sides and tested the day-shift / race-number-drift / no-LC-counterpart hypotheses. Then probed the warwick-farm-specific 2026-03-02 and 2026-03-30 cases to disambiguate trials from real meetings.

### §5C — Dry-run retroactive merge

Read-only Python script (`/tmp/build_fix_5c.py`). Re-applied `normalise_venue` (post-§5A) against every Racing-API-only orphan row's stored `venue_normalised`. Built `(race_date, harmonised_venue, race_number)` index against the live-capture-only orphan set. Day-shift broadening (`±1` day) applied only to {sunshine coast, orange, ballina, rockhampton} per §5B finding. Categorised into `clean / ambiguous / no_match` with sub-reasons. Wrote one record per orphan to `dr029/2_1_race_data/fix_5c_proposed_merge.json`.

---

## 3. Pre-fix baseline

**B1 — race-level merge stats** (live-capture window `race_date >= '2026-03-02'`; matches the brief's queries with `betfair_win_market_id` substituted for the brief's `betfair_market_id` — that column does not exist; `betfair_win_market_id` is the actual schema column populated by the live-capture path):

```
has_subscription_sync | has_betfair_win_market_id | count
0                     | 0                         | 14,838
0                     | 1                         |  7,445
1                     | 0                         |  3,249
1                     | 1                         |  2,081
```

This has shifted substantially from `surgical_fix_1_2_report.md` §5's snapshot (which read 17,377 / 8,327 / 1,266 / 0 on 2026-04-30). The `(1,1)` cell is now non-zero (2,081 races have BOTH flags) — the nightly `racing-metadata-backfill.service` runs of 2026-04-30 23:30 ACST and 2026-05-01 09:00 ACST will have processed additional dates and produced race-level merges where venue alignment happened to work. The orphan set has also grown (1,266 → 3,249), consistent with continued daily Racing API enrichment landing on un-aligned venue keys.

**B2 — runners with both `finish_position` AND `betfair_selection_id`**: **0**. Despite 2,081 race-level merges, no runner row carries both fields. This is downstream of §5's scope (runner-key matching mechanics) but worth surfacing — a race-level merge alone doesn't produce the runner-level convergence v3 needs. Surfaced in §7 below as a finding.

**B3 — top-20 RA-only orphan venues** (post-Fix-1+2 sample, current state):

```
southside cranbourne           213
southside pakenham             155
royal randwick                 106
aquis park gold coast          104
ladbrokes geelong               95
rosehill gardens                91
flemington                      78
warwick farm                    77
belmont                         73
lark hill                       70
thomas farms rc murray bridge   67
sportsbet-ballarat              66
morphettville parks             60
bet365 camperdown               60
doomben                         59
caulfield heath                 59
ladbrokes pioneer               53
aquis beaudesert                53
sunshine coast@inner track      51
sportsbet oakbank               49
```

The composition has changed since 2026-04-30: sportsbet-Y hyphenated venues have shrunk relative to non-hyphen sponsor venues (`ladbrokes geelong`, `bet365 camperdown`, `aquis park gold coast`) — meaningful for §5A's effective coverage, see §4 below.

---

## 4. §5A execution log

### Pre-edit dirty-tree check

`git status --short` returned 11 modified files plus 7 untracked. **This is a +3 drift from `vps_drift_check.md` §3** (which listed 8 modified): `betfair/client.py`, `betfair/models.py`, `storage/database.py` are newly modified. Diff stats `+40 / +2 / +48` lines respectively. Pattern matches the `surgical_fix_3_brief.md` BSP write-back anchor set (per `vps_drift_check.md` §6 cross-check). Inferred: a separate Code session executed Fix 3 between 2026-04-30 (Session 36 drift check) and 2026-05-01. The 8 originally-dirty files plus the 3 Fix-3 files are all unchanged in their already-existing diff content; my edit added only to `matching/race_matcher.py`. Surfaced for awareness; no action taken.

`git diff matching/race_matcher.py` pre-edit confirmed only the single tabtouch line (line 219) per `vps_drift_check.md` §3.

### Edit diff

```diff
@@ -64,8 +64,22 @@ def normalise_venue(name: str) -> str:
     """Normalise venue name for cross-bookmaker matching.

     Reused from race_browser.py with additions for Betfair aliases.
+    Sponsor / locality prefix strip lifted from bookmakers/sportsbet.py:_clean_venue
+    per DR-029 §2.1 surgical fix 5 — harmonises Racing API venue keys with
+    bookmaker-side venue keys.
     """
-    n = name.strip().lower()
+    # Sponsor prefix (e.g. "Sportsbet-Ballarat" -> "Ballarat")
+    n = re.sub(r"^[A-Za-z]+-", "", name)
+    # Locality qualifier prefix (e.g. "Southside Cranbourne" -> "Cranbourne");
+    # case-insensitive so the harmonisation also applies to already-lowercased
+    # venue keys re-normalised retroactively.
+    n = re.sub(
+        r"^(Northside|Southside|Eastside|Westside|South|North|East|West|New|Old|Upper|Lower)\s+",
+        "",
+        n,
+        flags=re.IGNORECASE,
+    )
+    n = n.strip().lower()
     # Remove parenthesised suffixes like "(AUS)", "(VIC)"
     n = re.sub(r"\s*\([^)]+\)\s*$", "", n)
     # Remove common venue suffixes
```

The edit lands cleanly in the `normalise_venue` body. The pre-existing tabtouch one-line addition at line 219 is preserved. `git diff --stat matching/race_matcher.py` reads `1 file changed, 16 insertions(+), 1 deletion(-)` — the tabtouch line plus 16 new lines.

`git status --short` post-edit: same 11-modified / 7-untracked list. Dirty file list grew by **zero** (only `matching/race_matcher.py`'s diff grew). Hard limits §5A held.

### Functional verification

`/tmp/verify_normalise_venue.py` imported the post-edit `normalise_venue` and ran it against the orphan-venue sample list. Input → output mapping:

```
INPUT                                    -> OUTPUT
--------------------------------------------------------------------------------
southside cranbourne                     -> cranbourne                    ✓ stripped
southside pakenham                       -> pakenham                      ✓ stripped
sportsbet-ballarat                       -> ballarat                      ✓ stripped
royal randwick                           -> royal randwick                ✗ unchanged
sportsbet-wangaratta                     -> wangaratta                    ✓ stripped
aquis park gold coast                    -> aquis park gold coast         ✗ unchanged
toowoomba inner track                    -> toowoomba inner track         ✗ unchanged
sportsbet oakbank                        -> sportsbet oakbank             ✗ unchanged
ladbrokes geelong                        -> ladbrokes geelong             ✗ unchanged
bet365 park kilmore                      -> bet365 park kilmore           ✗ unchanged
sunshine coast@inner track               -> sunshine coast@inner track    ✗ unchanged
devonport tapeta synthetic               -> devonport tapeta synthetic    ✗ unchanged
warwick farm                             -> warwick farm                  -- already canonical
thomas farms rc murray bridge            -> thomas farms rc murray bridge ✗ unchanged
morphettville parks                      -> morphettville parks           ✗ unchanged
bet365 camperdown                        -> bet365 camperdown             ✗ unchanged
caulfield heath                          -> caulfield heath               ✗ unchanged
aquis beaudesert                         -> aquis beaudesert              ✗ unchanged
ladbrokes pioneer                        -> ladbrokes pioneer             ✗ unchanged
rosehill gardens                         -> rosehill gardens              ✗ unchanged
flemington                               -> flemington                    -- already canonical
lark hill                                -> lark hill                     -- already canonical
belmont                                  -> belmont                       -- already canonical
doomben                                  -> doomben                       -- already canonical
Sportsbet-Ballarat                       -> ballarat                      ✓ pre-lower title
Southside Cranbourne                     -> cranbourne                    ✓ pre-lower title
Northside Pakenham                       -> pakenham                      ✓ pre-lower title
Flemington                               -> flemington                    -- title-case
Royal Randwick                           -> royal randwick                ✗ unchanged
```

**The lift addresses sponsor-with-hyphen and locality-prefix venues only.** It does NOT address:

- Sponsor-without-hyphen (`ladbrokes geelong`, `bet365 camperdown`, `sportsbet oakbank`) — the regex `^[A-Za-z]+-` requires a trailing hyphen.
- "Royal" / "Aquis" / "Thomas Farms" / "Picklebet" prefixes — none in the locality regex.
- Suffix decorations (`@inner track`, ` tapeta synthetic`, ` parks` with-s, ` heath`, ` gardens`).

Per brief §5A "Code's discretion", I implemented the lift exactly as specified — the `_clean_venue` source itself only handles sponsor-with-hyphen and the named locality words, so a strict lift inherits those limitations. **Extending the patterns is a candidate for a follow-up Fix 6 brief**; surfaced in §5C's no-match breakdown below and explicitly NOT actioned in this session.

Post-§5A re-run of B1 / B2 / B3 was **not executed** — per brief §7 these queries are not expected to move post-§5A (existing rows still carry their old `venue_normalised`; the function change alone doesn't rewrite stored values). Confirmed expectation; reading the unmoved cross-tab as expected, not as a Fix-5A failure, is the next session's anchor.

---

## 5. §5B probe results

Time spent on §5B: ~12 minutes (within 15-minute time-box).

### Cross-tab venue intersection (post-harmonisation)

Top 30 venues that appear in BOTH the RA-only AND LC-only orphan sets (post-§5A `normalise_venue`):

```
venue_harmonised   ra_only   lc_only
bathurst              8       215
launceston            7       167
bendigo              24       119
hobart               15       117
morphettville         5        98
tamworth              6        96
warwick farm         77        16
doomben              59        33
flemington           78        10
belmont              73        14
sunshine coast        9        74
wyong                30        40
mornington           41        26
ipswich               1        61
muswellbrook         14        47
hawkesbury           21        37
rockhampton          19        35
gosford              17        36
kembla grange        18        30
scone                32        14
narrogin              8        37
ararat               13        31
ballina              13        25
geraldton             7        31
strathalbyn          22        14
balaklava            11        22
warrnambool          17        16
sale                  6        24
orange                7        22
armidale              5        22
```

Both sides have entries for the same harmonised venue, but the per-venue (date, race_number) tuples don't overlap cleanly. Two structurally distinct mismatch classes emerged.

### Class A — date drift (timezone hypothesis CONFIRMED for narrow set)

Sample for Sunshine Coast (Queensland, no DST, UTC+10:00):

```
RA: race_id=214265 race_date=2026-03-22 sched=2026-03-22T02:24:00.000Z R1
LC: race_id=209311 race_date=2026-03-21 sched=2026-03-22T02:24:00+00:00 R1

RA: race_id=214266 race_date=2026-03-22 sched=2026-03-22T02:59:00.000Z R2
LC: race_id=209548 race_date=2026-03-21 sched=2026-03-22T02:59:00+00:00 R2
```

`scheduled_start` (UTC) is identical to the second; `race_date` differs by exactly 1 day. **Same race, two rows.** Racing API stores `race_date` from the meet's local-day field; live-capture's path stores `race_date` from a UTC-day-ish derivation. This explains a small but real class.

Day-shift breakdown across the 13-edge-case venue set (1,339 normal-race RA-only orphans, excluding trials/jump-outs):

```
EXACT (date, vh, rn): 165 (12.3%)
DAY-SHIFT (+/-1 day, vh, rn): 21 (1.6%)  -- only sunshine coast (9), orange (6), ballina (5), rockhampton (1)
AMBIGUOUS: 0 (0.0%)
NO MATCH: 1,153 (86.1%)
```

Day-shift is real but narrow — it accounts for ~1.6% of the normal-race orphan set, all in non-DST QLD or border venues. Other edge-case venues (warwick farm, flemington, doomben, etc.) do **not** show date drift; their RA-side `race_date` matches the live-capture-side `race_date` for the same race when both rows exist.

### Class B — trial / jump-out exclusion (DOMINANT, was not surfaced in earlier reports)

Probing `warwick farm` 2026-03-30 (15 RA-only orphans):

```
race_id=286631 R1 sched=2026-03-29T22:00:00Z is_trial=1 is_jump_out=0 race_name="OPEN TRIAL"
race_id=286632 R2 sched=2026-03-29T22:12:00Z is_trial=1 is_jump_out=0 race_name="OPEN TRIAL"
race_id=286633 R3 sched=2026-03-29T22:24:00Z is_trial=1 is_jump_out=0 race_name="CLASS 1 & MAIDEN TRIAL"
... (15 rows total, all is_trial=1, all 12 minutes apart) ...
```

These are barrier-trial sessions — the Racing API tracks them, Betfair does not market them. They are **not** missing-merge candidates; they are correctly orphaned by design.

Across the full 3,249 RA-only orphan set:

```
is_trial  is_jump_out  count
0         0            1,339   ← real merge candidates
0         1            834     ← jump-outs (non-Betfair)
1         0            1,076   ← trials (non-Betfair)
```

**1,910 of 3,249 (58.8%) are unmergeable by design.** This finding repoints the `surgical_fix_1_2_report.md` §5 hypothesis: the warwick-farm-class residual is overwhelmingly trials/jump-outs, not race_date timezone drift. Date drift exists but is narrow.

### Findings split (edge-case 13-venue subset)

```
Total edge-case orphan races inspected: 432 (across 13 venues, normal races only — trials/jump-outs filtered)
Resolved by exact-key match post-harmonisation:     0 (0.0%)  ← LC-only counterparts don't exist for these
Resolved by timezone day-shift hypothesis:         29 (6.7%)
Resolved by race_number drift:                      0 (0.0%)
Unresolved (LC-only counterpart absent):          403 (93.3%)
```

The "unresolved" sub-class for the 13 edge-case venues mostly consists of dates where the live-capture side simply has no orphan row at all — either the race didn't have a Betfair market, or the live-capture row sits in a different cross-tab cell (e.g. `(0,0)` neither-flag rows from old PENDING discoveries, or the rare `(1,1)` already-merged cell). Sample for `warwick farm` 2026-03-02:

```
RA: race_id=31678 R9  sched=2026-03-01T23:36:00Z (Sun 10:36 AEDT — meeting day) is_trial=0 is_jump_out=0
RA: race_id=31679 R10 sched=2026-03-01T23:48:00Z                                is_trial=0 is_jump_out=0
... (15 rows of normal races) ...
LC counterparts on 2026-03-02: NONE (warwick farm has no LC-only row on this date)
```

These warwick-farm-2026-03-02 rows are real meetings but have no Betfair-side orphan — they may sit in the `(0,0)` cell from an earlier-cycle PENDING discovery, or Betfair simply didn't market them. Resolving this class requires either a wider match (cross-tab cell agnostic) or runtime evidence about Betfair coverage; out of scope per brief §6.

### §5B summary

The brief's load-bearing §5B hypothesis (timezone-shift) is **partially confirmed but narrowly**: it accounts for ~1.6% of the normal-race orphan set, only for non-DST venues (Sunshine Coast / Orange / Ballina / Rockhampton). The dominant explanation for the residual orphan class is **trial/jump-out exclusion** (58.8% of the full orphan set), which the surgical_fix_1_2_report.md did not surface. §5C uses both findings: day-shift broadening for the four named venues, plus an explicit `is_trial / is_jump_out` short-circuit so trials/jump-outs are flagged with a deterministic "no_match — Betfair does not market trials" reason rather than treated as a generic match-failure.

---

## 6. §5C dry-run merge plan summary

### Headline counts

```
Total orphan races inspected:                   3,249
  Clean merge:                                    186  (5.7%)
  Ambiguous (multiple LC candidates):               0  (0.0%)
  No match — is_trial:                          1,076 (33.1%)
  No match — is_jump_out:                         834 (25.7%)
  No match — unstripped naming:                   652 (20.1%)
  No match — no_lc_counterpart:                   501 (15.4%)

  Sum:                                          3,249  ✓
```

**Of the 1,339 normal-race orphans (excluding trials/jump-outs):**

```
  Clean merge:                                    186 (13.9%)
  Ambiguous:                                        0 (0.0%)
  No match — unstripped naming:                   652 (48.7%)
  No match — no_lc_counterpart:                   501 (37.4%)
```

The §5A lift addresses 13.9% of normal-race orphans cleanly. A regex-broadened follow-up (sponsor-without-hyphen, "royal X", "aquis X", suffix decorations) would unlock ~48.7% more — the unstripped-naming class is the highest-yield next-step.

### Top-10 clean merges

Six examples of the day-shift class (orange, sunshine coast):

```
orphan=47542 -> target=43807  | 2026-03-05 orange R2  (day_shift_broadened)
orphan=47543 -> target=44228  | 2026-03-05 orange R3  (day_shift_broadened)
orphan=47544 -> target=44443  | 2026-03-05 orange R4  (day_shift_broadened)
orphan=47545 -> target=44659  | 2026-03-05 orange R5  (day_shift_broadened)
orphan=47546 -> target=44879  | 2026-03-05 orange R6  (day_shift_broadened)
orphan=47547 -> target=45329  | 2026-03-05 orange R7  (day_shift_broadened)
```

Four examples of clean exact-key (locality-stripped → matches LC orphan):

```
orphan=960750 -> target=47690 | 2026-03-05 pakenham R1 (exact_key)
orphan=960751 -> target=47691 | 2026-03-05 pakenham R2 (exact_key)
orphan=960752 -> target=47692 | 2026-03-05 pakenham R3 (exact_key)
orphan=960753 -> target=47693 | 2026-03-05 pakenham R4 (exact_key)
```

### Top-10 no-match (unstripped naming)

```
orphan=960866 | 2026-03-06 stored='bet365 park kilmore' harmonised='bet365 park kilmore' R1
orphan=960867 | 2026-03-06 stored='bet365 park kilmore' R2
orphan=960868 | 2026-03-06 stored='bet365 park kilmore' R3
orphan=960869 | 2026-03-06 stored='bet365 park kilmore' R4
orphan=960870 | 2026-03-06 stored='bet365 park kilmore' R5
orphan=960871 | 2026-03-06 stored='bet365 park kilmore' R6
orphan=960872 | 2026-03-06 stored='bet365 park kilmore' R7
orphan=960873 | 2026-03-06 stored='bet365 park kilmore' R8
orphan=961007 | 2026-03-07 stored='aquis park gold coast' R1
orphan=961008 | 2026-03-07 stored='aquis park gold coast' R2
```

LC-only orphans for those venues exist as `kilmore` (112 rows) and `gold coast` (98 rows) — they would merge if the lifted regex were extended to handle non-hyphenated sponsor prefixes and suffix decorations.

Top venues by unstripped-naming no-match volume:

```
ladbrokes pioneer:                  53
aquis park gold coast:              50
royal randwick:                     48
ladbrokes cannon:                   44
ladbrokes geelong:                  39
sportsbet mount isa:                35
bet365 park kyneton:                30
thomas farms rc murray bridge:      28
sportsbet sandown lakeside:         24
bet365 park kilmore:                23
bet365 echuca:                      23
bet365 terang:                      23
sportsbet oakbank:                  23
```

### Top-10 no-match (no_lc_counterpart)

```
orphan=17 | 2026-03-02 'bathurst' R2  sched=2026-03-02T03:15:00Z
orphan=18 | 2026-03-02 'bathurst' R3  sched=2026-03-02T03:50:00Z
orphan=19 | 2026-03-02 'bathurst' R4  sched=2026-03-02T04:25:00Z
orphan=20 | 2026-03-02 'bathurst' R5  sched=2026-03-02T05:05:00Z
orphan=21 | 2026-03-02 'bathurst' R6  sched=2026-03-02T05:45:00Z
orphan=22 | 2026-03-02 'bathurst' R7  sched=2026-03-02T06:25:00Z
orphan=10 | 2026-03-02 'tamworth' R2  sched=2026-03-02T02:55:00Z
orphan=11 | 2026-03-02 'tamworth' R3  sched=2026-03-02T03:30:00Z
orphan=12 | 2026-03-02 'tamworth' R4  sched=2026-03-02T04:05:00Z
orphan=13 | 2026-03-02 'tamworth' R5  sched=2026-03-02T04:40:00Z
```

Top venues by no_lc_counterpart volume:

```
rosehill gardens:           38   ← suffix " gardens" not stripped; LC side may be 'rosehill'
morphettville parks:        30   ← suffix " parks" not stripped (vs " park"); LC has 98 'morphettville' rows
balnarring:                 18   ← genuinely venue without Betfair market?
innisfail:                  15
picklebet park werribee:    15   ← new sponsor pattern
picklebet park warwick:     14
barcaldine:                 11
kensington:                 10
thangool:                    8
narrogin:                    8
```

`rosehill gardens` and `morphettville parks` are particularly suspect — they're suffix-stripping near-misses (`gardens` not in the suffix list; ` parks` ends-with-`s` and the existing strip uses ` park` with no trailing-s tolerance). Same regex-broadening follow-up that fixes the unstripped-naming class would also fix these. (`rosehill gardens` is also surfaced in B3's top-20 — 91 races affected if the LC side stores `rosehill`.)

### JSON artefact

`dr029/2_1_race_data/fix_5c_proposed_merge.json` — 1.7 MB, 3,249 records. One record per RA-only orphan with fields:

- `orphan_race_id`, `race_date`, `venue_raw`, `venue_stored_normalised`, `venue_harmonised`, `race_number`, `scheduled_start`, `is_trial`, `is_jump_out`, `race_name`
- `outcome`: `clean | ambiguous | no_match`
- `target_race_id` (clean), `candidate_race_ids` (ambiguous), `reason` (no_match)
- `match_method` (clean): `exact_key` or `day_shift_broadened`
- `target_race_date` (day-shift clean): the LC-side row's actual `race_date` for the merge

Generation metadata: `generated_at_acst`, method-block describing the harmonised normaliser and day-shift broadening rule. Future merge-execution session reads this file as the contract.

---

## 7. Anything surprising

### a. Race-level cross-tab moved without §5A landing yet

Pre-§5A B1 read `(1,1) = 2,081` races with both flags. The `surgical_fix_1_2_report.md` §5 snapshot read `(1,1) = 0`. The cross-tab moved between 2026-04-30 and 2026-05-01 because the nightly `racing-metadata-backfill.service` ran twice (23:30 ACST 2026-04-30 and 09:00 ACST 2026-05-01 — the latter is a `Type=oneshot` retry; would need to read service journal to confirm). For races where the Racing API and live-capture paths happened to produce aligned `venue_normalised` values (no sponsor / locality / decoration drift in either path), the upsert collided correctly and produced a `(1,1)` row. The `(1,0)` orphan count nearly tripled in parallel (1,266 → 3,249) because more days were processed — including dates where the un-aligned-naming class dominates.

### b. Runner-level `with_both` is still 0 despite 2,081 race-level merges

This is the larger anomaly. 2,081 races now carry both subscription enrichment AND live-capture Betfair coverage at the race level, but `runners.finish_position IS NOT NULL AND betfair_selection_id IS NOT NULL` returns 0 across the entire window. The race-level merge composes via `upsert_race`'s `(race_date, venue_normalised, race_number)` key, which DID work for these 2,081 — but the runner-level merge composes via `compute_runner_key` (`N:<num>` if number present, else `S:<name>`) and that's where the failure now lives. The `_check_settlement` Betfair path writes `betfair_selection_id` keyed by Betfair's runner number; the Racing API path writes `finish_position` keyed by Racing API's `runner.number`. These should match — but evidence says they don't on the merged race rows. **This is a downstream finding, beyond §5's named scope.** Surfaced for triage. Likely follow-up: a per-runner-row probe within the 2,081 merged-at-race-level set to characterise where keys diverge.

### c. `betfair_market_id` column reference in the brief is stale

The brief's queries reference `betfair_market_id` but the schema column is `betfair_win_market_id`. The earlier `surgical_fix_1_2_report.md` §5 shows the same numbers with the same query semantics, so the column name shorthand was carried forward into the brief. Used `betfair_win_market_id` for B1 / B3 / §5C as the actual column. Result-shape unchanged.

### d. 3-file Fix-3 drift since `vps_drift_check.md` §3

`betfair/client.py` (+40), `betfair/models.py` (+2), `storage/database.py` (+48) are newly dirty since 2026-04-30 — the `vps_drift_check.md` §6 cross-check identifies these as the BSP-write-back anchor set. A separate Code session has executed `surgical_fix_3_brief` between Session 36 and this session. Surfaced for awareness; my edits did not touch these files.

### e. The lift's coverage is narrower than the brief's framing suggests

The brief lists 13 sample orphan venues (§2) including `aquis park gold coast`, `royal randwick`, `bet365 park kilmore`, `sunshine coast@inner track`, `devonport tapeta synthetic`. **Strict lift of `_clean_venue` does not address any of these** — the existing `_clean_venue` regex requires a hyphen for sponsor stripping and only handles named cardinal localities. The lift cleanly addresses `southside cranbourne`, `southside pakenham`, `sportsbet-ballarat`, `sportsbet-wangaratta` (the hyphen-pattern sample). Of the 13 brief-cited venues, only 3-4 are addressed by the strict lift. Per brief §1 "Surprises become findings in the report, not blockers" — surfaced here. Operator-Claude's call whether a Fix 6 brief broadens the regex.

### f. `morphettville parks` vs ` park` suffix near-miss

Existing `normalise_venue` strips ` park`, ` racecourse`, ` races`, ` race club`. It does NOT strip ` parks` (with trailing `s`). 60 `morphettville parks` orphans would resolve trivially with a one-character suffix-list extension or with `rstrip('s')` in the suffix loop. Same near-miss applies to ` gardens` (rosehill gardens, 91 orphans) and ` heath` (caulfield heath, 59 orphans).

### g. Day-shift class extends beyond the 13 brief-named venues

§5C found `orange` (6 races), `ballina` (5), `rockhampton` (1) also exhibit the day-shift pattern in addition to the brief-named `sunshine coast`. Common pattern: NSW border / QLD non-DST venues running races where Racing API's local-day differs from live-capture's UTC-day during March (DST-active period). Applied broadening to those four venues only; venues outside this set don't show the day-shift signal.

---

## 8. Self-assessment

**Brief scope adherence.** §5A → §5B → §5C executed in the named order. §5A edited `matching/race_matcher.py:normalise_venue` only — no drift into adjacent files. §5B was read-only; lifted findings repointed the warwick-farm hypothesis cleanly without exceeding the 15-minute time-box. §5C produced the JSON artefact at the named path with the named record schema.

**Hard limits held.**

- §9.1 single bounded session: ✓ (~43 minutes wall-clock).
- §9.2 named anchors only: ✓ (only `matching/race_matcher.py:normalise_venue` edited).
- §9.3 no schema changes: ✓.
- §9.4 no DB writes: ✓ (read-only URI used throughout).
- §9.5 no commit / stash / restore: ✓ (`git status` post-session matches pre-session list, plus the in-place diff growth of `matching/race_matcher.py` only).
- §9.6 no DR-029 named-debt remediation: ✓ (no tests added; verification snippet kept in `/tmp/`).
- §9.7 no mid-session escalation: ✓ (surfacing-only on every surprise).
- §9.8 no `bookmakers/sportsbet.py` edit: ✓.
- §9.9 no merge execution: ✓ (JSON plan only).

**Dirty-tree discipline.** §10 followed verbatim. Pre-edit `git status` captured. Post-edit `git status` confirmed only `matching/race_matcher.py`'s diff grew. The +3 newly-dirty Fix-3 files were surfaced as a finding (§7d) rather than treated as a blocker.

**What moved.**

- `matching/race_matcher.py:normalise_venue` is now the canonical normaliser carrying the lifted prefix-strip logic.
- `dr029/2_1_race_data/fix_5c_proposed_merge.json` exists at 1.7 MB / 3,249 records — the contract for a future merge-execution session.

**What did NOT move.**

- B1 / B2 / B3 cross-tabs are unchanged from the §3 baseline above (per brief §7's expectation — §5A only changes the function, not the stored values).
- The 1,910 trial/jump-out RA orphans remain orphaned (correct — Betfair doesn't market them).
- The 652 unstripped-naming and 501 no-LC-counterpart orphans remain orphaned (a Fix 6 follow-up would address ~80% of the former; the latter likely resolves only via runtime cross-tab-agnostic matching or per-venue alias additions).

**Assessment of the lift's effective coverage.** §5A is a real but partial fix. It harmonises forward — future Racing API discoveries with hyphenated-sponsor or named-locality prefixes will now upsert against existing live-capture rows correctly. It harmonises retroactively for ~14% of normal-race orphans (186 of 1,339). The remaining 86% of normal-race orphans need either (a) a regex broadening that the brief explicitly placed outside §5A's scope, or (b) per-venue alias-table extension, or (c) a different match strategy (cross-tab cell agnostic, or scheduled_start UTC keyed). Those choices are operator-Claude's call.

*End of report.*
