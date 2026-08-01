# International thoroughbreds — Phase 1 build brief (worklist 0p)

**Status:** PLANNING. No code written. **Commissioned:** S260 (operator: "first action of the next session"), from `international_thoroughbreds_assessment.md` §5 Phase 1 (items 5–7) + the operator-directed GB discovery flip (item 8), merged into one phase.
**Repos:** `racing-data-capture` (most work) + `bethub-v3` (thin display/plumbing glue).
**Standing decisions honoured:** D2 UK pilot, GB only; IE stays a disabled row. D3 country as plain column (no natural-key schema change). D6 Adelaide day is "the day"; picker shows venue-local date. D8 (settled below, §4): `race_date` is **not** flipped — ever, for book-discovered rows; `local_race_date` is the venue-local truth.

---

## 0. Operator summary — what this means for your betting day

Today the system already watches ~30 UK races a day through TAB — the odds are in the database — but the tool refuses to show them, because no UK race has a Betfair market attached and the tool drops any race without one. This build attaches the Betfair market.

When it's done: UK races appear in your race list and in the Log Past Bet picker like any Australian race — with TAB odds, live Betfair prices, a country tag, and the UK date shown so "Ascot Wednesday" can't be confused with Perth's Ascot or with the wrong day. You can log a promo bet on a UK race and the lay side works, because the Betfair market is real.

The dangerous part is not the switch — it's what the switch would do if flipped carelessly. The system currently tells same-named venues apart by nothing: UK Ascot and Perth Ascot are the same word to it, and a UK Sandown market could land on the Sandown Lakeside dogs. So the build order is fixed: first teach every race its country and make same-named venues collide-proof, prove that on a full day of data, **then** flip one database row to turn UK discovery on. The flip takes effect within 30 minutes without a restart, and flipping the row back turns it off just as fast.

Not in this build (deliberately): UK race **results** and settlement feeds (Phase 2), the commission/EV calibration fixes (Phase 3), promo "applies to international" scoping (Phase 3), Ireland and everywhere else. Until Phase 2, a UK bet settles the way an AU bet did before automation: the Betfair market settles it; the race-results door in the tool stays closed for UK. Your proxy bill does not move: everything new here talks to Betfair directly, which is not proxied.

---

## 1. What code inspection settled (corrections and confirmations)

These override the assessment where they conflict; several change the build's shape.

