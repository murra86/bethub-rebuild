# Build 1 — promo-attach foundation — build report

**Session:** single bounded Claude Code build, 2026-06-23 (Adelaide
local, ACST). Start ~18:45 ACST, close ~19:14 ACST.
**Brief:** `interface_triage/promo_attach_build1_brief.md` (LOCKED S180).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main` (HEAD
`2329604`, unchanged at close).
**Outcome:** all six §5 pieces built, tested green, end-to-end round-trip
confirmed on **both** entry paths. Zero regressions. Settlement seam
proven byte-identical. No work deferred for non-fit reasons — the §6
split point was not needed.

This report records what was found and done. It contains no
recommendations and names no next brief (per §8 / §10) — findings route
to the next operator-Claude triage session.

---

## §0 — Baseline

- **HEAD:** `2329604` at start and close (no commit/checkout/reset — the
  build is in the working tree).
- **Settlement seam (bet-safety gate):**
  `workflows/bet_entry/v1/settlement.py` SHA-256 at **start and close**:
  `9e07a75d3ab85741d5c3346521dbca25d09da632bd1140fcdb6550e55840d4a3`
  — **byte-identical**, matching the recorded hash (§5.6 / §7). Not
  touched, read or written.
- **Dirty tree (expected substrate, brief §4):** 69 `git status` entries
  at start; **69 at close** — no new top-level entries (every new file
  landed inside an already-untracked dir). 17 tracked-modified files at
  start (in-flight `betfair_client` work + `domain/bets/__init__.py`);
  the **only** one I edited is `domain/bets/__init__.py` (additive — 0
  deletions, §5.2). The other 16 were left byte-untouched.
- **Test baseline (Python `uv run pytest -q`):** the first full run after
  the schema/field edits showed 1158 collected (the pre-edit passing
  count, with the in-flight `betfair_client` tests already present). Final
  at close: **1166 passed, 0 failed, 4 warnings** (the 4 warnings are
  pre-existing `HTTP_422` / anyio deprecations). Net **+8 tests, 0
  regressions**.
- **Frontend:** `tsc -b` clean (exit 0); `vitest run` **16 files / 103
  tests, all passing** (no regressions; +0 net — two existing tests
  updated for the new required field/prop).
- **Read:** the four pre-reads (S179 review report + review brief +
  `store/schema/{promos,bets}.py`), plus the live-tree anchors verified in
  the pre-build confirmation. v2 read for requirements only
  (`promoPresets.js`, `database.py` promo columns, `betting.py` refund
  rule). **No DB inspected** beyond what the test suite + an in-memory
  smoke harness touch; no `capture.db`.

Order followed the §6 sequence (1 → 2 → 3 → 4 → 5 → 6); it held cleanly.
§5.5's backend was threaded alongside §5.4's (both are the same
record-builder surface), then both frontends, then the §5.6 tests.

---

## §5.1 — Structured terms on the promo catalogue

**Built.** Four **typed, nullable** columns added to `promo_template` via
the additive pattern — to `_PROMO_TEMPLATE_DDL` (fresh installs) **and**
matching `_add_column_if_missing` calls in `apply_migrations`
(`store/schema/promos.py`, the **first** such calls in that module):

- `refund_positions TEXT` — JSON int array (`[2]` / `[2,3]`).
- `return_type TEXT CHECK (return_type IN ('free_bet','cash'))`.
- `return_pct REAL` — fraction (`1.0` = 100%-back, `0.25` = 25%).
- `cap TEXT` — Decimal-as-string; analytics-only (no calc, §5.1).

The `return_type` CHECK is carried identically in the DDL and the
`_add_column_if_missing` definition string; on `ALTER TABLE ADD COLUMN` a
NULL value passes the CHECK (verified by test).

Threaded end-to-end through the catalogue persistence hop:

- **Domain** (`domain/promos/__init__.py`): `PromoTemplate` gains
  `refund_positions: list[int] | None`, `return_type: Literal['free_bet',
  'cash'] | None`, `return_pct: float | None`, `cap: Decimal | None`
  (all defaulted None). The free-form `default_terms` blob is **retained**
  but is no longer canonical for these four terms.
- **Row layer** (`store/repositories/promos.py`): `PromoTemplateRow` gains
  the four fields (as `str|str|float|str`, mirroring the columns), with
  `= None` defaults following the W12.1 `BetRow` `side`/`commission`
  precedent (this kept existing row constructions valid — see Findings
  F2). `create_row` INSERT, `update_row` (partial, None-keeps-existing),
  and `_row_to_promo_template_row` all carry them.
- **Adapter** (`workflows/promos/v1/promo_store_adapter.py`):
  `_template_to_row` serialises (`refund_positions` → JSON, `cap` →
  Decimal string), `_row_to_template` rehydrates (JSON → `list[int]`,
  string → `Decimal`), and `update_template` exposes the four as optional
  params. **The adapter CRUD stays fully functional** — it is the
  add-a-promo-later path (brief §5.1); not bypassed.

Verified: a catalogue row written through the adapter with all four typed
terms reads back identical (incl. `refund_positions` JSON and `cap`
Decimal); a row with all-null terms round-trips as null; re-running
`apply_migrations` is a no-op (idempotent).

## §5.2 — Serial + EV columns on `bets`

**Built.** Two additive **nullable** columns on `bets`
(`store/schema/bets.py`), following the W12.1 `side`/`commission`
precedent (in `_BETS_DDL` **and** `_add_column_if_missing`):

- `promo_template_id TEXT` — the promo serial (soft reference to
  `promo_template.promo_template_id`; **no inline FK**, matching `bets`'
  no-outbound-FK convention — confirmed only `bet_legs → bets` exists).
  Named `promo_template_id`, not `…_instance_id` (the DR-032 amendment
  made concrete — points at the catalogue serial; §11).
- `promo_ev_at_log REAL` — resolves S179 O1 (previously accepted by the
  API and dropped).

The **full persistence hop** was traced and round-trip-confirmed (the
brief flagged this path as named-from-signatures-but-not-traced):

`BetRecord` (`domain/bets/__init__.py`, +2 fields) → `to_rows` /
`from_rows` (`workflows/bet_entry/v1/bet_store_adapter.py`) → `BetRow`
(`store/repositories/bets.py`, +2 fields, defaulted) → `write_bet_record`
INSERT (column list + params) → `read_bet_record` `SELECT *` →
`_row_to_bet_row` → back to `BetRecord`.

Verified: a bet written with a serial + EV reads back with both identical;
a **plain bet (no promo) persists and reads back exactly as before, both
fields null** (null-tolerance end to end). `domain/bets/__init__.py` (the
one tracked-modified anchor) was edited **purely additively** — 0
deletions; my contribution is the promo block on top of the existing
whole-module authoring.

## §5.3 — Seed the catalogue from v2 + reconcile

**Built.** `scripts/seed_promos.py` reworked from 7 generic templates to
**9 v2-derived catalogue rows**, each with the four typed terms, via a
small `tpl(...)` helper. Stable `uuid5` slugs match the v2 preset ids
(`ins_25_fb_2nd`, … `boosted_odds`). The 5 warning-catalogue rows are
unchanged.

Reconciliation of the two prior representations (S179 O3), all resolved:

- **Kind enum canonical:** `boosted_odds` → `price_boost`.
- **Insured spots:** `'2nd'`/`'2nd_3rd'` → `refund_positions` `[2]`/`[2,3]`.
- **Return pct:** v2 percent (100 / 25) → fraction (`1.0` / `0.25`).
- **Cap:** v2 `promo_max_stake` → `cap` Decimal-string (`"25"`/`"50"`/null).

**The bare "Free Bet" preset is NOT a catalogue row** (the §5.3
reconciliation call — see Findings F1). It carries no refund terms; it is
a *deployment marker* (paying with a held free bet), handled by the bet's
existing `is_free_bet` path, not a promo offering. Decision taken: **no
catalogue row** (over a `kind='other'` null-terms row), so the catalogue
holds only genuine promo offerings; the picker offers "no promo" and the
existing free-bet toggle remains the deployment path.

Verified: a fresh seed writes 9 templates + 5 warnings; re-seed is
idempotent (9 existed, 0 written); the typed terms read back correct per
row; the bare free bet and the old `goodwill_free_bet` slug are both
absent.

## §5.4 — Race-screen path: catalogue-driven picker → serial on the bet

**Built.**

- **Read endpoint** (NEW `ui/api/routers/promos.py`, DR-030-placed):
  `GET /api/v1/promos/catalogue` → `list[PromoCatalogueItem]` (serial +
  name + kind + the four structured terms), reading via
  `PromoStoreAdapter.list_templates` over a per-request connection
  (override-able, mirroring `racing.py`). Registered in
  `ui/api/routers/__init__.py` + `ui/api/main.py` (minimal wiring). **Read
  surface only** — no write/CRUD endpoint (brief §9).
- **Picker is catalogue-driven:** `Racing.tsx` fetches the catalogue
  (`useQuery` → `fetchPromoCatalogue`, new `ui/web/src/api/promos.ts`) and
  passes the rows to `PromoBar`, which now renders a button per catalogue
  row (was the hard-coded `PROMO_PRESETS` array). Selecting a row builds
  the EV config via `buildConfigFromCatalogue` (`presets.ts`), which maps
  catalogue terms to the **same `PromoConfigState` shape the EV table
  already consumes** — converting `return_pct` fraction → percentage
  (the EV engine expects percent) and `refund_positions` → the
  `InsuredPositions` token. EV numbers are unchanged (the `cap`/`max_stake`
  does not affect the per-dollar EV — confirmed in `evEngine.ts`).
- **Serial on the bet at log:** `promo_template_id` threads
  `LogBetRequest` (`racing.py`) → `log_bet` → `SoftBookLogRequest`
  (`orchestrator.py`, the authorised expansion) → `_soft_book_inputs_from`
  → `SoftBookRecordInputs` (`record_builder.py`) →
  `build_soft_book_bet_record` → `BetRecord`. `promo_ev_at_log` (already
  on `LogBetRequest`, previously dropped) rides the same thread.
  `LogBetPanel.tsx` posts both (`promoTemplateId` from `promoConfig`).

Verified: the endpoint returns the seeded 9 with correct terms; the
orchestrator hand-off carries the serial + EV onto the `BetRecord`; the
null path (no promo) stays null.

## §5.5 — Log Past Bet path: promo picker → serial on the bet

**Built.** The manual path mirrors the race path:

- `ManualBetCreateRequest` (`ui/api/routers/bets.py`) + the endpoint's
  `ManualBetRecordInputs(...)` mapping carry `promo_template_id` +
  `promo_ev_at_log`; `ManualBetRecordInputs` + `build_manual_bet_record`
  (`record_builder.py`) persist both onto the bet.
- `LogPastBet.tsx` gains a **promo `<select>` reading the same catalogue
  endpoint** (`fetchPromoCatalogue`), defaulting to "– no promo"; the
  submit body sends `promo_template_id`. **`promo_ev_at_log` is left null
  on this path** — EV-at-log is not meaningful for an after-the-fact entry
  (Findings F3).
- `ui/web/src/api/bets.ts` `ManualBetCreateRequest` type carries both
  fields.

Both paths converge on the same two `bets` fields (§5.2) and the same
catalogue (§5.1). No new term representation introduced.

Verified (endpoint round-trip): a manual POST with a serial + EV persists
and reads back identical through the real storage; a plain manual POST
leaves both fields null.

## §5.6 — Tests + settlement-seam proof

- **Python:** `uv run pytest -q` → **1166 passed** (from 1158;
  **+8, 0 regressions**). New / updated coverage:
  - `tests/store/repositories/test_promos_schema.py` (+2): the four
    `promo_template` term columns present + idempotent on re-run; the
    `return_type` CHECK rejects out-of-set values, allows NULL.
  - `tests/scripts/test_seed_promos.py`: counts updated 7 → 9; kinds
    updated to the v2-derived names (incl. `boosted_odds` → `price_boost`,
    bare free bet absent); the `goodwill` round-trip test repurposed to a
    **typed-terms round-trip** (refund_positions / return_pct fraction /
    cap Decimal-string / return_type across insurance, bonus, boosted).
  - `tests/ui/api/test_promos.py` (NEW, 3): the catalogue endpoint returns
    the seeded set; an insurance row carries structured terms; each serial
    is a UUID.
  - `tests/ui/api/test_bets_manual_create.py` (+2): the manual path
    persists the serial + EV (read back via real storage); a no-promo bet
    leaves both null.
  - `tests/workflows/bet_entry/v1/test_record_builder.py` (+1): the
    race-path builder carries the serial + EV; null path stays null.
  - `test_promos_repository.py` needed **no edit** — the `BetRow`-style
    defaults (F2) absorbed the new fields.
- **Frontend:** `tsc -b` clean; `vitest run` 103/103. Two existing tests
  updated for the new required field/prop (`OddsTable.test.tsx` config
  literal; `LogBetPanel.test.tsx` `promoTemplateId` prop).
- **Settlement SHA:** byte-identical start → close (§0).

---

## §7 — Empirical verification (before / after)

- **Test baseline:** Python 1158 → **1166** (+8, 0 regressions);
  `tsc -b` clean; vitest 103/103.
- **Schema (`PRAGMA table_info`, after):** `promo_template` gained
  `refund_positions, return_type, return_pct, cap`; `bets` gained
  `promo_template_id, promo_ev_at_log`. Idempotent on re-run (no-op).
- **Catalogue:** 9 rows seeded + readable through the endpoint; a
  spot-checked insurance row (`Ins $50 FB 2+3`) returns
  `refund_positions=[2,3]`, `return_type=free_bet`, `return_pct=1.0`,
  `cap="50"`.
- **Round-trip:** one race-path bet (via the orchestrator hand-off) and
  one manual-path bet (via the endpoint, read back through real storage),
  each written with serial + EV and read back identical; plain bets null
  on both paths.
- **Settlement SHA:** `9e07a75d…` unchanged.

---

## §8 — Findings / surprises

**F1 — The bare "Free Bet" reconciliation call (§5.3, operator-relevant).**
The tenth v2 preset (bare free bet, all terms null) is **not** a catalogue
row. It is a deployment marker, not a promo offering with refund terms;
it maps to the bet's existing `is_free_bet` path. Chosen over a
`kind='other'` null-terms row so the catalogue holds only real offerings.
**UX consequence:** the race-screen picker no longer shows a "Free Bet"
button; the operator uses the existing `is_free_bet` toggle on the log
panel. Flagged for triage in case the operator wants a synthetic
"free bet / no promo" affordance restored.

**F2 — `PromoTemplateRow` new fields given `= None` defaults.** Following
the W12.1 `BetRow` `side`/`commission` precedent. This kept every existing
`PromoTemplateRow` construction (the repository test fixtures) valid with
**zero edits to `test_promos_repository.py`** — the additive-with-defaults
shape is exactly how W12.1 avoided churn. Field order: the defaulted
fields sit after the non-defaulted ones (dataclass rule); all
construction is keyword, so column/field order is unaffected.

**F3 — `promo_ev_at_log` is null on the manual path.** The race screen
computes an EV-at-log to stamp; Log Past Bet is after-the-fact, so there
is no meaningful EV-at-log to capture. The field is nullable and stays
null on the manual path — only `promo_template_id` is carried there. Race
path stamps both.

**F4 — `cap` is stored, never computed against (confirmed).**
`evEngine.ts` `evInsurance` takes `max_stake` but the per-dollar EV does
not use it ("max_stake does NOT" affect the rate), so sourcing the EV from
the catalogue's `cap` changes no number. `return_pct` is stored as a
fraction and converted to a percentage only at the frontend EV boundary
(`buildConfigFromCatalogue`), matching the engine's expectation. Consistent
with the brief's §5.1 "cap is analytics-only."

**F5 — Authorised named-anchor expansions used (as pre-cleared).**
`workflows/bet_entry/v1/orchestrator.py` (`SoftBookLogRequest` +
the `SoftBookRecordInputs` hand-off) and `store/repositories/bets.py`
(`BetRow` + INSERT/SELECT) were edited per the go. Two additional minimal
**wiring** edits were required to make the §5.4 read route live:
`ui/api/routers/__init__.py` (re-export) and `ui/api/main.py`
(`include_router`) — one import + one line each. Flagged as necessary
registration for the named route, not scope drift.

**F6 — `presets.ts` legacy symbols now unreferenced (dead code).** With
the picker catalogue-driven, `PROMO_PRESETS`, `buildConfigFromPreset`, and
`findPreset` have **no remaining importers** (grep-confirmed). They were
**retained, not deleted** — the brief made `presets.ts` "superseded as a
source of truth" but additive discipline + "no drift" argues against
removing exported symbols here. A later cleanup brief could drop them. The
`PromoPreset`/`PromoType`/`InsuredPositions` types remain in use.

**F7 — No `bets`-table FK on the serial (by design).** `promo_template_id`
is a soft reference (no inline FK), matching `bets`' existing convention.
A bet can therefore carry a serial whose catalogue row was later deleted;
acceptable for an append-mostly catalogue, but a note for any future
referential-integrity pass.

**Nothing was dropped for non-fit.** All six pieces completed with budget
to spare; the §6 split point (after §5.4) was not needed.

---

## §9 — Files touched (complete list)

**Production — Python:**
- `store/schema/promos.py` — §5.1 columns + migration calls.
- `domain/promos/__init__.py` — §5.1 `PromoTemplate` typed fields.
- `store/repositories/promos.py` — §5.1 `PromoTemplateRow` + INSERT /
  UPDATE / SELECT mapper.
- `workflows/promos/v1/promo_store_adapter.py` — §5.1 row↔domain
  serialise/rehydrate + `update_template` + `Decimal` import.
- `store/schema/bets.py` — §5.2 columns + migration calls.
- `domain/bets/__init__.py` — §5.2 `BetRecord` fields (tracked-modified;
  additive, 0 deletions).
- `store/repositories/bets.py` — §5.2 `BetRow` + INSERT/SELECT (authorised
  expansion).
- `workflows/bet_entry/v1/bet_store_adapter.py` — §5.2 `to_rows`/`from_rows`.
- `scripts/seed_promos.py` — §5.3 9-row reconciled seed + `Decimal` import.
- `ui/api/routers/promos.py` — **NEW** §5.4 read router.
- `ui/api/routers/__init__.py`, `ui/api/main.py` — §5.4 route registration.
- `ui/api/routers/racing.py` — §5.4 `LogBetRequest` + `log_bet` thread.
- `workflows/bet_entry/v1/orchestrator.py` — §5.4 `SoftBookLogRequest` +
  hand-off (authorised expansion).
- `workflows/bet_entry/v1/record_builder.py` — §5.4/§5.5
  `SoftBookRecordInputs` + `ManualBetRecordInputs` + both builders.
- `ui/api/routers/bets.py` — §5.5 `ManualBetCreateRequest` + endpoint map.

**Production — frontend:**
- `ui/web/src/api/promos.ts` — **NEW** §5.4 catalogue client.
- `ui/web/src/api/racing.ts`, `ui/web/src/api/bets.ts` — request types.
- `ui/web/src/promos/presets.ts` — §5.4 `promo_template_id` field +
  `buildConfigFromCatalogue` + mappers.
- `ui/web/src/components/PromoBar.tsx` — §5.4 catalogue-driven picker.
- `ui/web/src/components/LogBetPanel.tsx` — §5.4 `promoTemplateId` prop +
  POST.
- `ui/web/src/routes/Racing.tsx` — §5.4 catalogue query + wiring.
- `ui/web/src/routes/LogPastBet.tsx` — §5.5 promo picker + POST.

**Tests (new / modified):**
- `tests/store/repositories/test_promos_schema.py` (+2),
  `tests/scripts/test_seed_promos.py` (updated),
  `tests/ui/api/test_promos.py` (**new**),
  `tests/ui/api/test_bets_manual_create.py` (+2),
  `tests/workflows/bet_entry/v1/test_record_builder.py` (+1),
  `ui/web/src/components/OddsTable.test.tsx` (literal),
  `ui/web/src/components/LogBetPanel.test.tsx` (prop).

**Deliberately NOT touched:** `workflows/bet_entry/v1/settlement.py`
(seam, SHA-proven), `apply_manual_operator_resolution`,
`ui/api/routers/provisional.py`; no credit-in write, no "placed?" surface,
no idempotency/cycle-link work (all Build 2); no `capture.db` / placings.

---

## §10 — Self-assessment

- **Coverage:** all six §5 pieces built and verified with evidence; both
  entry paths persist + re-hydrate the serial and EV; the catalogue is
  reconciled to the v2 set and read through the live endpoint. Every claim
  above is backed by a test or an in-session round-trip.
- **Confidence:** high on the persistence (round-trips + 8 new tests +
  full-suite green), the migration idempotency, and the settlement-seam
  proof (SHA). High on the additive/null-tolerant invariant — a plain bet
  persists unchanged on both paths, tested. Medium-high on the frontend EV
  equivalence: I verified the config-shape mapping preserves the EV inputs
  and `tsc`/`vitest` are green, but I did **not** pixel-compare the EV
  table against the old hard-coded presets in a running browser (no app
  run this session — out of scope; the EV functions are unchanged and the
  config shape is identical).
- **Not traced exhaustively (honest gaps):** I did not run the live app /
  screenshot the picker; the frontend is verified by type-check + the
  existing vitest suite, not an interactive render. I added no new vitest
  test for the catalogue-driven `PromoBar` specifically (the brief's §5.6
  new-coverage list is Python; `tsc -b` + the existing component tests
  cover the TS contract) — a `PromoBar` render test is a reasonable future
  add. The pre-build Python baseline (1158) was taken from the first full
  run *after* the first edits and reconstructed (the 15 failures were all
  caused by the intended seed/row changes); I did not snapshot a clean
  pre-edit `pytest` run before touching files.
- **Partial-stop:** not needed — all six pieces fit one session.
- **Repo integrity:** HEAD unchanged; no `git add`/`commit`/`stash`/
  `restore`/`checkout`/`reset`; the only tracked file edited
  (`domain/bets/__init__.py`) changed purely additively (0 deletions);
  all other edits are within already-untracked dirs; `git status` entry
  count unchanged (69 → 69). `settlement.py` byte-identical. No DB written;
  no `capture.db` access. Adelaide timestamps throughout.
