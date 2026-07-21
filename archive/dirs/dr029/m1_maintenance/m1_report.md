# M1 Report — Maintenance micro-bundle

Single Code session, end-to-end per the locked M1 brief. All seven
items delivered. Brief's expected close-state met:

- pytest **896 / 0** (was 894 / 2 at session start).
- `lint-imports` **5 contracts kept, 0 broken**.
- mypy on `workflows/bet_entry/v1/betfair_adapter.py` **0 errors**
  (was 15).
- Alembic adopted; `alembic upgrade head` against a fresh DB
  produces a schema identical to the legacy `apply_migrations` path
  (`sqlite_master` diff empty).

---

## §1 — Per-item delivery notes

### Item 1 — FB-inventory test time-bomb (clock freeze)

Pinned `REF_TIME = datetime(2026, 5, 18, 12, 0, tzinfo=ADL)` in both
named promo test files and added an autouse fixture that
monkeypatches `workflows.promos.v1.promo_derivations._now` to return
`REF_TIME`.

- `test_promo_derivations.py` — fixture added; five
  `datetime.now(tz=ADL)` calls (L314 / L326–327 / L349 / L377)
  rewritten as `REF_TIME + timedelta(...)`. REF_TIME was already
  2026-05-18 Adelaide.
- `test_promo_store_adapter.py` — fixture added; `_REF_TIME`
  advanced from `2026-05-13` to `2026-05-18` Adelaide; paired
  `utc_now` literal in the tz-rejection test moved with it.

Scope edge — see f#1.

### Item 2 — Stale docstring, balance derivation

`workflows/balances/v1/balance_derivation.py` L153–160:
`_DEFAULT_COMMISSION` docstring rewritten to present tense —
commission is populated at write time from the Betfair
`MarketBookResponse` (W12.2), the 0.08 constant is the read-side
fallback for legacy / edge NULL-commission rows. No code change.
Stale `_COMMISSION_TABLE` pointer updated to the live
`DEFAULT_COMMISSION_RATE`; see f#2.

### Item 3 — Stale docstring, lay-branch test

`tests/workflows/balances/v1/test_balance_lay_branch.py` L290–291:
docstring of `test_lay_win_null_commission_falls_back_to_eight_percent`
aligned with Item 2's framing, same pointer fix. No assertion
changes; test still green.

### Item 4 — Bets row-factory asymmetry (W15 f#2)

`store/schema/bets.py:88-89` — `_add_column_if_missing` rewritten to
positional access (`row[1]` against
`PRAGMA table_info`'s `(cid, name, type, notnull, dflt_value, pk)`
tuple), matching the pattern in `store/schema/{cash_flow,promos,ops,
accounts}.py`. The helper no longer depends on the caller having set
`conn.row_factory = sqlite3.Row`. A short docstring note records the
convention so future readers see it.

Brief's anchor reference was `store/repositories/bets.py` ~L475; the
actual W15 f#2 surface is the schema-side helper. The repository-side
pattern is internally consistent and was not touched — see f#3.

### Item 5 — `.importlinter` documentation note (W15 f#1)

Comment header added above `[importlinter]` documenting the DR-030
layered architecture and the deliberate partial membership of
`workflows-independent`. The note records that `workflows.balances`,
`workflows.cash_flow`, and `workflows.promos` are intentionally
omitted because DR-019's derivation-chain pattern (locked S124) has
`workflows.balances` reading both `workflows.cash_flow` and
`workflows.promos`. Contract definitions unchanged; lint-imports
still 5 / 0.

### Item 6 — `betfair_adapter.py` single-file mypy cleanup

15 → 0 errors via isinstance narrowing. No `# type: ignore`, no
envelope-model edits.

Read paths (L147 / L165 / L251 / L298 / L322 pre-edit): replaced
`if envelope.status == EnvelopeStatus.UNAVAILABLE:` with
`if isinstance(envelope, UnavailableReadEnvelope):`. mypy narrows
the union (`FreshEnvelope[T] | StaleEnvelope[T] |
UnavailableReadEnvelope`) on both branches without following the
enum tag.

Write path (`_envelope_to_placement_outcome`, L406 / L418 pre-edit):
`if isinstance(envelope, FreshEnvelope):` narrows the
`WriteEnvelope` union symmetrically.

Imports: `FreshEnvelope` and `UnavailableReadEnvelope` added (both
re-exported from `clients.betfair_client.v1`). `EnvelopeStatus`
became unused and was removed (ruff F401 flagged it). All 29
`test_betfair_adapter.py` cases still pass; ruff clean.

