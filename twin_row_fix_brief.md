# Twin-row permanent fix — build brief v2 (worklist 0l, S259)

Status: REVIEWED — three adversarial reviews (repair-safety, write-side,
read-side/governance/ops lenses) all returned SAFE WITH FIXES; every accepted
fix is integrated below (changelog §8). Operator pre-authorised
("plan → adversarial review → if clear, proceed; return only for decisions").
Repo: `racing-data-capture` (capture-side only, per 0l scope). Companion report
to follow as `twin_row_fix_report.md`.

## 1. Problem (evidence, measured 29 Jul on the live DB)

One physical race gets multiple `races` rows ("twins"/"fragments") because the
natural key `UNIQUE(race_date, venue_normalised, race_number)`
(storage/database.py:78) admits any drift in date or venue spelling, and no
uniqueness exists on `betfair_win_market_id` (index only, non-unique —
storage/racing_day.py:90-93).

Live census (read-only, capture.db 4.8 GB):
- 8,876 markets all-time sit on >1 race row (first 2026-03-04, latest 2026-07-29).
- Since 1 Apr: 6,811 of 12,245 markets (55.6%). Class split by market:
  - 6,534 date twins (same venue_normalised, race_date differs by a day) —
    catalogue/collector row on one date vs subscription row on the local date
    (Pinjarra/Pinjarra Park anatomy, SESSION_252 §4c, B.5 worked example).
  - 214 date+venue twins; 56 same-date venue-variant twins (Randwick class,
    SESSION_258 §9); 7 race-number twins (NB: one market on two race numbers
    means at least one fragment is MIS-STAMPED — fragments are not guaranteed
    to be the same physical race; this drives the identity guard in §4).
- Data is genuinely SPLIT both ways (58 pairs since 20 Jul: stamps on the old
  row 58/58 vs 24/58 on the new; book snapshots more often on the new row).
  Repair must MERGE fragments, not pick-a-winner-and-drop.
- Collector double-tracking (same-date twins): 63 markets since Apr, 30 with
  Betfair snapshots on BOTH rows. Proven data loss: Randwick R3 29 Jul (two
  trackers, final ~6 min of snapshots landed on no row, BSP pass 0 rows,
  "16 runners settled" on an 8-horse field — worklist.md:28-36).
- Operational symptom: blank TAB column all day on Randwick 29 Jul, 9
  stamped-coverage RACING ALERTs overnight, BSP/settlement corruption above.

## 2. Root causes (from the code map)

Seven twin-generation surfaces, two families:

Date family (≈96% of twins):
- G1. Two date conventions: `match_races` Betfair-matched records already use
  the event's own timezone (race_matcher.py:295-301); the collector's
  bookmaker-only records and fallbacks stamp Sydney/UTC "today"
  (orchestrator.py:222); identity_sweep uses local_racing_day(start, event tz)
  (identity_sweep.py:154). Multiple writers, multiple date rules.

Venue family:
- G2. Collector normalises Betfair `event.name` ("Randwick Kensington 3rd Sep"
  → "randwick kensington") while identity_sweep normalises `event.venue`
  ("Randwick" → "randwick") — betfair/client.py:367 vs identity_sweep.py:152,375.
- G3. Each bookmaker's own venue spelling seeds its own grid key and race
  record in `match_races` (race_matcher.py:198-279).
- G4. `_find_matching_venue` substring match is non-transitive and dict-order
  dependent (race_matcher.py:505-517) — can stamp the market id onto the wrong
  variant, or (the race-number twin class) the wrong race.
- G5. `normalise_venue` has no track-within-venue aliases; S255 surface-suffix
  aliasing (synthetic/poly) lives ONLY in the morning-sweep day map.
- G6. No writer resolves by market id before inserting except identity_sweep
  (W7b.1). The collector's `_persist_race` → `upsert_race` goes straight to
  the natural key with new-value-wins COALESCE (database.py:331-345).
- G7. The collector tracks races by `races.id` with no market-id dedup
  (orchestrator.py:114,287-295) — N twin rows ⇒ N live trackers ⇒ the S258
  data-loss mechanism (BSP/final-flag/settlement triple-key on one race_id).
- G8 (SURVIVING GENERATOR, named): the subscription writer
  (subscription/racing_api.py:465-519) carries no market id, stamps
  race_date = query date and Racing-API course spelling, and still uses
  new-value-wins upsert_race. B1-B3 shrink its divergence; B4 cannot reach it.
  Mitigated (fill-guarded writes, §4 B7) but not eliminated; residual twins
  from this path are caught by B6 self-heal. Date-convention assumption
  (RA meet date == venue-local jump date) gets a test + rehearsal check.

