# W12.2 — Commission source + construction plumbing (Code brief)

**Status:** Locked, Session 143 (2026-06-10 ACST).
**Type:** Surgical-fix workstream. Single bounded Code session.
**Workstream:** W12.2 (bet-entry / balances sub-stream).
**Precedent shape:** W12.1 surgical brief
(`dr029/w12_balances/w12_1_lay_balance_brief.md`).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3/`

---

## §1 — What this brief is and is not

This brief commissions the two-piece W12.2 fix settled at
Session 142:

**(a) Commission source.** Port hedge-entry commission off the
static `_COMMISSION_TABLE` in `staking.py` onto Betfair's
per-market base rate (`marketBaseRate`), snapshotted onto the
bet record at entry. The DR-025 Session 139 amendment locked
this sourcing: Betfair's stated per-market rate is the single
source of truth; a flat 8% fallback applies when the rate
cannot be read; the static venue/track table is retired.
Because the v3 `betfair_client` does not yet surface
`marketBaseRate` on any read, piece (a) includes a
backward-compatible addition to the §9.7 market-catalogue read
per the contract's §14.4 additions mechanism.

**(b) Construction plumbing.** Wire the orchestrator so the
hedge construction reaches the bet record at entry —
`HedgeRecordInputs.construction` (added by W12.1, currently
never populated by the orchestrator) gets forwarded, so the
`side` tag populates on every new hedge record and the W12.1
lay-balance maths bites on new bets.

**This brief is not:**

- A change to the W12.1 balance-derivation maths, the lay
  branch, or the read-side 8% fallback — all shipped and
  verified; W12.2 feeds them, it does not modify them.
- The hedge-classification engine, the `hedge_state` column,
  or anything in W15 ops-log territory.
- A backfill of `commission` or `side` on existing bet rows.
  Existing rows keep NULL and the read-side fallbacks; only
  new entries populate.
- Account-level Betfair discount handling (`discountAllowed`)
  — out of scope per the DR-025 amendment and the v2
  precedent; the stated market base rate is what is stored.

Surprises become **findings** in the report, not blockers and
not silent scope expansion.

---

## §2 — Why this work exists

The DR-025 Session 139 amendment ruled that commission is
Betfair's per-market `marketBaseRate`, captured at hedge-entry
time, with an 8% fallback — explicitly *not* a static
venue/track lookup table, because v2's earlier table drifted
and silently misclassified markets (NSW/ACT thoroughbred and
NRL at wrong rates). The shipped W4 `staking.py` still carries
the static table; the W12.1 triage (Session 142) routed the
reconciliation here as W12.2 piece (a).

W12.1's report finding F§5.2 surfaced that new lay bets are
not tagged as lays at entry: `HedgeRecordInputs.construction`
exists and the record builder derives `side` from it, but the
orchestrator's `_hedge_inputs_from` never passes it, so every
new hedge record lands with `side=NULL` and reads as a back.
Today's behaviour is preserved-but-wrong-for-lays; the wire is
W12.2 piece (b).

Both pieces touch the same bet-entry flow
(`workflows/bet_entry/v1/`), so they land in one bounded Code
session per the Session 35 combine-related-fixes precedent.

---

## §3 — Pre-reads

Required, in order:

1. This brief.
2. `workflows/bet_entry/v1/staking.py` — the commission table
   and lookup being retired (§5.3 anchor).
3. `workflows/bet_entry/v1/orchestrator.py` —
   `HedgeEntryRequest` and `_hedge_inputs_from` (§5.4 anchor).
4. `workflows/bet_entry/v1/record_builder.py` —
   `HedgeRecordInputs` and the `commission=None` write site
   (§5.5 anchor); the W12.1 side-derivation block.
5. `clients/betfair_client/v1/market_catalogue.py` — the §9.7
   read being extended (§5.1 anchor).
6. `contracts/betfair_client_contract.md` §9.7 + §14.4 — the
   backward-compatible additions mechanism the §5.2 edit uses.
7. Rebuild `decisions.md` DR-025 **2026-05-22 Session 139
   amendment** — the commission-sourcing ruling and the v2
   precedent (`_get_commission_for_market` reads
   `description.marketBaseRate` per market, divides by 100).

Reference-only (read on demand):

- `clients/betfair_client/v1/_translation.py` — where the
  path-style endpoint maps to Betfair's JSON-RPC shape; the
  MARKET_DESCRIPTION projection lands here (§5.1).
- `domain/bets/__init__.py` — `Construction`, `BetSideTag`,
  `BetRecord.commission` (W12.1 fields).
- `store/schema/bets.py` — the `commission` column (W12.1;
  NULL → 8% read fallback).
- `dr029/w12_balances/w12_1_lay_balance_report.md` F§5.2 —
  the plumbing-gap finding behind piece (b).
- v2 `src/services/betfair_sync.py`
  (`/Users/tim/Desktop/Projects/bethub-v2/`) —
  `_get_commission_for_market`, the live-proven precedent.
  Read-only; v2 receives no modifications.

---

## §4 — System access

- **Mac filesystem, read-write**, limited to the named anchors
  in §5. Everything else read-only. v2 codebase read-only.
- **Python:** `.venv/bin/python` at the repo root — Python
  3.12 per DR-031. All `pytest` / `lint-imports` runs through
  the venv binaries.
- **No live databases.** All DB work is against temp/in-memory
  SQLite in tests.
- **No network access.** No live Betfair calls — the
  `marketBaseRate` field's availability is proven by v2's
  daily production use; tests exercise the parse path with
  canned payloads.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021.

---

## §5 — Substantive scope

Five anchors + tests. Two existing-file groups (client +
contract; bet-entry workflow) and no new modules.

### §5.1 — `clients/betfair_client/v1/market_catalogue.py` — surface `market_base_rate`

Backward-compatible field addition to the §9.7 read:

- `MarketCatalogue` gains
  `market_base_rate: float | None = None` — **decimal
  fraction** (e.g. `0.08`), normalised at parse from Betfair's
  percentage form (`description.marketBaseRate`, e.g. `8.0`,
  divided by 100 per the v2 precedent). Document the unit in
  the field's docstring/comment; the decimal-fraction form
  matches `HedgeStakeInput.commission_rate` and
  `BetRecord.commission` so no further conversion happens
  downstream.
- `_parse` reads the field tolerantly:
  `payload.get("market_base_rate")` (or the translated key the
  wire shape carries — see translation note below); absent or
  null → `None`. Absence is not an error.
- The path-style endpoint's wire shape is produced by the
  translation layer. Extend `_translation.py` (or wherever the
  §9.7 endpoint's projection list lives) so the underlying
  `listMarketCatalogue` call requests the
  `MARKET_DESCRIPTION` projection in addition to the existing
  four, and maps `description.marketBaseRate` → the catalogue
  payload's `market_base_rate` (performing the ÷100
  normalisation at exactly one place — the translation/parse
  boundary, not downstream). Code inspects the actual
  translation wiring and lands the change where the existing
  projection list lives; if the wiring differs materially from
  this description, implement the minimal equivalent and
  record the divergence as a finding.
- No other field, no other read surface, no version bump
  (additive per contract §14.4).

### §5.2 — `contracts/betfair_client_contract.md` — §9.7 addition note

Two edits, both additive:

- §9.7's return-shape listing gains the `market_base_rate`
  field with its unit (decimal fraction; `None` when Betfair
  omits the description block) and the MARKET_DESCRIPTION
  projection note.
- The changelog table gains a v1.3 row dated this session:
  backward-compatible addition per §14.4, naming W12.2 and the
  DR-025 S139 amendment as the driver. No existing surface
  changed; no consumer version bump.

### §5.3 — `workflows/bet_entry/v1/staking.py` — retire the static table

- Remove `_COMMISSION_TABLE`, `_SportFamily`,
  `CommissionLookupKey`, `resolve_commission`,
  `_classify_sport`, and `commission_lookup`. Grep confirms no
  production callers exist outside the package re-export in
  `workflows/bet_entry/v1/__init__.py` (which is updated in
  the same edit); the W4 tests covering the table are replaced
  per §5.6.
- Add `DEFAULT_COMMISSION_RATE: float = 0.08` (module-level
  constant; the DR-025 fallback, matching the W12.1 read-side
  fallback) and:

  ```python
  def commission_from_market_base_rate(
      market_base_rate: float | None,
  ) -> float:
      """DR-025 S139 amendment — Betfair's per-market rate
      is the source of truth; flat 8% fallback when the
      rate could not be read. Input and output are decimal
      fractions (the §9.7 surface normalises ÷100)."""
  ```

  Returning `market_base_rate` when it is not `None` and
  within `[0.0, 1.0)`, else `DEFAULT_COMMISSION_RATE`. A
  malformed out-of-range value falls back rather than raising
  — bet entry must not hard-fail on a bad metadata field; the
  record stores what was resolved (see §5.4).
- Update the module docstring's commission paragraph to the
  new sourcing (DR-025 S139 amendment reference; table-drift
  lesson).
- `HedgeStakeInput`, `compute_hedge_stake`,
  `breakeven_betfair_price`, and all hedge maths are
  untouched — commission remains an input resolved upstream.
- Update `workflows/bet_entry/v1/__init__.py` re-exports:
  remove the retired names, add the new function + constant.

### §5.4 — `workflows/bet_entry/v1/orchestrator.py` — request fields + forwarding

`HedgeEntryRequest` gains two optional fields:

- `commission_rate: float | None = None` — the decimal
  fraction resolved at modal time from the §9.7 catalogue's
  `market_base_rate` (via
  `commission_from_market_base_rate` upstream, or carried
  raw — the composition root / W17 modal decides; W12.2 only
  requires the request can carry it). `None` means
  "unresolved" and flows through to the record as NULL so the
  W12.1 read-side 8% fallback applies — do NOT coerce `None`
  to `0.08` at write time; NULL preserves the
  we-did-not-know signal.
- `construction: Construction | None = None` — the staking
  calculator's construction flowing through the modal.
  Model validator: when `construction` is not `None` it must
  agree with `side` (`LAY_AGAINST_BACK` ⇔ `side == "LAY"`;
  `BACK_AGAINST_BACK` ⇔ `side == "BACK"`); mismatch raises at
  request construction (programmer error, per the §5.6
  result-type doctrine exceptions carve-out).

`_hedge_inputs_from` forwards both into `HedgeRecordInputs`:

- `commission=request.commission_rate` (verbatim; may be
  `None`).
- `construction=` the request's construction **when supplied,
  else derived from `side`** (`"LAY"` →
  `Construction.LAY_AGAINST_BACK`, `"BACK"` →
  `Construction.BACK_AGAINST_BACK`). The derivation is total —
  `side` is a required request field — so every new hedge
  record gets a populated construction (and therefore a
  populated `side` tag via the W12.1 record-builder
  derivation) regardless of whether the caller passes
  `construction` explicitly. This closes F§5.2 operationally,
  not just structurally.

`_modal_data_snapshot` gains the two new fields (error-path
data preservation parity).

No other orchestrator behaviour changes: retry policy,
Trigger A/B, error paths, pre-flight all untouched.

### §5.5 — `workflows/bet_entry/v1/record_builder.py` — populate commission

- `HedgeRecordInputs` gains `commission: float | None = None`
  if the field does not already exist (W12.1 added
  `construction`; Code verifies whether it also added
  `commission` — the write site currently hardcodes
  `commission=None`).
- The hedge build path replaces the hardcoded
  `commission=None` with `commission=inputs.commission`, and
  the W12.1 deferred-next-brief comment is updated to name
  W12.2 as landed.
- The soft-book build path is untouched — commission is a
  Betfair-leg concept; soft-book records keep `None`.
- The W12.1 side-derivation block is untouched.

### §5.6 — Tests

Adjust/extend in place, mirroring each anchor:

- **Staking tests** — remove/replace the table-lookup tests
  (Ipswich 4%, family fallback, unknown-family raise) with
  `commission_from_market_base_rate` coverage: passthrough of
  a valid rate; `None` → 0.08; out-of-range (negative, ≥ 1.0)
  → 0.08. All `compute_hedge_stake` math tests untouched and
  green.
- **Catalogue tests** — `market_base_rate` parses when
  present (8.0-percent wire form → 0.08 if normalisation
  lands at parse; or decimal passthrough if it lands in
  translation — match the §5.1 implementation), absent →
  `None`. Existing §9.7 tests untouched.
- **Orchestrator tests** — `_hedge_inputs_from` forwards
  commission verbatim including `None`; construction
  derivation from side both ways; explicit construction
  honoured; side↔construction mismatch raises;
  `_modal_data_snapshot` carries the new fields.
- **Record-builder tests** — `commission` lands on the built
  hedge record; soft-book path stays `None`; existing W12.1
  side-derivation tests untouched and green.

---

## §6 — Sequencing within session

1. Pre-build alignment: `git status` snapshot, §7.1
   pre-baselines, read the anchors.
2. §5.1 client surface + §5.2 contract edits (no workflow
   dependencies).
3. §5.3 staking retirement + `__init__.py` re-exports.
4. §5.5 record builder (so the forwarding target exists).
5. §5.4 orchestrator request fields + forwarding.
6. §5.6 tests, full `pytest` + `lint-imports`.
7. §7.2 post-baselines + §7.3 spot-check + report.

If a different order is operationally cleaner mid-session,
Code may deviate with the reasoning recorded in the report.

---

## §7 — Empirical verification

### §7.1 — Pre-baselines (capture at session open)

- `git status --short` — full dirty-tree snapshot. Expected
  state includes the W10–W15 build region (untracked +
  modified) per §9; the W15 ops-log build landed 2026-06-10
  and is part of the baseline.
- `.venv/bin/pytest -q` — expected baseline **881 passed,
  2 failed** (the two pre-existing FB-inventory failures in
  `compute_free_bet_inventory`, carried since before W12.1;
  not W12.2's concern). Record actual counts.
- `.venv/bin/lint-imports` — expected 5 contracts kept,
  0 broken.

### §7.2 — Post-baselines (capture at session close)

- `.venv/bin/pytest -q` — green apart from the same two
  pre-existing failures; record the delta (net new passing
  tests from §5.6; zero new failures).
- `.venv/bin/lint-imports` — 5 kept, 0 broken.
- `git status --short` — delta vs §7.1 is EXACTLY the §5
  anchors (five named files + `workflows/bet_entry/v1/
  __init__.py` + the contract doc + test files). Nothing else
  moved.

### §7.3 — End-to-end spot-check

Through the orchestrator with the deterministic mock adapter
(W4 test harness pattern), place two hedges and inspect the
built records:

1. A LAY hedge with `commission_rate=0.05` and no explicit
   construction → record carries `commission=0.05`,
   `construction`-derived `side=LAY`; read-side balance
   derivation values it on the lay branch with c=0.05.
2. A BACK hedge with `commission_rate=None` → record carries
   `commission=NULL`, `side=BACK`; read-side derivation
   applies the 8% fallback.

Record the transcript (inputs, stored row fields, derived
liability/return figures) in the report.

---

## §8 — Output spec

Single report file:

`/Users/tim/Desktop/Projects/bethub-rebuild/dr029/w12_balances/
w12_2_commission_construction_report.md`

(one path — wrapped here for display width only).

Section structure: (1) session header + §7.1 pre-baselines;
(2) pre-build alignment; (3) what was built per §5 sub-section;
(4) §7.2 post-baselines + §7.3 spot-check transcript;
(5) findings (numbered f#N — observed / why it matters / no
remediation design); (6) self-assessment; (7) final
`git status --short`.

Length anticipation: 200–350 lines. The report does NOT
contain: recommendations, next-brief proposals, redesign
suggestions, or commentary on other workstreams.

---

## §9 — Hard limits (non-negotiable)

**Not in scope — do not build, do not touch:**

- W12.1 territory beyond the named anchors: no changes to
  `balance_derivation.py`, the lay maths, the read-side 8%
  fallback, `bet_store_adapter.py`, or `store/schema/bets.py`
  (the `commission` column already exists).
- W15 / ops-log territory: nothing under `domain/ops`,
  `store/schema/ops.py`, `store/repositories/ops.py`,
  `workflows/ops/`.
- The hedge-classification engine, `hedge_state` column, Burst
  Review surface, settlement code.
- Data backfill: no UPDATE of existing bet rows; existing
  NULLs stay NULL.
- Betfair account-discount handling (`discountAllowed`).
- Other `betfair_client` surfaces beyond §9.7; no streaming
  changes; no new endpoints.
- The two pre-existing FB-inventory test failures — carried,
  not fixed here.
- Alembic / migration framework (DR-031 defers it).
- Refactors / tidy-ups in passing.

**Single bounded session.** If the work does not fit, stop at
a coherent boundary and record it as a finding —
partial-but-coherent beats complete-but-lost.

**No mid-session operator escalation.** Surprises become
report findings; Code runs end-to-end.

**Dirty-tree git discipline** (load-bearing — the entire
W10–W15 build region is untracked/modified; expected state,
not drift):

- No `git add`, `git commit`, `git stash`, `git restore`,
  `git checkout` (file-targeted), `git reset`.
- Read working-tree state at session start (§7.1).
- Edit only the §5 anchors. After each edit to a
  tracked-modified file, run `git diff <file>` to confirm only
  intended changes landed.
- At session close, `git status --short` per §7.2.

**Module boundaries (DR-030):** no new cross-boundary imports.
`workflows/` may import `domain` and `clients` surfaces it
already imports; `clients/` imports nothing from `workflows/`
or `store/`. `lint-imports` green is the mechanical check.

---

## §10 — What happens after Code's session

The next operator-Claude Chat session reads
`w12_2_commission_construction_report.md` and triages:

- Green and clean → W12.2 closes. From that point every new
  hedge entry stores Betfair's true per-market commission and
  its back/lay tag, and the W12.1 lay-balance maths is live on
  new bets end-to-end.
- Findings → triage; decide whether a W12.2.x follow-up is
  warranted.
- The modal/UI wiring that resolves `commission_rate` from
  the catalogue read at modal-open time, and passes the
  staking construction through, lands with the racing screens
  (W17) — the request fields shipped here are its landing
  pads. Code does NOT write that brief.

---

## §11 — Cross-references

- **Decision:** DR-025 2026-05-22 Session 139 amendment
  (`decisions.md`) — commission sourcing ruling
  (`marketBaseRate`, 8% fallback, table retired) and the
  lay-substrate framing; DR-026 / architecture.md §A.10
  (Betfair canonical for market facts).
- **DRs invoked:** DR-019 (derive-on-read — liability still
  derived, never stored), DR-030 (module boundaries), DR-031
  (tech stack), DR-032 (canonical bet record), DR-021
  (Adelaide timestamps).
- **Prior artefacts:**
  `dr029/w12_balances/w12_1_lay_balance_report.md` (F§5.2 —
  the plumbing gap; the commission column + read fallback);
  `dr029/w12_balances/w12_1_lay_balance_brief.md` (precedent
  shape); `sessions/SESSION_142.md` (scope settlement);
  v2 `betfair_sync._get_commission_for_market` (live-proven
  sourcing precedent).
- **Contract:** `contracts/betfair_client_contract.md` §9.7
  (catalogue read), §14.4 (backward-compatible additions —
  the mechanism §5.1/§5.2 use).
- **Excluded items (tracked elsewhere):** classifier engine +
  `hedge_state` column (DR-025 sequencing point (c), W8/W17
  surfaces); FB-inventory test failures (open item, low
  priority); Alembic (sequenced after W12 + W15); W17 modal
  wiring (the consumer of the request fields shipped here).

**End of brief.**
