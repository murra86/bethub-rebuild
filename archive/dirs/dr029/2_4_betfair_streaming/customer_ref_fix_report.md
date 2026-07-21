# Report — Betfair customer-reference fix (Option B: decouple, schema-less)

**Executed:** 2026-06-18 19:52 ACST (Adelaide-local, DR-021)
**Brief:** `dr029/2_4_betfair_streaming/customer_ref_fix_brief_v2.md`
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`) — READ-WRITE,
named anchors only, dirty/in-flight tree (Session 35/36 discipline).
**Decision enacted:** Option B (decouple), schema-less form — operator's call
on the impact-review evidence, 2026-06-18.
**Status:** **code-complete.** The live $5 lay is the remaining operator gate
(see §8).

---

## §1 — Working-tree attestation (start vs end)

No git mutation was performed — no `add` / `commit` / `stash` / `restore` /
`checkout` / `reset`. State read at session start and close with
`git status --porcelain` / `git diff`.

| | Start | End |
|---|---|---|
| Branch | `main` | `main` |
| Dirty entries (`git status --porcelain` lines) | **61** | **62** |

**The single delta is the one §5.2-authorised new file:**

```
?? clients/betfair_client/v1/_customer_ref.py
```

Every other change landed **inside files/dirs already dirty at start**, so it
created no new top-level `git status` entry:

- `clients/betfair_client/v1/_translation.py` — already ` M` at start; my §5.4
  guard is an isolated addition within it (diff verified — see §4 / §5.4).
- `ui/api/routers/racing.py`, `workflows/bet_entry/v1/orchestrator.py`,
  `tests/ui/api/test_racing.py`,
  `tests/workflows/bet_entry/v1/test_orchestrator.py`,
  `tests/workflows/promos/v1/test_fb_deployment.py` — all sit under
  directories already untracked (`??`) at start (`ui/api/`,
  `workflows/bet_entry/v1/`, `tests/ui/`, `tests/workflows/`), so edits are
  subsumed under the existing `??` dir entries.

**Do-not-touch confirmations:**
- `.importlinter` — still ` M` with the **same** 24-insertion pre-existing
  diff as at start; **not edited** by this session (verified byte-identical
  via `git diff --stat`).
- `clients/betfair_client/v1/placement.py` — remains its **pre-existing** ` M`;
  **never opened for edit** this session. The bet-safety gate lives here and is
  byte-for-byte preserved (§6).
- No schema file under `store/` touched; no migration added.

Close condition from brief §4 met: *same dirty set as start + only the file
§5 authorises.*

---

## §2 — What was changed (summary)

Four code changes in dependency order + tests, exactly per brief §5:

1. **§5.1** — lay route's internal `bet_id` cleaned from `bet-record-{uuid4}`
   (47) to canonical `bet-{uuid4}` (40).
2. **§5.2** — a dedicated ≤32 Betfair reference (`bh-{26hex}`, 29) is minted by
   one shared helper and used at **both** placement sites; the reference is
   now decoupled from `bet_id`.
3. **§5.3** — a `StrategyTag → ≤15` boundary map at the lay route shortens the
   only breaching value (`synthetic_each_way`, 18 → `synth_ew`, 8); the stored
   enum / DB column stays full.
4. **§5.4** — a client-side length guard in the placement funnel raises a named
   error (not a silent Betfair 503) if any of the three references exceeds its
   cap.

---

## §3 — Per-anchor change summary (re-grounded by grep)

All four brief anchors were re-located by symbol/grep before editing — the
tree had moved since the brief was written. Re-grounded line numbers below.

### §5.1 — clean `bet_id` (lay route)

- **File / symbol:** `ui/api/routers/racing.py` · `place_lay` (re-grounded
  `racing.py:1018`; brief said `:981`).
- **Before:** `bet_id = body.bet_id or f"bet-record-{uuid4()}"`  (47)
- **After:** `bet_id = body.bet_id or f"bet-{uuid4()}"`  (40, canonical)
- A modal-supplied `body.bet_id` is still honoured unchanged. `bet_id` carries
  no Betfair cap (internal PK) — it was **de-`record-`'d, not shortened**.

### §5.2 — mint dedicated ≤32 Betfair reference (both sites)

- **Helper:** `clients/betfair_client/v1/_customer_ref.py` ·
  `make_betfair_customer_ref()` → `f"bh-{uuid4().hex[:26]}"` (29 chars).
- **Lay route** — `racing.py:1022/1031`: a `customer_ref` is minted once per
  request and passed as `customer_order_ref=customer_ref` (was
  `customer_order_ref=bet_id`). The lay route has **no internal retry**, so a
  single mint is correct (verified: `place_lay` calls `place_bet` once).
- **Hedge orchestrator** — `workflows/bet_entry/v1/orchestrator.py:746`
  (brief said `:743`): the fallback
  `request.customer_order_ref or f"bet-record-{uuid.uuid4()}"` became
  `request.customer_order_ref or make_betfair_customer_ref()`. The mint stays
  **once per logical order** (L741-748) and is threaded through every retry
  attempt (reused at the `_place_with_retry` sites, re-grounded L858/874/938) —
  threading unchanged, only the minted value changed.
- The now-unused `import uuid` in orchestrator was removed (it was used **only**
  by the replaced line; leaving it would fail `ruff` F401). Necessary
  consequence of the §5.2 edit, not drift.

### §5.3 — strategy reference ≤15 boundary map (lay route)

- **File / symbol:** `ui/api/routers/racing.py` ·
  `_BETFAIR_STRATEGY_REF_BY_TAG` + `_betfair_strategy_ref()`, applied at the
  lay route's `customer_strategy_ref=` (re-grounded `racing.py:1038`).
- Only the **lay route** sends a non-`None` strategy ref (the hedge path sends
  `None` — impact review §5.2), so the map lives there.
- The internal `strategy_tag=` argument (re-grounded `racing.py:1040`) is
  **unchanged** — it still passes the full enum value to the record/DB. Only
  the Betfair-bound `customer_strategy_ref` is mapped.

### §5.4 — client-side length guard (placement funnel)

- **File / symbol:** `clients/betfair_client/v1/_translation.py` ·
  `_build_place_orders_params` (re-grounded `:313`; the single funnel all
  placement paths pass through).
- Added named caps `_CUSTOMER_ORDER_REF_MAX=32`, `_CUSTOMER_REF_MAX=32`,
  `_CUSTOMER_STRATEGY_REF_MAX=15` and a `_guard_ref_length()` helper; the
  funnel validates all three references before returning. The returned param
  dict is **value-identical** to before (verified by `git diff` — see §5.4).

---

## §4 — Reference scheme, helper location, and import-linter finding

**Scheme (dev-lead call, brief §5.2):** `bh-{uuid4().hex[:26]}` = `bh-`
(BetHub, recognisable on the Betfair statement) + 26 hex = **29 chars**,
comfortably under the 32 cap, ~104 bits of entropy (collision-free at any
realistic volume).

**Helper location used:** a new module `clients/betfair_client/v1/_customer_ref.py`,
imported **directly** at both sites:
`from clients.betfair_client.v1._customer_ref import make_betfair_customer_ref`.

**Import-linter finding (none — a clean shared home exists):** under the
DR-030 layers, `clients` sits **below** both `ui` (the lay route) and
`workflows.bet_entry` (the hedge orchestrator), and both layers may import
`clients`. So no `.importlinter` change and no per-site duplication fallback
was needed. This placement mirrors the existing `_failure_diagnostics.py`
precedent (a private `_`-module in the same package, imported directly across
the boundary). **`uv run lint-imports` → 5 kept, 0 broken** after the change.
`.importlinter` was **not** edited.

---

## §5 — Details: map, guard, error type

### §5.3 — the strategy map as built

Exhaustive over the **actual** `StrategyTag` enum (`domain/bets/__init__.py:73`,
4 members). Existing values ≤15 are kept verbatim; only the breaching one is
shortened:

| StrategyTag | enum value | len | Betfair `customerStrategyRef` | len |
|---|---|---|---|---|
| `SAFETY_NET` | `safety_net` | 10 | `safety_net` | 10 |
| `PRICE_BOOSTER` | `price_booster` | 13 | `price_booster` | 13 |
| `SGM_CORRELATED` | `sgm_correlated` | 14 | `sgm_correlated` | 14 |
| `SYNTHETIC_EACH_WAY` | `synthetic_each_way` | **18** | `synth_ew` | **8** |

`_betfair_strategy_ref(None)` returns `None` (no strategy). An **unmapped**
tag raises `ValueError` (explicit, loud — never a silent over-length pass);
the §5.4 guard backstops it. The enum definition and `bets.strategy_tag`
column are untouched — **no migration**.

### §5.4 — the guard + error type

- **Error type:** `BetfairRestError` (from `clients/betfair_client/v1/_connection.py`)
  — the existing betfair-client error type, already raised in this same module
  for analogous bad-input-to-translation (`_translation.py:307`, unrecognised
  path). `_errors.py` was read per the brief: it maps `BetfairRestError` to the
  closed envelope reasons, so this is the right family to raise.
- **Behaviour:** raises (does **not** truncate). The message names the field,
  the cap, and the actual length, e.g.:
  `Betfair customerOrderRef exceeds its 32-char limit: got 51 chars ('bet-record-…')`.
- **Diff isolation (dirty file):** `_translation.py` was already ` M` with
  pre-existing in-flight W17.1 work. `git diff` confirms my hunk is confined to
  the cap constants + `_guard_ref_length` + the `_build_place_orders_params`
  body, and that the returned `placeOrders` params are **value-identical** to
  before (same `customerOrderRef` / `customerStrategyRef` / `customerRef`
  sources). No pre-existing hunk was disturbed.

---

## §6 — Bet-safety gate (preserved)

`placement.py` was **not opened** this session. The fix changes only the
reference string, the `bet_id` format, the strategy code, and adds a read-only
length guard. Stake, price, liability, and the gate that has refused every lay
across 5 live runs are byte-for-byte untouched. The streaming-disconnect
write pre-check (§13.1) and the bet-safety refusal are unchanged. The "no bet
placed" property remains true through this fix.

---

## §7 — Empirical verification (pre / post)

### Pre-state (grep + arithmetic confirmed)

- Lay route emitted `bet-record-{uuid4}` = **47** chars → breaches 32.
- Hedge orchestrator emitted `bet-record-{uuid4}` = **47** chars → breaches 32.
- Canonical `bet-{uuid4}` = 40 (internal PK, no cap).
- Strategy `synthetic_each_way` = **18** chars → breaches 15.
- **No client-side length guard** anywhere on these refs (the only
  `max_length` hits in-tree are unrelated promo/cash-flow Pydantic field
  validators).

### Post-state (executed against the live code)

- **Minted ref, both sites** (`make_betfair_customer_ref()`):
  `bh-c9fac7ce30aa4600ae41c0545b` … each **len = 29 ≤ 32**.
- **Strategy codes:** every `StrategyTag` ≤ 15 (table §5.3);
  `synthetic_each_way → synth_ew` (8).
- **Guard raises** on synthetic over-length input:
  - `customerOrderRef` 51 → `BetfairRestError: … exceeds its 32-char limit: got 51 chars`.
  - `customerStrategyRef` 18 → `BetfairRestError: … exceeds its 15-char limit: got 18 chars`.
- **`bet_id` latent-bug fix exercised:** the lay route's stored `bet_id` is the
  canonical `bet-{uuid4}` (40) and `_safe_uuid` / `_coerce_uuid` now recover
  the real UUID from it (the 47-char form did not — impact review §5.4).

### Test changes + suite counts

Baseline established empirically at session start (not hard-coded):

| | Command | Result |
|---|---|---|
| Before | `uv run pytest -q` | **1018 passed, 0 failed** |
| After | `uv run pytest -q` | **1028 passed, 0 failed** |

**Delta = +10, fully accounted (all additions; zero regressions):**

- `tests/workflows/bet_entry/v1/test_orchestrator.py`: **+1** —
  `test_auto_minted_customer_order_ref_is_stable_across_retry` (minted once,
  reused across a retry cycle). Plus **1 updated** (not a count change):
  `test_customer_order_ref_auto_generated` re-grounded from
  `startswith("bet-record-")` to `bh-` / `≤32`.
- `tests/clients/betfair_client/v1/test_translation.py`: **+5** — helper shape
  + uniqueness; legal refs pass; guard raises for over-length
  `customerOrderRef`; guard raises for over-length `customerStrategyRef`; guard
  helper names each of the three fields (covers `customerRef`).
- `tests/ui/api/test_racing.py`: **+3** — lay mints a ≤32 `bh-` ref decoupled
  from a clean 40-char `bet_id` (+ `_safe_uuid` recovery); lay maps
  `synthetic_each_way → synth_ew ≤15` end-to-end; strategy map ≤15 for **every**
  `StrategyTag`.
- `tests/workflows/promos/v1/test_fb_deployment.py`: **+1** — `_coerce_uuid`
  recovers the real UUID from a clean `bet-{uuid4}` (the latent-bug fix,
  exercised not assumed).

`1018 + 10 = 1028`. The two pre-existing `TranslatingTransport`/format tests
that asserted on **supplied** refs (`bet-record-uuid-12345`,
`bet-record-fixed-ref-9999`, both ≤32) were left unchanged — they test
round-trip of a caller-supplied value, which still holds.

### Quality gates

- **`uv run lint-imports` → 5 kept, 0 broken** (DR-030 contracts intact).
- **`ruff check`** is **clean on every file I authored or cleanly own**
  (`_customer_ref.py`, `_translation.py`, `test_translation.py`). Pre-existing
  `ruff` debt remains in the untracked in-flight WIP files
  (`ui/api/routers/racing.py`, `workflows/bet_entry/v1/orchestrator.py`, and
  their test files): unused imports, `E402` from a mid-import module constant,
  `I001` import-ordering on lines I did not add. Verified via
  `ruff check --diff` that each remaining `I001`/`F401` falls on **pre-existing
  lines**, never on my additions — see §9 finding F1. Fixing that debt would be
  out-of-anchor drift, so it was left.

---

## §8 — The remaining operator gate (carve-out)

This fix is **code-complete**. The one check Code cannot run is the live $5 lay
actually placing against live Betfair — an **operator-side** action, out of
Code's scope. **The live $5 lay is the remaining operator gate.** With both
placement sites now emitting a Betfair-legal (≤32) reference and the strategy
ref ≤15, the S162 `INVALID_INPUT_DATA — customerRef … 32 character limit` 503
should no longer fire. Code does not run the live lay and does not write the
next artefact (brief §10).

---

## §9 — Findings

- **F1 — pre-existing `ruff` debt in untracked in-flight files (NOT fixed —
  out of anchor scope).** `ui/api/routers/racing.py` and
  `workflows/bet_entry/v1/orchestrator.py` are brand-new untracked WIP files
  carrying unused imports, `E402` (a module-level `_IDEMPOTENCY_NAMESPACE`
  constant sits mid-import in `racing.py`), and `I001` import-ordering issues
  that predate this session. `ruff check --diff` confirms every remaining
  finding is on a pre-existing line, not on any line I added; the one `I001`
  my edit *did* introduce (in `test_translation.py`) was fixed. Cleaning the
  rest is for whichever session owns those in-flight files.
- **F2 — `customerRef` cannot diverge from `customerOrderRef` in the funnel.**
  v3 sets `customerRef = customer_order_ref` (same value). The guard still
  validates all three fields independently (so the `customerRef` cap is
  enforced and named), but an over-long order ref trips the `customerOrderRef`
  guard first. The `customerRef` field-named branch is covered by a direct
  `_guard_ref_length` unit test rather than via the funnel.
- **F3 — helper kept private (`_customer_ref`), imported directly.** Not
  re-exported via the package `__init__.py`, to avoid editing a pre-existing
  ` M` non-anchor file. Matches the `_failure_diagnostics` precedent.

---

## §10 — Hard-limits self-assessment

- **No schema change** — no column, no migration. ✓
- **Named anchors only** — the four §5 changes + their tests; the sole new file
  is the §5.2-authorised helper. ✓
- **No git mutation.** ✓
- **`_coerce_uuid` / `_safe_uuid` not refactored** — they self-healed once
  `bet_id` was cleaned (proven by tests). ✓
- **Soft-book `log_bet` path untouched** (`racing.py` `log_bet`, the `bet-` +
  `uuid5` derivation — out of the lay path). ✓
- **`.importlinter` not edited; no layering violation** (5 kept, 0 broken). ✓
- **Bet-safety gate byte-for-byte preserved** — `placement.py` never opened. ✓
- **No scope creep** into other §2.x items, broader `bet_id` harmonisation,
  sports (W18), or cutover (W16). ✓
- **Single bounded session** — completed end-to-end. ✓
- Adelaide-local timestamps (DR-021). ✓

---

## §11 — Cross-references

- **Brief:** `customer_ref_fix_brief_v2.md` (this report's spec).
- **Grounding:** `customer_ref_impact_review_report.md` (every anchor traces to
  it).
- **Prior diagnostic:** `placement_failure_diagnostic_report.md` (S162, named
  the `customerRef` 503).
- **DRs:** DR-021 (Adelaide-local timestamps), DR-030 (layered architecture).
- **Decision enacted:** Option B (decouple), schema-less — operator's call,
  2026-06-18.

*End of report.*