(The `|code` collision valve — storage/racing_day.py:97-135 — is a DELIBERATE
splitter for different racing codes; preserved. Under B4 a same-code
natural-key collision with a DIFFERENT market id now also mints a valve-suffix
row instead of coalescing two real races — correct, recorded in DR-036 so the
data reset strips same-code suffixes.)

## 3. Governing constraints (locked)

- DR-034 (decisions.md:1337): WIN market id IS the race identity; fragments
  resolve by completeness; `races.id` is never an identity; target end-state =
  collapse at read + enforce at write. 0l executes that target → DR-036.
- DR-035 (decisions.md:1411): UNIQUE market-id index + code dimension in the
  natural key RESERVED for the data reset. 0l adds neither.
- W7b bans: COALESCE upsert banned for identity writes; never overwrite a
  non-null market id; never attach cross-code; race_date = venue-local racing
  day, never UTC-today; venue authority = Betfair catalogue spelling; on
  ambiguity INSERT + alarm.
- RC-2 principle (decisions.md:1399-1401, storage/database.py:269-309): match
  on HORSE IDENTITY, never bare saddlecloth number. Binds every cross-fragment
  bridge in this build (§4 identity guard).
- Surgical-fix-7 fence (archive/dirs/dr029/2_1_race_data/
  surgical_fix_7_design_brief.md:228 — a per-brief scope constraint, not a DR):
  superseded by the 0l commission; DR-036 cites that source.
- House repair conduct: timestamped `.backup` + integrity check first; archive
  never destroy; append-only audit; gates between steps; dress rehearsal on a
  copy; canary before full history.
- Governance reading (review-confirmed): the operator-present rule binds the
  v3 bethub.db reset only (v3_data_reset_runbook.md:1-10); worklist 0l
  commissions the capture historical repair explicitly; unattended execution
  with canary + gates is in scope. The report and DR-036 must say plainly that
  a destructive (merge) pass ran unattended under this commission.

## 4. Cross-cutting: the horse-identity guard (build gate — review R3-F1)

EVERY cross-fragment runner bridge (Layer A union, Layer C merge, B6) applies:
- Per-pair gate: fragments bridge only if runner-NAME overlap ≥50% with both
  sides having ≥3 comparable names (`robust_name_match_key`, S255
  `runner_identity_ok` shape — morning_sweep.py:254-272). Gate fail ⇒ Layer A
  falls back to current single-fragment behaviour; Layer C/B6 SKIP the market
  onto an audit/review list. Fragments with <3 named runners on either side:
  bridge only runners that name-match exactly; never number-only.
- Per-runner rule: a bridge (selection-id inheritance, stamp fill, results
  fill) requires robust-name agreement for that runner. Name mismatch at the
  same number ⇒ OMIT from the union map / no fill, audit line. Blank cell over
  wrong price, always (Phase E precedent).
- Scratched semantics: OR across bridged fragments (scratched-anywhere wins) —
  fill-if-null is a no-op on a NOT NULL DEFAULT 0 column (R3-F2).
- Settled-count sanity: results fills refuse when they would take canonical's
  settled-runner count above field size (R1-F5).

## 5. Design

### Layer A — read-side collapse (racing-api)

New shared module `api/market_resolution.py` (dedupes soft_odds.py:50-68 and
live_soft_odds.py:177-202):
- `fragments(db, market_id)`: all races rows for the market (rides
  idx_races_bf_win_market — NOT in database.py SCHEMA, created at
  racing_day.py:90-93; new test fixtures must create it explicitly).
- `union_selection_map(db, frags)`: runner map unioned across fragments under
  the §4 identity guard, bridged on runner_key/`N:<num>`/robust name.
  Selection-id conflict across name-agreeing rows: prefer the DR-034
  most-complete fragment, audit.
- `/soft-odds`: TAB-data fragment still supplies snapshot rows + captured_at
  (DR-034 ordering unchanged); runners keyed through the union map; the
  `runners: []` early-blank now only fires when NO fragment has stamps.
  Scratched flag = OR across bridged rows.
- `/live-soft-odds`: `sel_by_num` from the union map; tab_race_id/race_date/
  race_number coalesced (first non-null in DR-034 order).