### Item 7 — Alembic adoption (DR-031 deferral closes)

Standard layout:

- `alembic.ini` at repo root (scaffolded via `alembic init
  migrations`, then customised).
- `migrations/` at repo root, sibling to `store/`:
  - `env.py` — URL resolution `BETHUB_DB_URL` env var →
    `-x url=...` CLI arg → `alembic.ini` fallback. `target_metadata
    = None` (no SQLAlchemy ORM model — DR-031 locks Core, not ORM
    — so autogenerate isn't wired; revisions are hand-authored
    against `store/schema/`).
  - `versions/0001_baseline.py` — thin wrapper, extracts the
    underlying DBAPI sqlite3 connection via
    `op.get_bind().connection.connection` and calls each
    `store.schema.*.apply_migrations` helper in FK order
    (accounts → bets → cash_flow → promos → ops). Schema DDL is
    NOT duplicated into the migration; `store/schema/` remains
    the readable source of truth. See f#4 for the autogen-path
    deviation.
  - `README.md` — developer flow + documented operator stamp
    path.
- `alembic.ini` fallback URL: `sqlite:///bethub.db`; production /
  operator flows pass `BETHUB_DB_URL`.

Zero schema changes ride along.

---

## §2 — Verification

### Pytest

| Point | Result |
|---|---|
| Pre-Item-1 baseline | **894 / 2** (`test_balance_free_bet_inventory_surfaces`, `test_inventory_single_freebie_available`) |
| Post-Item-1 | **896 / 0** |
| Post-session (after Items 1–7) | **896 / 0** in 3.68s |

### Mypy on `workflows/bet_entry/v1/betfair_adapter.py`

Before: `Found 15 errors in 1 file (checked 1 source file)`.
Errors clustered as 13 read-path `union-attr` (`.reason` / `.data`
on `FreshEnvelope | StaleEnvelope | UnavailableReadEnvelope`) + 2
write-path (`.data` access plus arg-type on
`FreshEnvelope[BetPlacementResult] | UnavailableWriteEnvelope`).

After: `Success: no issues found in 1 source file`. Ruff on the
same file: `All checks passed!`.

### Lint-imports

| Point | Files / deps | Contracts |
|---|---|---|
| Pre-session | 173 / 422 | 5 kept / 0 broken |
| Post-session | 173 / 424 | 5 kept / 0 broken |

(+2 deps because three test files now import
`workflows.promos.v1.promo_derivations` for the monkeypatch target.)

### Alembic schema-identity check

Built two scratch DBs in `/tmp` (never touched the operator's live
DB): one via `store.schema.*.apply_migrations`, one via
`alembic upgrade head` against a fresh empty DB. Compared
`SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE
'sqlite_%' AND name != 'alembic_version' ORDER BY type, name`.

```
legacy entries: 35
alembic entries: 35
SCHEMAS IDENTICAL
```

### Alembic stamp + idempotence

Stamp against a copy of the seeded fixture DB: succeeded;
`alembic_version` row inserted as `0001_baseline`. Bonus
idempotence check — `alembic upgrade head` against an UNSTAMPED
legacy-built copy: schema unchanged (CREATE IF NOT EXISTS plus
`_add_column_if_missing` are idempotent, baseline is a true no-op
against an already-shaped DB). The documented operator path
remains `stamp head`, not `upgrade head` — explicit about intent.

### Per-hard-limit attestations (brief §9)

