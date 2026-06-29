# Account-id format normalization (F2 fix) — report

**Session:** single bounded Claude Code session, 2026-06-23 (Adelaide
local, ACST). Start ~23:36 ACST, close ~23:58 ACST.
**Brief:** `interface_triage/account_id_normalization_brief.md` (LOCKED
S183). **Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main`
(HEAD `2329604`, unchanged at close).

**Outcome (read first).** The **F2 write defect is fixed and proven**: a
credit (and a deploy) event written against a real, router-created
(`uuid4().hex`) account now **succeeds** with `foreign_keys = ON`, the
reference is stored verbatim in the operational format, and the pool
fills. The named-anchor work (§5.1–§5.5) is complete and the **promo
spine is green** (112 passed) including a new FK regression guard.

**BUT — this is partial-but-coherent, not all-green.** The spine retype
surfaced that two **read-path callers outside the named anchors** —
`workflows/balances/v1/balance_derivation.py` and the
`ui/api/routers/racing.py` `/log-context` endpoint — independently
re-normalize these three references through `UUID`. They are **not §5
anchors**; per §9 ("named anchors only") and §1 ("route remediation beyond
the named anchors to triage, don't chase"), I did **not** edit them. As a
result **10 read-path-caller tests regress**, and the production read /
pool-*display* path still needs the same str-treatment. This is the
headline finding (F-A) and needs a short follow-up brief.

---

## §1 — Baseline

- **HEAD:** `2329604` at start and close (no commit/checkout/reset).
- **Settlement seam:** `workflows/bet_entry/v1/settlement.py` SHA-256 at
  start **and** close:
  `9e07a75d3ab85741d5c3346521dbca25d09da632bd1140fcdb6550e55840d4a3` —
  **byte-identical**. Untouched (verified: `git diff` empty). No contact
  with `apply_manual_operator_resolution` / `provisional.py`.
- **Dirty tree:** 69 `git status` entries at start **and** close; HEAD
  unchanged. No git state-changing command run.
- **Tests:** `uv run pytest -q` **1180 passed** at start (Build 2 close).
- **F2 reproduced (baseline):** a credit write against a hex
  `account_at_book_id` with `foreign_keys = ON` raised
  **`PromoEventError - FOREIGN KEY constraint failed`** (captured).

---

## §2 — Per-change (every site the sweep touched)

### §5.1 — Domain retype (`domain/promos/__init__.py`)
- `PromoEventBase` **664–666**: `account_id` / `book_id` /
  `account_at_book_id` — `UUID | None = None` → **`str | None = None`**.
- `Promo` **776**: `book_id` — `UUID` → **`str`**.
- **Sweep result (this file):** exactly those four sites. The spine-owned
  ids alongside them (`event_id` 660, `parent_event_id` 667,
  `supersedes_event_id` 668, `correlation_id` 671; `Promo.promo_id` 774,
  `promo_template_id` 775) were left **`UUID`**, as required.

### §5.2 — Signature propagation
- `workflows/promos/v1/promo_derivations.py` — **8** annotation sites
  retyped `UUID` → `str`: `account_at_book_id` at 108, 155, 278, 293, 402,
  435; `book_id` at 401, 434. (Verified zero `…: UUID` ref annotations
  remain.)
- `workflows/promos/v1/promo_store_adapter.py` — method-signature params
  retyped `UUID` → `str`: `account_at_book_id` 164/240, `account_id`
  181/241, `book_id` 198/242/408.

### §5.3 — Adapter boundary pass-through (`promo_store_adapter.py`)
- **Write** (`_event_to_row`, ~702–708): dropped `str(event.account_id)` /
  `str(event.book_id)` / `str(event.account_at_book_id)` → store the str
  verbatim. (`event_id` / `parent_event_id` / `supersedes_event_id` keep
  `str(UUID)`.)
- **Read** (`_row_to_event`, ~670–676): dropped `UUID(row.account_id)` /
  `UUID(row.book_id)` / `UUID(row.account_at_book_id)` → return row text
  directly (None-guards retained). (`event_id` etc. keep `UUID(...)`.)
- **Line-537 nuance (real location reported):** the `str(event.account_at_book_id)`
  the brief cited "~537" is **not** in `_event_to_row` — it is in
  `_validate_payload_references`, the `accountcare_warning_cleared`
  **scope comparison**. Simplified to `current_scope = event.account_at_book_id`
  (a no-op `str()` removal; the comparison stays correct str-vs-str).
- **`Promo` mapping (propagation of §5.1's 776 change):** `_row_to_promo`
  dropped `UUID(row.book_id)` → `row.book_id`; `_promo_to_row` dropped
  `str(promo.book_id)` → `promo.book_id`. (`promo_id` / `promo_template_id`
  keep their UUID/str handling.)

### §5.4 — Credit write + deploy confirm
- `workflows/promos/v1/fb_credit.py` **184–186**: dropped
  `UUID(account_id)` / `UUID(book_id)` / `UUID(account_at_book_id)` → pass
  the strings through. (`event_id=uuid4()`, `triggering_*` UUIDs unchanged.)
- `workflows/promos/v1/fb_deployment.py` **158–160**: **confirmed no
  change needed** — it copies `credit_event.account_id` / `book_id` /
  `account_at_book_id` straight through; now `str`, they pass cleanly.

### §5.5 — Test seed migration + FK regression guard
- **To production hex (`uuid4().hex`), pure-promo tests:**
  `test_fb_credit.py` 37–39 (`A_ID`/`B_ID`/`AAB_ID`);
  `test_promos_credit_in.py` 37–39; `test_fb_deployment.py` 71–73
  (`uuid4()` → `uuid4().hex`); `test_promo_store_adapter.py` 82–84
  (`SEED_*` `.hex`) + 1308–1309 (`other_book`/`other_aab` `.hex`);
  `test_promo_derivations.py` 60–62 (`.hex`).
- **To dashed `str` (cross-domain promo+cash_flow tests — see F-B):**
  `test_balance_derivation.py` 62–68 (7 account/book/aab consts →
  `str(UUID(...))`; `PAYEE_ID` left UUID); `test_balance_lay_branch.py`
  55–57.
- **New regression test** (`test_fb_credit.py`):
  `test_f2_regression_hex_account_credit_holds_fk_and_fills_pool` — asserts
  the seed is dashless 32-char hex, the credit write succeeds under FK-on,
  the reference is stored **verbatim**, the pool fills, and a second call
  is idempotent. This is the guard that would have caught F2.

---

## §3 — Empirical verification (before / after)

| Check | Before | After |
|---|---|---|
| `settlement.py` SHA-256 | `9e07a75d…40d4a3` | **identical** |
| F2 write (hex account, FK on) | **`FOREIGN KEY constraint failed`** | **succeeds**, stored verbatim |
| Pool fills (inventory by hex aab) | n/a (write failed) | **`20.00`** |
| Deploy against hex account | latent FK risk | **writes, no FK failure** (pool drains to 0) |
| Promo spine + credit-in suites | 1180 baseline | **112 passed (green)** incl. new guard |
| Full `uv run pytest -q` | 1180 passed | **1171 passed, 10 failed** (read-path callers — F-A) |
| HEAD / `git status` count | `2329604` / 69 | **`2329604` / 69** |

The write/deploy/pool proof was captured directly (a credit + a deploy
against `uuid4().hex` accounts with `foreign_keys = ON`): credit
`credited` amount `20.00`, stored `account_at_book_id == hex` (True), pool
`20.00`, deploy wrote 1 event, pool then `0`.

---

## §4 — Findings / surprises

**F-A (headline) — the read-path derivation callers re-normalize the three
references and are OUTSIDE the named anchors.** The retype of
`compute_free_bet_inventory` (named anchor) surfaced two callers that pass
`UUID` objects, breaking against the now-`str` spine and (more importantly)
re-introducing the dashed mismatch on the **read / pool-display** path in
production:
- `workflows/balances/v1/balance_derivation.py` — `:512`
  `return [UUID(row[0]) for row in …]` wraps fetched account-at-book ids in
  `UUID`; its params/dataclass are `UUID`-typed (112, 128, 392, 496, 517,
  580, 589; `AccountAtBookBalance`). It feeds `compute_free_bet_inventory`.
- `ui/api/routers/racing.py` — `get_log_context` types the route param
  `account_at_book_id: UUID`, so FastAPI hands a `UUID` to the now-`str`
  inventory call.

**Consequence:** 10 tests regress (`test_balance_derivation` ×7,
`test_racing` ×2, `test_composition_root` ×1) — they exercise the
read/balance surface with these callers. **And** in production the racing
`/log-context` endpoint would `UUID`-parse a hex query param → `str(UUID)`
= dashed query → would **not** find a credit stored in hex (pool shows
empty even though the credit exists). **Both files are out of the §5
named anchors; per §9 I did not edit them, per §1 I flag rather than
chase.** A short follow-up brief should extend the str-treatment to these
two read-path callers so the pool *display* path also works against real
accounts. The F2 *write* defect — the literal F2 — is fully fixed.

**F-B — `domain/cash_flow` appears to share the pattern (unverified).**
The balance tests are cross-domain (promo + cash_flow). I migrated their
seeds to **dashed `str`**, not hex, precisely because cash_flow's event
types still take these references as `UUID` (out of this brief's scope) —
forcing hex there would re-dash on the cash_flow side and break its FK.
Whether cash_flow independently fails F2 on its production write path is
plausible (same `UUID`-typed-reference pattern) but I did **not** verify
it. Flagged for the follow-up.

**F-C — the §5.1 sweep, widened, found reference fields beyond
`domain/promos`.** The brief's §5.1 sweep was scoped to `domain/promos`
(done — 4 sites). Sweeping the wider spine surfaced the same `UUID`-typed
references in `balance_derivation.py` (F-A) — reported here, not chased.

**F-D — line-537 was a validation scope-check, not row serialization**
(handled as described; its real location named in §2/§5.3).

**F-E — balance-test seed format decision.** Cross-domain balance tests
kept **dashed `str`** (not hex) for cash_flow consistency (F-B); pure-promo
tests use **hex** (production format). Both are `str` (the type fix); the
format choice is per-test-domain and stated at each site.

---

## §5 — Files touched (complete)

**Production (Python — all named anchors):**
- `domain/promos/__init__.py` — §5.1 (4 sites).
- `workflows/promos/v1/promo_derivations.py` — §5.2 (8 sites).
- `workflows/promos/v1/promo_store_adapter.py` — §5.2 signatures + §5.3
  write/read boundary + line-537 + `Promo` mapping.
- `workflows/promos/v1/fb_credit.py` — §5.4 (3 sites).
- (`fb_deployment.py` — inspected, **no change needed**, confirmed.)

**Tests:**
- `tests/workflows/promos/v1/test_fb_credit.py` (hex seeds + **new FK
  regression test**), `test_promo_derivations.py`, `test_fb_deployment.py`,
  `test_promo_store_adapter.py` (hex); `tests/ui/api/test_promos_credit_in.py`
  (hex); `tests/workflows/balances/v1/test_balance_derivation.py`,
  `test_balance_lay_branch.py` (dashed `str`).

**Deliberately NOT touched (per §9):** `settlement.py` (SHA-proven),
`apply_manual_operator_resolution`, `provisional.py`; **`balance_derivation.py`,
`racing.py` (F-A — out of named anchors)**; `domain/cash_flow` (F-B);
`accounts.py` / the bets table / any schema / any persisted data.

---

## §6 — Self-assessment

- **Coverage:** §5.1–§5.5 complete at every named anchor; the sweep is
  reported exhaustively (4 domain + 8 derivation + adapter sites). The F2
  write defect is fixed and proven three ways (credit, deploy, pool fill)
  against real hex accounts, plus a permanent regression guard.
- **Confidence:** high that the **write defect** is fixed (direct proof +
  green spine) and that settlement is untouched (SHA identical). High that
  **F-A is real and blocking for the read/pool-display path** — it's the
  same root cause (UUID re-normalization → dashed) one layer up, proven by
  the 10 deterministic failures and the endpoint's `UUID` param type.
- **Not done / honest partial:** **the suite is not all-green** — 10
  read-path-caller tests regress because `balance_derivation.py` and the
  racing `/log-context` endpoint are **out of the named anchors** and
  re-normalize these refs. Per §9 (named anchors only) and §1 (flag, don't
  chase; "if it doesn't fit, that's a finding"), I did **not** edit them.
  This is a deliberate, brief-compliant partial: the named-scope deliverable
  is complete and green; the read-path coupling is escalated as F-A for a
  follow-up brief (≈2 files: retype the racing route param to `str` and
  stop `balance_derivation` wrapping fetched ids in `UUID` / retype its
  `AccountAtBookBalance` + params). cash_flow (F-B) was not verified.
- **Repo integrity:** HEAD unchanged; no `git add`/`commit`/`stash`/
  `restore`/`checkout`/`reset`; 69 git entries unchanged; `settlement.py`
  byte-identical (and `racing.py` / `balance_derivation.py` untouched); no
  schema, operational-store, or persisted-data change; no bet-id convention
  change. Adelaide timestamps throughout.

### Routes to the operator-Claude triage
- **F-A (do first):** a short follow-up to extend the str-treatment to the
  two read-path callers (`racing.py` `/log-context` param; `balance_derivation.py`
  `:512` + its `UUID`-typed params/`AccountAtBookBalance`) — this is what
  makes the credited free bet **visible** in the launched app against a
  real account, and turns the suite fully green.
- **F-B:** check whether `domain/cash_flow` has the identical write-path
  F2 against hex accounts.