- `results.py:108-124` by-market: DR-034 resolver + unioned, name-deduped
  runners (route currently has NO consumers — v3 avoids it explicitly;
  clients/vps_client/v1/results.py:9-18 — change is forward-hygiene).
- Perf: EXPLAIN no-scan tests extended to every new query (union adds ≤1
  index seek per fragment on sqlite_autoindex_runners_1; verified acceptable
  at the 3.5s refresher cadence).
- Cache/refresher untouched (registry keyed by market id; fix propagates).

### Layer B — write-side de-twinning (collector)

- B1 date rule, spec'd (R2-F6): race_date = calendar day of scheduled start in
  (1) the Betfair event timezone when a market matched (already done for
  matched records); else (2) state→tz lookup from bookmaker meta (small new
  table, _TZ_STATE inverse); else (3) Australia/Sydney. scheduled_start None ⇒
  today_str. `today_str` REMAINS the bookmaker-discovery query date
  (orchestrator.py:264) — only the row stamp changes.
- B2 venue source: collector Betfair venue = `event.venue`, fallback routed
  through `extract_venue_from_betfair_event(event.name)` (NEVER raw name —
  R2-F7). Plumbing: MarketSnapshot gains a venue field
  (betfair/client.py:348-377, models.py:62-83).
- B3 aliases: BETFAIR_VENUE_ALIASES += {"randwick kensington"→"randwick",
  "kensington"→"randwick"} (review-verified: no competing Kensington in the
  data); surface-suffix strips (" synthetic", " poly", " polytrack") promoted
  into `normalise_venue`. Morning-sweep day-map alias stays (becomes no-op;
  its tests pin it).
- B4 market-id-first adoption: shared `storage/race_identity.py` resolver
  (extracted from identity_sweep W7b.1) used by sweep AND `_persist_race`.
  Spec (R2-F2): once resolved by market id, ALL subsequent writes for that
  record go by `races.id` — guarded UPDATE for identity columns, fill-if-null
  for cross-reference ids; `upsert_race` is NEVER called for a
  market-id-resolved record. Never overwrite non-null market id; cross-code
  attach refused; venue_codes_today guard: collector passes its (possibly
  partial) day view and the resolver treats absence of code evidence as
  ambiguity (INSERT + alarm path), not as safety.
- B5 tracker dedup WITH MERGE (R2-F4/R3-F4): `_register_race` detects an
  existing RaceState tracking the same market id (same racing day); instead of
  registering a twin tracker it MERGES the refused record into the survivor —
  book race ids via the `_update_race_ids` machinery + fill-if-null onto the
  tracked row — and logs `AUDIT tracker twin-merged`. Registration order no
  longer decides data coverage.
- B5b late-attach name backfill (R2-F3): when a market id is attached to an
  existing RaceState (`_update_race_ids` or B5 merge), populate
  `betfair_runner_names`/sort priorities from the bf_win catalogue in scope at
  `_maybe_discover`, so Betfair capture + settlement work from the first poll.
- B5c collector resilience (R1-F3): an IntegrityError from a snapshot write no
  longer permanently drops the race (orchestrator.py:441-447); it invalidates
  the tracker's race_id and re-resolves via discovery on the next cycle.
- B5d runner-stamp writes become guarded fill-if-null (orchestrator.py:646-651
  unconditional overwrite — R2-F8).
- B6 nightly self-heal, FENCED (R1-F4/R2-F1): identity_sweep gains a merge
  pass using the Layer-C core, but ONLY over markets that are (a) venue-local
  racing day < today, AND (b) terminal (market CLOSED / capture_status
  terminal on all fragments / scheduled_start > 6h ago). Runs on all sweep
  invocations but the fence makes mid-card invocations no-ops for anything
  live. Counters in the sweep summary (`twin_merged= twin_skipped_gate=`).
- B7 subscription writer hardening (R2-F5): `_sync_single_race` race-row
  writes move to the fill-guarded path — never overwrite a non-null
  scheduled_start/race_name on an existing row (metadata refresh continues via
  the dedicated backfill columns it actually owns). Test pins the RA
  meet-date == venue-local-day assumption; rehearsal measures it.

### Layer C — historical repair (merge core + driver)

One merge core shared with B6; driver `scripts/merge_market_twins.py`.

- Scope: markets with >1 same-code rows (NULL racing_code is compatible with
  anything; only two DIFFERENT non-null codes ⇒ refuse + audit — R1-F11).
  Cross-code sharers: audit, skip. No-market-id shells: OUT (data-reset
  thread; no spine).
