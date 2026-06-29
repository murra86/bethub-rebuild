# W12.1 — Lay-balance fix (Code brief)

**Status:** Locked, Session 140 (2026-05-26 PDT / 2026-05-27 ACST).
**Type:** Surgical fix. Single bounded Code session.
**Workstream:** W12.1 (balances sub-stream — read-side lay derivation).
**Precedent shape:** Sessions 35 / 36 surgical-fix briefs (named
anchors, dependency order, pre/post verification, dirty-tree
discipline).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3/`

---

## §1 — What this brief is and is not

This is a **surgical fix** to the W12 Location 1 balance
derivation so that Betfair **lay** bets compute the correct cash
effect. Today the derivation treats every bet as a back; a lay is
mis-valued because the win/loss cash flows are inverted and the
at-risk amount is the liability, not the stake.

The fix is small and contained:

- Store two new facts on the `bets` record: which **side** a
  Betfair bet is (lay or back), and a **commission** rate.
- Record the side at bet-entry time from the construction the
  staking calculator already computes.
- Add a **lay branch** to the read-side cash maths in the balance
  derivation, deriving liability on read per DR-019 (the
  derive-state-on-read decision — liability is never stored).

**This brief is not** the commission-source change. Where the
commission *value* comes from (Betfair's per-market base rate vs
the static table currently in `staking.py`) is a separate,
tracked item — see §9 hard limits and §10. This brief reads
commission with a sensible fallback and does **not** alter how
commission is produced.

Surprises become **findings** in the report, not blockers and not
silent scope expansion. If the lay branch turns out to touch more
of the derivation than the anchors named in §5, Code stops at the
boundary, implements what is named, and records the additional
surface as a finding for operator-Claude triage.

---

## §2 — Why this work exists

W12 shipped the balance read-side derivations (Location 1
account-at-book balance, Location 2 account-holder holding) clean.
Its report surfaced finding **b#4**: the derivation has no lay
branch, so any Betfair lay is valued as if it were a back. Session
138 routed the fix to a standalone sub-stream (W12.1); Session 139
revisited DR-025 (hedge classification), confirmed the six-state
model, and **locked the lay substrate**: two stored fields (side +
commission), with liability derived on read per DR-019. Session
139 also established that balance correctness depends only on this
two-field substrate — **not** on the hedge-classification state
machine — so W12.1 runs independently of W15 (the operations log).

This brief executes that locked decision.

---

## §3 — Pre-reads

Required, in order:

1. This brief.
2. `workflows/balances/v1/balance_derivation.py` — the edit target
   for the read-side fix (§5.5).
3. `store/schema/bets.py` — schema + inline-migration target
   (§5.1).
4. `domain/bets/__init__.py` — the `BetRecord` model, the
   `BetSideTag` / `Construction` enums, and the embedded math-review
   references (the lay-maths cross-check authority, §5.5/§7).

Reference-only (read on demand, not required up front):

- `store/repositories/bets.py` — persistence target (§5.3).
- `workflows/bet_entry/v1/record_builder.py` — side-population
  target (§5.4).
- `workflows/bet_entry/v1/staking.py` — where the construction and
  liability are already computed (`liability = s_bf × (p_bf − 1)`
  for Construction A); useful for the §5.4 side mapping and the §7
  cross-check.

---

## §4 — System access

- **Filesystem:** read-write on the v3 repo at
  `/Users/tim/Desktop/Projects/bethub-v3/`. Edits confined to the
  named anchors in §5.
- **Python:** use the repo venv — `.venv/bin/python` (Python
  3.12+, per DR-031 the locked tech stack). Run tests via the venv
  interpreter.
- **Database:** the fix changes derivation and schema code only.
  Any DB touched during testing is a throwaway test fixture, never
  a live operational store. Do **not** open, query, or modify any
  live `bethub.db` or `capture.db`.
- **Git:** the working tree is dirty and the entire W12 build is
  untracked. Strict dirty-tree discipline applies — see §9.
- **Timestamps:** any time-of-day reference in the report uses
  Adelaide local time (ACST/ACDT) per DR-021. (The operator's
  Vancouver display window is an operator-Claude-side override
  only; Code reports in Adelaide local.)

---

## §5 — Scope: the fix, anchor by anchor

Five code anchors plus tests. Each names the file, the function or
block, and the exact change. Edit only these.

### §5.1 — Schema: add `side` + `commission` columns

**File:** `store/schema/bets.py`

The `bets` table today has `book_or_exchange` but neither `side`
nor `commission` (confirmed). Add both, following the existing
W6 / W6.5 / W9 inline-migration pattern exactly:

1. In `_BETS_DDL`, add two columns to the `CREATE TABLE` body:
   - `side TEXT` — nullable; holds the `BetSideTag` value
     (`'BACK'` / `'LAY'`). NULL for any record where side was not
     recorded (treated as back on read — see §5.5).
   - `commission REAL` — nullable; the Betfair commission rate as a
     decimal fraction (e.g. `0.08`). NULL until the separate
     commission-source item populates it; read with a fallback
     (§5.5).
2. In `apply_migrations`, add two idempotent `_add_column_if_missing`
   calls (one per column), placed after the existing W9 call,
   each with a short comment tagging them `W12.1`.

No other schema change. Do **not** touch `bet_legs`, indexes, or
any other column.

### §5.2 — Domain: add `side` + `commission` to `BetRecord`

**File:** `domain/bets/__init__.py`

The `BetSideTag` enum (`BACK` / `LAY`) and `Construction` enum
already exist. The `BetRecord` model carries `book_or_exchange`
but no side or commission. Add two optional fields to `BetRecord`,
both backward-compatible (default `None`) so existing records and
existing construction call-sites keep working:

- `side: BetSideTag | None = None`
- `commission: float | None = None` — REAL-backed, mirroring the
  existing `matched_price` float handling in this codebase.

Backward-compatibility is load-bearing: the soft-book leg and any
historic record carry no side and must remain valid (`None`).

### §5.3 — Repository: persist + read back the two fields

**File:** `store/repositories/bets.py`

1. **INSERT** (the `INSERT INTO bets (...)` statement, ~L486–517):
   add `side` and `commission` to the column list and the
   corresponding bound parameters, sourced from the `BetRecord`
   fields added in §5.2. Persist `side` as its enum string value
   (`row.side.value if row.side is not None else None`); persist
   `commission` as the float (or `None`).
2. **Row → `BetRecord` mapping** (the read-mapping that
   reconstructs `BetRecord` from a `bets` row, ~L871): map the two
   new columns back onto the model fields, parsing `side` back into
   `BetSideTag` when non-NULL.

No change to any other repository method.

### §5.4 — Bet entry: record `side` from the known construction

**File:** `workflows/bet_entry/v1/record_builder.py`

`BetRecord` is constructed at ~L272 and ~L345. The staking
calculator has already resolved the `Construction` by this point
(`LAY_AGAINST_BACK` for Construction A, `BACK_AGAINST_BACK` for
Construction B). Set `side` on the **Betfair (hedge) leg** record
from that construction:

- `Construction.LAY_AGAINST_BACK` → `side = BetSideTag.LAY`
- `Construction.BACK_AGAINST_BACK` → `side = BetSideTag.BACK`

The soft-book leg is always a back by definition (math review §1 —
"soft-book lay does not exist as a soft-book product"); leave its
`side` as the default `None` (read as back). Do **not** set
`commission` here — commission population is the deferred item
(§9). Leave `commission` as `None`.

Identify the construction from whatever the record builder already
has in hand (the staking result / hedge input it builds from). If
the construction is **not** cleanly available at the construction
site without reaching outside the named anchor, stop, leave `side`
defaulting to `None`, and record this as a finding — do not thread
new plumbing through other modules to obtain it.

### §5.5 — Balances: the lay branch (the core fix)

**File:** `workflows/balances/v1/balance_derivation.py`

Four edits. Liability is **derived on read** per DR-019 — never
stored:

> **liability `L` = `matched_stake × (matched_price − 1)`**

**(a) `_read_bet_rows_for_account_at_book` (~L124).** Add `side`
and `commission` to the `SELECT` column list. Nothing else in the
query changes.

**(b) `_bet_cash_return` (~L151).** Add a lay branch. A row is a
lay when `side == 'LAY'`. Keep the existing back-bet logic exactly
as-is for every non-lay row. For a lay (cash; commission rate `c`,
with `c = 0.08` when `commission` is NULL):

- `settled_won` (the lay won — the backed selection lost):
  return `L + matched_stake × (1 − c)`
  (reserved liability returned, plus the backer's stake net of
  commission).
- `settled_lost` (the lay lost — the backed selection won):
  return `0` (liability forfeited).
- `voided`: return `L` (reserved liability returned).
- pending / provisional / None: return `0`.

Convert `commission` via `Decimal(str(...))`, mirroring the
existing `matched_price` handling.

**(c) `_bet_cash_stake_committed` (~L217).** For a lay, the cash
that leaves the account at placement is the **liability** `L`, not
the matched stake. Add a lay branch returning `L`; keep the
back-bet branch (`matched_stake`) and the free-bet branch (`0`)
unchanged.

**(d) `_bet_pending_cash_stake` (~L202).** For a lay that is still
pending, the reserved cash is the **liability** `L`. Add a lay
branch returning `L` while pending; unchanged otherwise.

The loop in `compute_account_at_book_balance` (~L289–296) is
**unchanged** — it already does `cash -= committed; cash +=
return`. The committed/return split above is deliberately mirrored
on the back-bet structure so the net comes out right with no loop
change and **no double-counting**.

**Net-effect check (must hold for the §5.6 tests):**

- lay win: `−L + (L + S×(1−c))` = **`+ S×(1−c)`**
- lay loss: `−L + 0` = **`− L`**
- lay void: `−L + L` = **`0`**

(where `S = matched_stake`, `L = S × (matched_price − 1)`.)

**Two guard conditions, surfaced as findings if hit:**

1. **`settlement_state` perspective.** The lay maths assumes
   `settled_won` means *the lay bet itself won* (consistent with
   how back bets record won/lost). If the settlement worker records
   a lay's `settlement_state` from the *backed selection's*
   perspective instead, the signs invert. Code confirms the
   recorded perspective (from `domain/bets` / the settlement path)
   and, if it cannot confirm it is the bet's own perspective,
   records this as a finding rather than guessing.
2. **`is_free_bet` + `side == 'LAY'`** is a contradiction (you
   cannot lay with a free bet). If any such row is encountered in
   testing, treat conservatively (return `0`, do not apply lay
   maths) and record as a finding.

**NULL side = back.** Any row with `side` NULL flows through the
existing back-bet logic unchanged — this preserves today's
behaviour exactly for every existing and non-lay record.

### §5.6 — Tests

The W12 build is tested (the balances workstream ships with unit
coverage; W13 shipped 753 tests). Add focused tests for the lay
branch — do not weaken or rewrite existing tests. Cover:

- Lay win, loss, void, and pending — each asserting the
  **net cash effect** from §5.5 against hand-computed values.
- Commission applied (e.g. `c = 0.08`, `c = 0.04`) and the
  **NULL-commission → 8% fallback** path.
- **NULL side → back behaviour unchanged** (a regression guard:
  an existing back-bet test case must produce an identical result
  with the new columns present-but-NULL).
- The §5.5 guard conditions (free-bet-marked lay → `0` + finding
  shape; verify the conservative path).
- A schema round-trip: persist a `BetRecord` with `side = LAY` and
  a commission, read it back via the repository, confirm both
  fields survive.
- Migration idempotency: `apply_migrations` run twice on the same
  connection is a no-op the second time (the `_add_column_if_missing`
  contract).

Use worked numbers Code can verify by hand (e.g. lay `$10` at
`3.0`, `c = 0.08`: `L = $20`; win → `+$9.20`; loss → `−$20`;
void → `$0`).

---

## §6 — Sequencing within session

Do the edits in dependency order:

1. **§5.1 schema** (columns must exist first).
2. **§5.2 domain** (`BetRecord` fields).
3. **§5.3 repository** (persist + read-back, depends on §5.2).
4. **§5.4 bet-entry side population** (depends on §5.2).
5. **§5.5 balance lay branch** (the core; depends on §5.1 columns
   being in the SELECT).
6. **§5.6 tests** (write alongside each edit or after §5.5; run the
   full suite at the end).

If a cleaner order surfaces, Code may deviate and note why. Run the
full test suite once at the end; capture pre-fix and post-fix
results (§7).

---

## §7 — Empirical verification

**Pre-fix baseline (capture before any edit):**

- Run the existing balances test suite; record pass/fail counts.
- `grep -nE "side|commission" store/schema/bets.py` to confirm
  both columns are absent at start (expected: zero functional
  matches in the DDL/migration).

**Post-fix verification:**

- Full test suite green, including the new §5.6 cases. Record the
  delta in test count.
- The net-effect identities in §5.5 hold in the new tests.
- The NULL-side regression guard passes (back-bet behaviour
  unchanged).
- **Cross-check the implemented lay maths against the `domain/bets`
  construction definitions and their math-review references**
  (Construction A liability = `s_bf × (p_bf − 1)`; the lay-win
  net = `S × (1 − c)`). State explicitly in the report whether the
  implementation matches the domain authority. **Any mismatch is a
  finding, not a silent reconciliation.**
- `git status` shows only the five named files modified (plus any
  new test file); no other working-tree change.

---

## §8 — Output spec

**Single file:** `dr029/w12_balances/w12_1_lay_balance_report.md`

Section structure:

1. **Summary** — what was changed, did the suite go green, headline
   net-effect confirmation.
2. **Per-anchor outcome** — one short subsection per §5 anchor
   (§5.1–§5.6): what changed, confirmation it landed.
3. **Verification** — pre/post test counts, the net-effect test
   results, the NULL-side regression result, the schema round-trip,
   migration idempotency.
4. **Cross-check result** — implemented maths vs `domain/bets`
   authority; match or mismatch stated plainly.
5. **Findings** — anything surfaced: the §5.5 guard conditions if
   hit, the §5.4 construction-availability outcome, any
   additional surface encountered, `settlement_state` perspective
   confirmation. If none, say "none".
6. **Self-assessment** — did the work fit one session; any anchor
   that ran larger than expected; length note.

Rough length: 150–350 lines. The report does **not** contain
recommendations, does **not** propose the commission-source change,
and does **not** carry scope into W15 or any other workstream.

---

## §9 — Hard limits (non-negotiable)

**Out of scope — name-and-exclude:**

- **Commission source.** Do **not** change where the commission
  value comes from. Do **not** wire `staking.py`'s
  `resolve_commission` / `_COMMISSION_TABLE` to populate the bet
  record, and do **not** introduce a Betfair `marketBaseRate`
  lookup. Commission is read with the 8% fallback only. The
  table-vs-Betfair-rate reconciliation is a separate tracked item.
- **Commission population at write.** `commission` stays `None` at
  write time in this brief. Only `side` is populated (§5.4).
- **The hedge-classification state machine.** No `hedge_state`
  column, no auto-classification flow (DR-025 / W15 territory).
- **W15 operations log** and every other workstream.
- **`bet_legs`, indexes, other schema.** Only the two named columns.
- **Alembic / migration framework.** Use the existing inline
  `_add_column_if_missing` pattern; Alembic adoption is a separate
  deferred brief (DR-031).
- **Refactors / tidy-ups in passing.** Named anchors only; no drift
  into adjacent code "while here".

**Single bounded session.** If the work does not fit one session,
that is a finding — partial-but-coherent beats complete-but-lost.

**Dirty-tree git discipline** (the entire W12 build is untracked;
the W12.1 anchors sit inside that untracked region — this is
expected, building on W12's output, not drift):

- No `git add`, `git commit`, `git stash`, `git restore`,
  `git checkout` (file-targeted), `git reset`.
- Read working-tree state at session start.
- Edit only the named anchors.
- After each edit, `git diff <file>` to confirm only intended
  changes landed.
- At session close, `git status` to confirm the dirty file list is
  unchanged apart from the five named files (+ new test file).

**Module boundaries (DR-030):** `store/` imports stdlib only;
`domain/` imports no `workflows`; `workflows/` may import `domain`
and `store`. The changes here add fields and reads within those
boundaries — introduce **no** new cross-boundary import.

---

## §10 — What happens after Code's session

The next operator-Claude session reads
`w12_1_lay_balance_report.md` and triages:

- If green and clean → W12.1 closes; the lay-side balance figure
  is now correct in structure (it computes correctly once `side` is
  recorded, which §5.4 wires up).
- If findings surfaced (`settlement_state` perspective,
  construction-availability, cross-check mismatch) → triage and
  decide whether a small W12.2 follow-up is warranted.
- The **commission-source reconciliation** (port `staking.py` off
  the static `_COMMISSION_TABLE` onto Betfair's per-market
  `marketBaseRate`, and snapshot `commission` onto the bet record
  at entry — the full landing of the Session 139 DR-025 decision)
  is its own brief, sequenced next. Code does **not** write that
  brief.

---

## §11 — Cross-references

- **Scope / decision:** DR-025 (hedge classification) + its Session
  139 amendment in `decisions.md` (lay substrate = side +
  commission; commission from Betfair per-market rate; liability
  derived on read).
- **DRs invoked:** DR-019 (derive-state-on-read — liability never
  stored), DR-032 (canonical bet record / `bet_legs`), DR-026 /
  architecture.md §A.10 (Betfair canonical for market facts incl.
  commission), DR-030 (module boundaries), DR-031 (tech stack;
  Python 3.12+; Alembic deferred), DR-021 (Adelaide-local
  timestamps).
- **Architecture:** §A.5 (Location 1 cash-balance formula), §A.6
  (per-bet derived cash return).
- **Prior artefacts:** `dr029/w12_balances/w12_balances_brief.md`
  and `w12_balances_report.md` (W12 + the b#4 lay-side finding);
  `sessions/SESSION_139.md` (the grounding, lay maths, dirty-tree
  state); `sessions/SESSION_138.md` (W12 ship + lay routing).
- **Excluded item (tracked):** commission-source reconciliation
  (track-table vs Betfair per-market rate) — separate brief, §10.

**End of brief.**