- No W17 work touched (the W17 brief's anchors were not opened).
- No schema changes shipped (sqlite_master diff empty).
- No mypy work outside `betfair_adapter.py`.
- No edits to envelope models (`clients/betfair_client/v1/envelope.py`
  unchanged) or `.importlinter` contract definitions (only the
  comment header above `[importlinter]`).
- No v2 / VPS / capture.db / live-Betfair access.
- Zero `# type: ignore` added.
- Zero Alembic ops against the operator's live DB; all scratch DBs
  were `/tmp` paths and were removed at session close.
- Named anchors only, with one scope-edge documented (f#1).

---

## §3 — Findings

### f#1 — Item 1 scope edge: balance test file not in anchors

`tests/workflows/balances/v1/test_balance_derivation.py::test_balance_free_bet_inventory_surfaces`
(the second W15 f#4 carried failure) reaches
`compute_free_bet_inventory` transitively through
`compute_account_at_book_balance`. Without an analogous monkeypatch
in the balance test file's scope, the wall-clock-driven expiry
filter still fires; the suite would have closed at 895 / 1, not the
brief's stated 896 / 0.

Re-used the identical autouse fixture pattern in
`test_balance_derivation.py`. Zero other changes.

Triage: accept as-is (three identical autouse fixtures) or
consolidate into `tests/workflows/conftest.py`.

### f#2 — `_COMMISSION_TABLE` symbol no longer exists in `staking.py`

Items 2 and 3's pre-rewrite docstrings both referenced
`staking.py`'s `_COMMISSION_TABLE`. That symbol is gone — the
constant is now `DEFAULT_COMMISSION_RATE`. Updated both rewritten
docstrings to point at the live name as part of "rewrite the
docstring", since leaving a broken pointer in place would have
replaced a stale framing with a broken one.

Brief said "no code change" — that held; constant value unchanged.

### f#3 — Item 4 anchor pointed at repositories; actual surface was schema

Brief Item 4 referenced `store/repositories/bets.py` ~L475 as the
asymmetry locus, but the W15 f#2 surface is
`store/schema/bets.py:88-89` (`row["name"]` vs the positional
`row[1]` used by the four sibling schema helpers). Fixed the schema-
side helper per W15 f#2's wording.

The repository-side pattern (`conn.row_factory = sqlite3.Row` set at
connect-time in `store/repositories/{bets,accounts,cash_flow,ops,
promos}.py`) is internally consistent — every repository owns its
own connection's row-factory choice — and was not touched. The
repository-side `_row_to_*` helpers assume dict-style access; the
brief's "per-cursor preferred" direction would require deeper
changes that sit outside M1.

Triage: accept as-is or schedule a separate later brief to
normalise the repository-side pattern.

### f#4 — Alembic baseline path: helper re-use, not autogenerated DDL

Brief §5 / §7 named "autogenerate against the live model/DDL, then
hand-verify the emitted DDL matches `store/schema/`". v3 has no
SQLAlchemy ORM model (DR-031 locks Core, not ORM), so autogenerate
has no metadata to diff against.

Took the equivalent path: re-use `store.schema.*.apply_migrations`
as the baseline's body, verify empirically via `sqlite_master`
diff. Diff was empty (35 / 35 identical). The replacement strategy
preserves the brief's intent (baseline = current schema) and the
"store/schema/ remains readable source of truth" property even
better than a hand-copied DDL dump would have — the baseline is
structurally guaranteed to stay in sync with `store/schema/`.

Triage: accept the re-use-the-helpers shape as the going-forward
pattern, or schedule a switch to verbatim-DDL revisions if there's
a downstream reason to prefer that.

---

## §4 — Self-assessment

### Pacing

Bounded session, single pass. Items 1–6 ran straight; Item 7 took
the largest share of attention because of the SQLAlchemy-Core ↔
sqlite3 connection bridging (resolved by extracting the DBAPI
connection from `op.get_bind()` and passing it to the existing
schema helpers, preserving the readable source of truth).

### Sequencing deviations

None. Brief §6 sequence ran as specified: 1 → 2 → 3 → 4 → 5 → 6 →
7. Verification at item boundaries (full suite after Item 1, item-
local suites after Items 2–6, full suite + lint + mypy + Alembic
diffs at close).

### Judgement calls

Three, all in §3 findings:

1. Item 1 / balance test file (f#1) — added the same fixture to a
   file outside the brief's anchor list; required to meet the
   brief's stated 896 / 0 effect.
2. Items 2 / 3 / broken `_COMMISSION_TABLE` pointer (f#2) — updated
   the pointer rather than preserving a broken one through the
   rewrite.
3. Item 6 / unused `EnvelopeStatus` import — became unused after the
   isinstance migration, ruff (F401) flagged it, removed it. Treated
   as hygiene on the named anchor file, not a drive-by.

### Out-of-scope edges refused

- `.importlinter` `workflows-independent` membership: still three of
  six; the brief's Item 5 was documentation-only. Refused to extend
  membership.
- Repository-layer `row_factory` pattern: consistent across
  repositories, not the W15 f#2 surface — left untouched (see f#3).
- Project-wide mypy: not run; only the named anchor file.
- Alembic operations against the operator's live DB: not executed;
  the stamp path is documented in `migrations/README.md` for the
  operator.

### What the next chat session needs

- Decide on f#1: accept three identical autouse fixtures or
  consolidate into `tests/workflows/conftest.py`.
- Confirm **896 / 0** as the new standing pytest expectation in
  `current_state.md` per brief §10.
- Note DR-031 Alembic adoption as landed (the deferral closes).
- Confirm f#4's "re-use the schema helpers" baseline pattern is the
  going-forward shape for revisions.