- Live-race fence (R1-F3 — replaces `--exclude-today`): a market is mergeable
  only if ALL fragments are terminal: latest non-null scheduled_start > 6h in
  the past AND no fragment's capture status is active; anything else is
  skipped this run. Date is NOT the fence (date twins are mis-dated by
  construction).
- Canonical row choice: (1) row whose race_date == venue-local racing day of
  the LATEST NON-NULL scheduled_start across fragments (all-NULL ⇒ skip rule);
  (2) DR-034 completeness (results present → most runners → most stamped
  selections → tab_race_id/book ids); (3) lowest id. Post-merge, canonical
  venue re-normalised through B3 `normalise_venue`; rename UNIQUE collision
  outside the merge set ⇒ audit + keep name.
- Merge mechanics per market — ONE transaction per market, FK ON (R1-F2),
  audit row inserted in the SAME transaction (= the journal, R1-F14):
  1. §4 identity-guard gate; fail ⇒ skip to review list.
  2. Runner unification: donor→canonical by runner_key (N: first), then by
     robust name for S:/unkeyed shapes (RC-2 S: keys have no number prefix —
     the migrate_s_to_n extraction does NOT apply to them, R1-F5); per-runner
     name agreement required for ANY fill; fills are fill-if-null EXCEPT
     scratched (OR) and results (settled-count sanity gate); unmatched donor
     runners: name-bridge first; if genuinely unmatched, INSERT under
     canonical ONLY when carrying payload (stamps/results/snapshot children);
     payload-less unmatched rows → audit, no insert (R3-F3, blocks S256 trial
     S:-row import).
  3. Child re-point to (canonical race_id, mapped runner_id):
     betfair_snapshots, bookmaker_snapshots, snapshot_batch_summary, AND
     betfair_historical (race_id + runner_id link columns — R1-F1). UNIQUE
     collisions: keep canonical's row, drop donor duplicate, count (verified
     near-impossible except single-fetch morning-sweep dual writes, which are
     identical — R1-F9).
  4. is_final_snapshot normalisation (R1-F7): if canonical ends with >1
     final-flagged set, keep the set carrying non-null bsp_price (else latest),
     unflag the rest, audit.
  5. Race-row coalesce: fill-if-null; never overwrite non-null.
  6. Matched donor runners DELETEd after re-point; donor race row DELETEd.
  7. Audit/journal row in `race_row_merges`: (market_id, canonical_id,
     merged_ids, run_id, merged_at, full pre-images of donor race+runner rows,
     old values of every canonical column changed, per-table manifest of moved
     child rows (table, rowid, old_race_id, old_runner_id), counts) — single
     bad merge reversible WITHOUT whole-DB restore (R1-F6).
- Schema handling: coalesce/pre-image column lists from PRAGMA table_info at
  runtime (live DB has migrated columns absent from SCHEMA: racing_code,
  bsp_price, source, tabtouch_race_id); fixtures include them (R1-F12).
- Post-run invariants (hard gates): zero orphans (runners LEFT JOIN races;
  both snapshot tables + betfair_historical LEFT JOIN runners/races); per-
  market snapshot-count preserved minus logged dupes; zero same-code
  multi-row mergeable markets remaining; endpoint replay on market
  1.260470533 → 8 stamped runners + TAB prices; Pinjarra exemplar single-row.
- Ops rails: preflight `df` gate (need ≥2× DB size free; disk verified 29G
  free of 48G); `.backup` + PRAGMA integrity_check + row-count proof;
  DRESS REHEARSAL on a VPS copy (per-market cost measured there sets the
  live-run budget; live run recomputes its OWN merge set — the rehearsal
  proves the code, not the row list); delete rehearsal copy before live run;
  `wal_checkpoint(TRUNCATE)` between market batches; STAGED live run:
  canary = pairs with race_date ≥ 2026-07-20 (~58 markets) → full
  verification gates → all-history pass; hard deadline abort at 04:30
  Adelaide (backup timer 05:00, backfill 05:30, sweep 05:50 — resumable
  design continues next quiet window; overrun would trip the backfill-failure
  alert email).
- Derived stores: report instructs a model.db re-extract
  (bethub-analytical capture_extract keys on races.id — R1-F8); pre-merge
  race ids 404 after repair (harmless at quiet hours, noted).

### Deliberately NOT in 0l