1. **Race-number synthesis (assessment item 9) is NOT needed for the pilot.** The collector matches a Betfair market to a bookmaker race by start-time proximity (≤600 s), not by market-name `R\d` — `matching/race_matcher.py:604-636`. UK race numbers come from TAB's card. The `R\d` parse is only needed on two paths that both fail *safe* for GB: (a) the collector's Betfair-only row creation (`race_matcher.py:427-434` — market is skipped, not corrupted); (b) the identity sweep, which already audit-skips numberless markets (`scripts/identity_sweep.py:138-142`). **Named limitation:** GB races at venues TAB does not list get no capture row in the pilot. The promos are at TAB, so the pilot's target set is exactly the TAB-served set. Synthesis is deferred to Phase 2 with the results work.
2. **Phase 0's "Betfair countryCode is country source 1" wiring is dead code, not merely unreachable.** `match_races` reads `getattr(snap, "country_code", None)` (`race_matcher.py:402-404, 445-447`) but `MarketSnapshot` has **no such field** (`betfair/models.py:61-125`) and `_catalogue_to_snapshot` (`betfair/client.py:371-401`) never copies `event.country_code`. Phase 1 must add the field.
3. **Phase 0 shipped ordering locks 1–3 but NOT lock 4.** `scripts/liveness_check.py` contains no country tripwire (grep: zero hits for "country"). Phase 1 adds it — it is precisely the post-flip safety net.
4. **The GB flip needs no collector restart and is one-row reversible — confirmed in code.** `market_countries()` is read from `jurisdiction_config` on every catalogue call (`betfair/client.py:212`, via `storage/racing_day.py:419-453`). Enable → next 30-min discovery pass picks it up; disable → same. Premature flip on old code raises inside `betfair_market_countries` (lock 3), which the orchestrator catches as a failed Betfair discovery — loud, no corruption.
5. **`PAGE_SIZE`/`MAX_PAGES` need NO resize for GB-only.** GB thoroughbred is ~25–40 WIN markets/day vs a 3,000-market pagination cap; AU today is 400–600. The truncation alarm exists (`betfair/client.py:163-168, 238-243`) and the identity sweep emails on cap (`identity_sweep.py:440-451`). The 12 h lookahead (`orchestrator.py:289`) also stands: the 30-min discovery cadence sweeps the UK evening card in as it enters the window.
6. **The live mis-bind risk at flip time is worse and more specific than R2 describes.** Two mechanisms, both in `race_matcher.py`: (a) `_find_matching_venue:597-599` bidirectional substring — Betfair GB "Ascot"→`ascot` binds TAB's `ascot uk` grid key, or exact-matches Perth's `ascot` when Perth races the same day; (b) worse, TAB's AU "Sandown Park" dogs venue normalises to `sandown` (` park` suffix strip, `:131-135`), Betfair GB "Sandown" also → `sandown`, and `_match_betfair_to_race_number` will accept any dog race starting within 10 minutes of the UK race — GB evening racing and AU night dogs overlap, so a **GB thoroughbred market can be written onto an AU greyhound row**, flipping its `race_date` and `racing_code` (`:386-388`). This is why the identity work is a hard precondition, mechanically enforced.
7. **The Betfair-branch `race_date` overwrite is the twin generator for GB.** `race_matcher.py:387` sets a matched race's `race_date` to the venue-local day. A UK evening race's TAB row sits under the AU card date (probe-proven, S259 §20); rewriting it to the UK date changes the natural key, so the first pass after the flip would INSERT a second row per UK race (`storage/database.py:340-345` upsert) and double-track it — market-less-twin class, invisible to `race_resolve`/`twin_merge`/self-heal. §4 makes this overwrite AU-only.
8. **Betfair traffic is not proxied.** `betfair/client.py` contains no proxy configuration; `capture/proxy.py` is consumed only by bookmaker fetch/discovery paths in `capture/orchestrator.py`. **Decodo delta of this phase ≈ 0** (UK races are already TAB/TABtouch-polled; the flip adds Betfair-direct traffic only: ~+2 catalogue pages/pass and ~+1,000–1,500 `listMarketBook` calls/day, well inside Betfair's own limits). Disk: ~+10–15k Betfair snapshot rows/day (~5–8 MB/day) against R7's runway — no decision required.
9. **The historical `country`/`local_race_date` backfill is already built** — it lives in `scripts/coverage_recompute.py` (header, refusal 2) and runs automatically once the twin repair reports zero markets outstanding. Item 7's remaining content is the venue-key requalification migration only (§5).
10. **Tool-side, most of the pilot works with no code change:** the picker's `collapse_fragments` (`clients/vps_client/v1/_lookup_api.py:246-300`) passes any row with a market id + runners; race-screen live prices are REST-per-market-id (`ui/web/src/api/racing.ts:97` → `_translation.py` `listMarketBook`), country-agnostic; per-market commission (`market_base_rate`) is already sourced from Betfair per market (`racing_catalogue.py:78-81`), so GB markets carry their real MBR and the 8% figure is only the description-absent fallback. The two v3 gaps: the **live sidebar** is built from a Betfair catalogue call hardcoded `marketCountries:["AU"]` (`_translation.py:289`), and the payload/picker show no country or venue-local date. The stream filter (`_stream_transport.py:121-125`) is NOT needed for the pilot: live prices are REST, and the streaming pre-check gates on global subscription status, not per-market coverage — deferred with its consumers named (§6.4).

---

## 2. Scope

**In:**
1. Betfair `country_code` plumbing end-to-end (capture).
2. Country-qualified venue identity + international-safe matching (capture) — the collide-proofing.
3. D8 semantics locked in code: `race_date` = AU card/join date for book-discovered rows; venue-local overwrite becomes AU-only; `local_race_date` authoritative for display.
4. Historical requalification migration for non-AU rows (~3,400 rows) + coverage/venue_country key migration + collision census/merge, journalled.
5. Ordering-lock completion: `INTL_IDENTITY_VERSION = 2`, migration-done marker in the readiness assertion, liveness lock-4 tripwire.
6. The GB flip itself, as a separate, one-row, restart-free, reversible step, behind a full verification day.
7. Minimal tool glue: capture-API payload gains `country` + `local_race_date`; v3 picker shows them and keys venues uniquely; v3 sidebar catalogue includes GB.
8. A read-only pre-flip GB catalogue probe (volume, venue names, market-name conventions, ante-post frequency).

**Out (deferred, named):** GB results/BSP/settlement supply (Phase 2, items 10–11); race-number synthesis (Phase 2); commission-by-market EV fix + uncalibrated-EV marker (Phase 3, item 13/D7); promo jurisdiction scope (item 15); each-way terms; v3 stream country widening; IE and all other jurisdictions (IE remains one disabled row); `check_stamped_coverage` widening (Phase 2); any change to AU venue normalisation output (regression-locked instead).

---

## 3. Design

### 3.1 Commit 1 — Betfair country plumbing (no behaviour change)
- `betfair/models.py` `MarketSnapshot`: add `country_code: str | None = None`.
- `betfair/client.py:_catalogue_to_snapshot`: `country_code=getattr(event, "country_code", None) if event else None`.
- `scripts/identity_sweep.py:_raw_market` (:360-380): carry `country_code` too (used only for its skip-audit line for now).
- Tests (red-before): snapshot carries the catalogue's countryCode; existing AU discovery byte-identical (`test_intl_identity.py` pattern, `:472` "client still asks for AU only" stays green).

### 3.2 Commit 2 — country-qualified venue identity + international-safe matching
All in `matching/race_matcher.py` + `storage/racing_day.py`; **AU output frozen and regression-locked** (fixture = the live DB's distinct `venue_normalised` corpus for AU-state rows; every key must round-trip unchanged).

- New `qualify_venue(venue_norm: str, country: str | None) -> str` in `storage/racing_day.py`: returns `venue_norm` unchanged for `country in (None, "AU")`; else applies (i) unicode NFKD accent fold, (ii) a per-country suffix-strip map — `{"GB": (" uk",)}` — then re-runs the trailing-suffix strips (` park` etc.) so `sandown park uk` → `sandown`, (iii) appends `|<cc>` lowercase, e.g. `ascot|gb`. Suffix style matches the existing `|greyhound` valve; the reset's suffix-strip targets racing codes only, so no clash.
- `match_races` grid build (`:219-334`): after country resolution (`:235-248`), the grid key and `race_record["venue_normalised"]` become `qualify_venue(vkey, country)`. Lookups that must stay on the base name (`get_meeting_type`, `infer_track_type`, `venue_timezone`, `BETFAIR_VENUE_ALIASES`) keep receiving the unqualified base.
- Betfair branch (`:341-424`): derive `bf_country = canonical_country(snap.country_code) or canonical_country(state_from_timezone(snap.event_timezone))`; qualify the Betfair venue key with it before `_find_matching_venue`.
- `_find_matching_venue` (`:589-601`) replaced by country-aware matching: (1) exact on qualified keys; (2) alias pass — new `INTL_VENUE_ALIASES` seed per country (GB seed from the §3.6 probe: `yarmouth`→`great yarmouth`, `newmarket july`/`newmarket rowley`→`newmarket`, …); (3) substring fallback **only between keys of the same country** and only where one key equals the other extended by whole words. **AU↔AU keeps the exact current behaviour; cross-country binding is impossible by construction.** Unmatched non-AU Betfair markets log one INFO audit line each (`AUDIT gb-market-unmatched: <event> <name>`), which is how the alias table grows.
- **D8 in code:** the matched-branch `race["race_date"] = derived_date` (`:387`) becomes conditional — only when `bf_country in (None, "AU")`. Non-AU matched rows keep the grid/book `race_date` (AU card date, the join key); they still receive market ids, `racing_code`, and `local_race_date` from the Betfair event timezone (`:396-400`, already present). The Betfair-only creation path keeps venue-local `race_date` (unreachable for GB in the pilot — no `R\d`).
- Multi-WIN guard: if a second WIN snap matches a grid slot that already received a market id this pass, first-wins + audit WARNING (ante-post double-market defence; probe quantifies how often it exists).
- `storage/race_resolve.py:_FILL_COLUMNS` (:27-51): add `local_race_date` (fill-if-null, non-identity) so adopted rows get their local date.
- Tests (red-before): GB Sandown market must NOT bind AU `sandown` (dogs-at-Sandown fixture with a start time 4 min away — the mis-bind proven as a failing test first); GB Sandown binds the TAB `sandown park uk` row and the row's `race_date` is unchanged while `betfair_win_market_id` and `local_race_date` land; Ascot GB vs Ascot Perth same-day fixture yields two rows, two countries, zero shared keys; Yarmouth alias; AU corpus regression; second-WIN-market first-wins.

### 3.3 Commit 3 — historical requalification migration + lock completion
- New `scripts/migrate_intl_venue_keys.py`: for every row with `country IS NOT NULL AND country != 'AU'`, compute `new_key = qualify_venue(old_key, country)`; census collisions first (`--dry-run` prints: rows to rewrite, target-key collisions per `(race_date, new_key, race_number)`); collisions (expected: the `ascot uk`-vs-`windsor`-style same-meeting split keys, small) are merged by the runner-name-identity-guarded journalled pattern (`storage/twin_merge.py` journal shape; pre-image table `intl_rekey_journal`), never pick-and-drop; then `UPDATE races SET venue_normalised = new_key`, and the same key mapping applied to `book_venue_coverage` and `venue_country` in the same transaction so coverage suppression does not reset to UNKNOWN.
- Disjointness proof before running (the reason this need not wait for the full twin-repair finish): `SELECT COUNT(*) FROM races WHERE betfair_win_market_id IS NOT NULL AND country IS NOT NULL AND country != 'AU'` must be 0 (assessment: 0 of 1,925) — the repair's merge set is market-keyed, so the rekey set and the repair set are provably disjoint. **If the count is non-zero, stop and wait for repair-zero.** Either way the migration runs outside 23:45–04:30 ACST and refuses while `twin-repair-n2.service` is active (same preflight as `scripts/collector_restart.py:62`).
- The migration writes `schema_meta('intl_rekey_done', <utc>)`; `assert_identity_ready` (`racing_day.py:456-493`) gains the check: enabled non-AU country requires the marker. `INTL_IDENTITY_VERSION` → 2 (`racing_day.py:53`) in this commit, so lock 3 opens only with the code that makes the flip safe.
- Deploy coupling: migrate-then-restart in one window — the collector must never run new matching code against un-migrated keys or vice versa (else a fresh discovery pass mints qualified-key twins of the in-flight international rows).
- Liveness lock 4 (`scripts/liveness_check.py`): new check — FAIL on any row with `betfair_win_market_id NOT NULL` created in the last 24 h whose `country` is NULL-or-'AU' while its `state` is a non-AU code, or whose `venue_normalised` lacks the `|cc` qualifier while `country != 'AU'`. This is the post-flip mis-stamp tripwire.
- Tests: migration idempotence (second run = 0 changes); collision merge journalled with pre-images; readiness assertion refuses GB-enabled without the marker (red-before).

### 3.4 Commit 4 — capture API payload
`api/models.py` `RaceSummary`/`RaceDetail` (+`RaceResultSummary` for symmetry): add `country: str | None = None`, `local_race_date: str | None = None`; populate in `api/routes/races.py:_build_race_summaries` and `race_detail` (routes already `SELECT *`). Additive; `racing-api` restart required on the VPS.

### 3.5 Commit 5 (bethub-v3) — display glue
- `clients/vps_client/v1/race_lookup.py`: `MeetingSummary`/`RaceSummary`/resolve payloads carry `country` and `local_race_date` (nullable, additive).
- `ui/web/src/routes/LogPastBet.tsx:374-377`: venue option label gains a country tag for non-AU (`Ascot Uk · T (7) — GB`) and the option `key` becomes `venue + country` (kills the duplicate-React-key hazard).
- Race header/picker detail: show `local_race_date` beside the Adelaide day when they differ (D6's condition for "Adelaide day everywhere" being safe).
- Sidebar: `_translation.py:289` `marketCountries` becomes a module constant `RACING_MARKET_COUNTRIES = ["AU", "GB"]` (env-overridable `BETHUB_RACING_COUNTRIES`), one catalogue call per code per country to stay under the S236 data-weight cap (`racing_catalogue.py:131-139` documents the cap; the per-country split mirrors the per-code fix). `RaceListSidebar.tsx:204` already renders `R?` for numberless GB markets — acceptable; optionally suffix the venue line with `country_code` (already in the payload, `racing.py:702`). Note the sidebar is Betfair-direct, so it will show GB venues capture has no TAB row for — Betfair prices only on those; correct and harmless.
- Rollback: constant back to `["AU"]`; all other changes additive display.
- Tests: vitest for the option key/label; pytest for payload passthrough; translation test for the country list + per-country split.

### 3.6 Pre-flip probe (read-only, before commit 2 is finalised)
`scripts/probe_gb_catalogue.py` — direct `list_market_catalogue` calls with a GB filter (bypasses the choke point legitimately; read-only; no DB writes; writes its report under `probe_output/`). Outputs: GB WIN/PLACE market counts for today+tomorrow (volume claim), distinct `event.venue` values vs TAB's GB venue keys (alias seed), market-name samples (confirms the no-`R\d` convention, assessment §7.8), multi-WIN-per-event frequency (ante-post guard sizing). Also settles assessment §7.1.

---

## 4. D8 — race_date semantics, decided and justified against code

**Decision: for bookmaker-discovered rows, `race_date` permanently means "the AU card date the row was discovered under" — the join key. `local_race_date` is the venue-local truth for display. The Betfair venue-local `race_date` rule applies to AU (and Betfair-only) rows exclusively.**

Justification from code, in order of weight: (1) flipping a matched row's `race_date` changes the natural key (`database.py:343`), and the first post-flip pass would insert a twin per UK race and double-track it (§1.7) — on the one class where `race_resolve` (market-id-keyed, `race_resolve.py:70-74`), `twin_merge` (market-scoped) and the B6 self-heal are all blind until the market id lands, i.e. exactly during the transition; (2) TAB files overseas meetings under its AU card date (S259 probe: Sandown Park UK, 29 Jul UK, on TAB's 30 Jul card), so the card date is the only stable book-side identity — the Phase 0 `book_query_date` decoupling (`scheduler.py:114-118`, `orchestrator.py:1110,1117`) protects fetches either way, but readers of `race_date` (`scripts/morning_sweep.py`, v3 `_keep_on_day` fallback `_lookup_api.py:218-221`) still consume it; (3) the tool already buckets by `scheduled_start`→Adelaide day (`_lookup_api.py:208-221`), so `race_date`'s display role is residual; D6 is satisfied by showing `local_race_date`. Meeting-fragmentation (Windsor split across two card dates) remains a *raw-query* cosmetic; `GROUP BY venue, local_race_date` is the meeting query. No historical `race_date` rewrite, ever, for this class.

---

## 5. Sequencing — with the ordering lock explicit

```
0. Probe (§3.6)                                — read-only, any time
1. Commit 1  country plumbing                  — deploy anytime (no behaviour change)
2. Commit 2  qualified identity + matching     ┐ deploy TOGETHER with
3. Commit 3  migration + version bump + lock 4 ┘ migration, one window
   GATE A: disjointness census == 0, migration dry-run clean,
           twin-repair not active, outside 23:45–04:30 ACST,
           au_suppressed == 0 in that morning's recompute log
4. Commit 4  capture API fields (racing-api restart)
5. Commit 5  v3 glue (live at next app start)
   GATE B (the assessment's Phase-1 gate, one full day, SQL below §7):
           every new international row has correct country + local_race_date,
           zero AU/international venue-key collisions, twin census unchanged
6. THE FLIP: UPDATE jurisdiction_config SET enabled=1 WHERE country='GB';
           — no restart, effective ≤30 min, one-row rollback
   GATE C (post-flip day): GB rows carry market ids + country='GB',
           no mis-binds (lock-4 liveness green), tool renders, operator logs
           one real GB promo bet end-to-end
```

**ORDERING LOCK (non-negotiable, now mechanical):** the flip is impossible before commits 2+3 are live — lock 3 raises below version 2, lock 2 refuses boot without the rekey marker, and lock 4 alarms if anything slips through an unpredicted path. Country stamping is verified on a full day of TAB-side GB rows **before** any Betfair GB market exists.

**Coexistence with tonight's machinery:** commits 1–2 touch no race rows; the migration is disjoint from the repair's market-scoped merge set (proven by census, refused if not), runs outside 23:45–04:30, and refuses while `twin-repair-n2.service` is active. The 04:05 coverage recompute and the `au_suppressed == 0` check are untouched — the migration's coverage-key mapping runs in the migration transaction, not in the recompute. The historical `country`/`local_race_date` backfill continues to ride `coverage_recompute.py`'s existing repair-zero gate unmodified.

---

## 6. Test plan (red before green; capture suite currently 385)

Per commit as listed in §3, plus cross-cutting:
- **AU invariance corpus:** every distinct AU `venue_normalised` in the live DB (fixture export) is unchanged by the new normalisation path; a fixture AU discovery day produces a bit-identical tracked-race set and identical race rows.
- **The mis-bind fixtures (the most important tests in the build):** GB Sandown vs Sandown Lakeside dogs (+4 min start offset) — no bind, red-first; GB Ascot + Perth Ascot same day — two rows, both correct.
- **D8:** matched GB row keeps card `race_date`, gains market id + venue-local `local_race_date`; AU matched row still gets the W7 venue-local overwrite (regression).
- **Locks:** flip before version 2 raises (exists, `test_intl_identity.py:442`); flip without rekey marker refuses boot (new); lock-4 liveness fires on a seeded mis-stamped row and stays green on a clean day.
- **Migration:** idempotent; journalled collision merge preserves pre-images and unions runners/snapshots; coverage keys migrate in-step (an UNSERVED venue stays UNSERVED under its new key).
- **v3:** 1949 pytest / 494 vitest stay green; new picker/translation tests as §3.5.

## 7. Verification gates — the SQL that proves them

Gate B (run over the verification day D, all must hold):
- `SELECT COUNT(*) FROM races WHERE created_at LIKE 'D%' AND country NOT IN ('AU') AND country IS NOT NULL AND (local_race_date IS NULL AND scheduled_start IS NOT NULL)` → 0; spot-check 10 rows' `local_race_date` against jurisdiction tz by hand.
- Non-null `country` on ≥95% of day-D international rows with non-blank `state`.
- `SELECT venue_normalised FROM races GROUP BY venue_normalised HAVING SUM(country='AU') > 0 AND SUM(country IS NOT NULL AND country != 'AU') > 0` → empty (no shared keys).
- `SELECT COUNT(*) FROM races WHERE country IS NOT NULL AND country != 'AU' AND venue_normalised NOT LIKE '%|%'` → 0 post-migration.
- Twin census (Phase 0 A10 query) → unchanged (≤1 in the trailing window).

Gate C adds: every GB row with a market id has `country='GB'` and both TAB + Betfair snapshots; lock-4 check green all day; the assessment-item-8 alarm silent (no truncation); picker + sidebar render GB; one operator-logged GB bet.

## 8. Deploy + rollback

Deploy per the S259 pattern: local full suite → push VPS + GitHub → gap-aware restart (`scripts/collector_restart.py` logic, never bare `systemctl restart racing-capture`) → `racing-api` restart at commit 4 → v3 lands at next app start (BetHub.command rebuild). Preflight refusals (scripted): repair unit active; 23:45–04:30 ACST; disk floor; that morning's `au_suppressed != 0`.

Rollback: commit 1–2 = git revert + restart (qualified keys written in the interim are non-AU-only and self-heal at next discovery via natural-key re-upsert — but revert *before* migration only; after migration, revert code + re-run the migration's journalled reverse map, which the script must emit). Commit 3 = journal-driven reverse (`intl_rekey_journal` holds old→new). Commit 4–5 = revert, additive fields ignored. **The flip = `UPDATE jurisdiction_config SET enabled=0 WHERE country='GB'`** — effective ≤30 min, no restart; already-attached GB market ids remain on their rows harmlessly (rows are correct; they simply stop refreshing).

## 9. Risks

R-a GB Betfair↔TAB venue-name misses (alias gaps) → races missing, never corrupted; INFO audit + alias top-up; probe pre-seeds. R-b ante-post double-WIN markets → first-wins guard + probe sizing. R-c TABtouch-only blank-state GB venues stay unqualified until `venue_country` learns them → unmatched (miss, not corruption). R-d migration collision-merge on market-less rows relies on runner-name identity — journalled, dry-run first, pre-image reversible. R-e post-flip the overnight Betfair-freshness liveness check arms for the first time (GB market-bearing races exist overnight) — expected louder watchdog; observe first night. R-f sidebar per-country catalogue calls still hit TOO_MUCH_DATA on a big Saturday → already split per code per country; further split is mechanical. R-g EV renders on GB races with AU calibration and no marker until Phase 3 (operator-sequenced; named, not fixed here). R-h GB results door stays closed until Phase 2 — bets settle via Betfair market settlement as normal. R-i in-flight international trackers at migration restart re-resolve via natural key under new keys — the migration rewrote the rows first, so keys align; tested by the tracker-invariance fixture.

## 10. DECISIONS NEEDED FROM OPERATOR

None. Code inspection settled every open question in this phase's scope. (Standing items unchanged: IE stays a disabled row until the operator asks; the UK+IRE-together recommendation remains on the table from Phase 0.)

---
*Planning document. No code written; all DB references from prior session evidence; repo inspection read-only.*

---

# v2 — Adversarial review round 1: integrated fixes (NORMATIVE)

Three independent reviewers (corruption/twins, matching identity, ops/deploy): **3× SAFE WITH FIXES, zero UNSAFE.** This section is normative and OVERRIDES §1–§9 where they conflict. Failed attacks confirmed: AU invariance by construction, D8 kills the GB twin generator, repair disjointness, flip reversibility, B6 cannot strip `|cc`, `|greyhound`-suffix parsers all strip to base identically, probe login concurrent-session-safe, stale post-rollback GB market ids harmless in v3.

## F1 — Country is stamped from the catalogue REQUEST, fail-closed (replaces §3.2's bf_country derivation) — BLOCKING
Betfair commonly returns tz "GMT" and may omit countryCode for GB; `state_from_timezone` returns None for GMT → the unqualified key re-opens the exact Sandown-dogs mis-bind, and `bf_country in (None,"AU")` re-enables the race_date overwrite. Therefore: discovery makes **one catalogue call per enabled country**, and every `MarketSnapshot` from that call is stamped `country_code = <the requested country>` (authoritative; `event.countryCode` used only as a cross-check/audit). With any non-AU jurisdiction enabled, a snapshot whose country is unresolvable is **dropped + audited, never matched**. The D8 race_date-overwrite gate becomes `bf_country == "AU"` strictly (None does NOT overwrite). `_TZ_STATE` gains no GMT entry — inference is no longer load-bearing. Probe (§3.6) must report countryCode/timezone presence rates.

## F2 — Per-country event-type scoping (GB = thoroughbreds only) — BLOCKING
The flip widens ALL catalogue calls including greyhounds (type 4339): GB dogs are ~400+ WIN markets/day (Romford, Hove, Newcastle, Yarmouth, Sunderland, Doncaster — several sharing AU venue names), 10× §1.5's volume math, and a GB dog market can bind an AU thoroughbred row and flip racing_code (matched branch has no code guard). Therefore: `jurisdiction_config` gains `betfair_event_types` (AU keeps '7,4339'; GB = '7'); the choke point filters per (country → event types). PLUS a racing-code guard on the matched branch: a market never binds a grid race of a different racing code, any country. Probe samples GB dog/harness market names too.

## F3 — Identity sweep skips non-AU markets in Phase 1 — BLOCKING
The sweep consumes the same widened catalogue (identity_sweep.py:408). Its no-`R\d` skip is convention, not a guard: a GB market named with `R\d` inserts an unqualified UK-dated row, or ADOPTS a market-less same-date AU row (UK 2026-07-30 == AU 2026-07-30; GB Ascot R5 → pre-market-id Perth Ascot R5). Therefore: sweep processes only snapshots with `country_code == 'AU'` (from F1 stamping) in Phase 1. Deferred with the results work: sweep GB support.

## F4 — Qualification reads learned `venue_country` at match time + flap census — BLOCKING
Grid country from per-pass book meta alone flaps (TAB timeout → TABtouch-only blank state → unqualified key pass 1, qualified pass 2 → market-less twin pair, invisible to all repair machinery). Therefore: `match_races` receives the learned `venue_country` map (the orchestrator has a conn; load once per pass) and resolution order is book-meta country → learned venue_country → None. AND lock 4 (liveness) gains a daily census: same base venue appearing under both a qualified and an unqualified key within the trailing 48 h → FAIL (this also catches F1 escapes). A same-base merge for any pairs the census finds uses the journalled migration merge path, run manually on review.

## F5 — Deploy window scripted and enforced (replaces §3.3 "one window" + §8 preflight) — BLOCKING
Three other writers can act between pull, migration, and restart (collector 30-min discovery; morning sweep hourly + identity sweep 3×/day run NEW code from the shared checkout immediately after pull; liveness self-heal can restart the collector unbidden). Therefore a single deploy script executes: **gap-aware STOP collector (reuse collector_restart gap logic) → git pull → migrate → start**, refusing to begin if `racing-capture`, `racing-identity-sweep`, `racing-morning-sweep`, or `twin-repair-*` units are active, targeting a <15-min window (self-heal needs 2 consecutive 15-min failures) placed off the top of the hour, outside 23:45–04:30 ACST, disk-gated. Migration itself re-checks the same unit set.

## F6 — Gate A recompute clause made satisfiable
Tonight's repair may hold its unit past both recompute slots (Persistent=false, no catch-up) → tomorrow may have NO au_suppressed line. Gate A becomes: most recent recompute ≤48 h old shows `au_suppressed == 0`; if none exists, run `coverage_recompute.py --dry-run` manually in daytime (prints the summary; only refuses while the repair unit is actually running) and use its au_suppressed.

## F7 — morning_sweep excludes non-AU rows in Phase 1
`load_races` has no country filter; GB rows share today's race_date (D8), and `fetch_id_for` uses the BASE venue key → AU book day-maps could fetch Perth Ascot odds onto UK Ascot rows. Add `AND (country IS NULL OR country = 'AU')` to sweep targets. Deferred: GB sweep support with results work.

## F8 — venue_country old-key aliases + re-runnable migration
`backfill_country_from_venue_table` joins on `venue_normalised`; after rekey, NULL-country historical GB rows under OLD keys would never backfill and Gate B/lock 4 would stay permanently dirty. The migration keeps old-key alias rows in `venue_country` (marked alias) and is idempotent + re-runnable after each nightly backfill until its census is zero.

## F9 — Reverse-rekey semantics
Journal-driven reverse can collide with rows minted under old keys in the interim: reverse is merge-or-refuse **per row** (identity-guarded journalled merge on collision, refuse+log otherwise), never a blind UPDATE.

## F10 — Grid conflicting-country-evidence audit
TAB "(Gbr)"-style names normalise to the bare name upstream of qualification, so a GB meeting can merge into a same-day AU meeting's grid bucket before country is resolved. The grid build logs an AUDIT warning when one bucket accumulates conflicting country evidence (and the probe records TAB's naming style per GB venue so aliases pre-empt this).

## F11 — Multi-WIN tie-break
First-wins by catalogue order can stick a same-start ante-post/secondary WIN market all day. Tie-break: prefer the market whose runner count matches the grid race; then higher total matched volume; WARN with both market ids either way.

## F12 — Confidence calc uses base venue
`_compute_race_confidence` compares the event-name venue to the (now qualified) key → every GB match would degrade to 0.5 "time_proximity_only". Compare against the base (unqualified) venue.

## F13 — Sidebar per-country error isolation
`racing_catalogue.py` fails the whole read on any single call failure → a GB Betfair error would blank the AU sidebar every 60 s. GB call failure degrades to omit-GB (one WARN); AU failure keeps failing the read.

## F14 — Brief corrections & notes
- §1.4: the identity sweep ALSO consumes the widened catalogue post-flip (safe for numberless GB markets via the R\d skip; F3 hard-guards it).
- §1.5 volume math corrected by F2 (GB thoroughbred-only ≈ 25–40 WIN/day holds ONLY with event-type scoping).
- Gate B SQL notes: `created_at` is ISO UTC (LIKE-on-day slices the UTC day — acceptable, note it); the shared-key query is weak while most AU rows have NULL country — rely on the `|cc` structural check + F4 census as the primary detectors.
- Lock 4 arming: GB rows usually carry blank state, so clause 1 rarely fires — the F1 catalogue-country cross-check and F4 census are the real tripwires; keep clause 2 (`|cc` structural) as written.
- Alias seed: add `bangor-on-dee` (hyphen sponsor-strip mangles it to `on-dee`; miss-only).
- 317 rows already carry `country` / 195 `local_race_date` (pre-stamped set observed in live DB 30 Jul) — migration must handle them like any other non-AU rows; not a special case.