- UNIQUE(betfair_win_market_id) / natural-key code dimension (DR-035 reserve).
- No-market-id shell merging (they do NOT age out — they actively split book
  data until Betfair match adopts them; pre-existing class, explicitly left
  with the data-reset thread — R2-F4b), pre-14-day trial metadata, S:-key
  cleanup.
- Morning-sweep tie-break realignment (moot post-merge; noted in report).
- v3-side changes: none (collapse_fragments verified twin- and merge-tolerant).

## 6. Test plan (red-before at every layer)

- Layer A: Randwick-shape twin fixture (stamps on A, TAB snaps on B, shell C)
  → non-empty runners both endpoints; same-number/different-name fixture →
  runner OMITTED + audit (identity guard); <3-names fixture → exact-name-only
  bridging; scratched-OR test; EXPLAIN no-scan on every new query (fixtures
  create idx_races_bf_win_market); results-by-market union dedupe test.
- Layer B: date-rule tests (WA evening, NZ venue, UTC boundary, None
  scheduled_start); venue alias tests; B4 adoption tests (market-id-first,
  by-id writes after adoption, no upsert_race post-resolution, fill guards,
  cross-code refusal, no-overwrite, same-code valve mint); B5 merge-on-refusal
  test (refused row's TAB id reaches the survivor); B5b name-backfill test;
  B5c IntegrityError-re-resolve test; B6 fence tests (live race skipped,
  yesterday's terminal race merged); B7 no-overwrite test + RA date-convention
  pin; existing 198 pytest green.
- Merge core: fixtures for all four twin classes incl. double-tracked with
  dual final-flag sets and migrated columns; identity-gate skip; S:-row
  no-import; idempotency (re-run = no-op); crash-resume (kill mid-run;
  journal transaction boundary asserted); single-merge rollback exercise from
  the audit row; orphan-scan invariants.

## 7. Deploy plan (standing capture-fix authority)

1. Local build + full suite.
2. Push VPS + GitHub; restart racing-api (state loss lazy-rebuilt; restart
   only while no Decodo bench cooldown is active and outside final windows —
   R3-F10).
3. Restart racing-capture in a no-NEAR-races gap (checked against upcoming
   list; graceful ~13s, S250/S257 practiced).
4. Backup → rehearsal on copy (measure per-market cost) → canary → gates →
   full history, 04:30 deadline, resumable.
5. Verify: endpoint live replay, liveness pass clean (stamped-coverage groups
   UNIFY post-merge — alert counters move the safe direction), morning-sweep
   counters next morning; next Kensington/synthetic meeting = live proof.
6. Docs: SESSION_259 record, worklist 0l → done, DR-036 appended (identity
   enforcement executed; fence supersession w/ correct citation; valve-mint
   note for the reset; unattended-destructive-pass disclosure),
   twin_row_fix_report.md, memory update, model.db re-extract note.

## 8. Review changelog (S259 adversarial round, three reviewers)

Verdicts: 3× SAFE WITH FIXES. Blockers accepted+integrated: horse-identity
guard (§4); donor-runner disposal + FK ON + orphan gates (§5 C.6, R1-F2);
market-status live fence replacing date fence (R1-F3); B6 terminal-only fence
(R1-F4/R2-F1); B5 merge-on-refusal (R2-F4/R3-F4). Majors integrated:
betfair_historical re-point; by-id writes post-adoption; late-attach name
backfill; collector IntegrityError resilience; rollback manifest; final-flag
normalisation; scratched-OR; S:-row no-import; subscription named as
surviving generator + B7 hardening; B1 tz spec; B2 fallback via extractor;
guarded runner stamps; canary staging + deadline abort. Minors integrated:
NULL-code compatibility, PRAGMA-derived schema, df/WAL rails, journal spec,
model.db note, DR-036 citation fix. Review claims that did NOT hold (recorded
so they aren't re-raised): snapshot UNIQUE-collision loss, perf/index
regression, disk fit, false-alert storm, fence legality, by-market consumer
breakage, v3 compatibility, restart-gap realism.

Build deltas (S259, evidence-driven — detail SESSION_259 §2/§4, DR-036):
B1 dropped (zero new date twins since W7 15 Jul — generator already dead;
no state→tz table needed); B7 dropped (subscription no longer twins
post-W7; write-semantics change was risk>benefit); canonical completeness
ranks stamped selections above raw runner count (DR-034 §B.7 amendment,
DR-036 §4); payload-less drop narrowed to S:-keyed strangers only (a
plain N: card runner on a donor always moves).
