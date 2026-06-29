# Brief — account-id format normalization (F2 fix)

**Status:** LOCKED — operator-approved 2026-06-23 (Session 183, ACST).
**Drafted:** 2026-06-23 (Session 183, Adelaide local / ACST).
**Type:** Surgical fix to a known integration defect (F2 from the Build 2
build report). Single bounded Claude Code session.
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main`
(HEAD `2329604` at the time of drafting — verify at start).

---

## §1 — What this brief is and is not

This brief commissions a single bounded Claude Code session to fix **F2**:
the promo-event log stores the operational store's account/book reference
ids in a different text format than the operational store itself, so a
credit (or deploy) event written against a real, router-created account
fails its foreign-key check.

The fix conforms the **one divergent layer** (the promo-event spine) to
the format the rest of the app already uses for these ids. It is a
type-and-serialization correction plus a test-format migration — **not** a
schema change, **not** an operational-store change, **not** a data
migration.

This is a surgical fix. Code edits **only** the named anchors in §5,
surfaces surprises as findings (not blockers), and routes any remediation
beyond the named anchors to the next operator-Claude triage rather than
chasing it. Single Code session; if the work does not fit, that is a
finding, not a continuation.

---

## §2 — Why this work exists

The Build 2 triage (Session 183) confirmed the credit-in write is correct
and bet-safe, but surfaced **F2** as a blocking integration gap:

- The operational store — the accounts router (`accounts.py`), the bets
  table (`store/repositories/bets.py`), and the operational domain types
  (`domain/bets`, `domain/accounts`) — stores `account_id`, `book_id`, and
  `account_at_book_id` as **dashless `uuid4().hex` TEXT**. This is the
  documented operational convention (`accounts.py` head docstring;
  `domain/accounts/__init__.py` notes `account_at_book_id` is TEXT matching
  the bets referent table).
- The promo-event spine (`domain/promos`, `workflows/promos`) types those
  same three reference fields as Python `UUID` and serializes them with
  `str(uuid)` on write → the **dashed** canonical form.
- Result: a credit event built from a real qualifier's hex
  `account_at_book_id` is stored dashed, which does not match the hex PK in
  `accounts_at_book`. With `PRAGMA foreign_keys = ON` (which the promo
  store adapter sets), the write raises `FOREIGN KEY constraint failed`.
  Proven empirically in the Build 2 session.

**Why it never bit before:** no production path ever wrote a credit (the
gap Build 2 closes), and the promo test-suite seeds accounts in dashed
`str(uuid4())` form — so the spine looks internally consistent in tests
while diverging from production. **The free-bet deploy path
(`fb_deployment.py`) carries the identical latent risk** — it copies the
account/book ids straight from the credit event, so it inherits the same
format mismatch. One fix at the spine boundary clears both.

---

## §3 — Pre-reads

Lean. Code reads, in order:

1. This brief.
2. `interface_triage/promo_attach_build2_report.md` — §8 finding **F2**
   (the empirical proof and scope note) and the §0 baseline (settlement
   SHA, test counts, HEAD).

Reference-only (read on demand, not required):

- `domain/promos/__init__.py` — the event domain types being retyped.
- `workflows/promos/v1/promo_store_adapter.py` — the serialization
  boundary.
- `interface_triage/promo_attach_build2_brief.md` — the locked Build 2
  contract (for the bet-safety and dirty-tree disciplines this brief
  inherits).

## §4 — System access

- **Mac filesystem, read-write to the v3 repo**, limited to the §5 named
  anchors. No edits outside them.
- **Live DB read-only** for the verification queries (§7), via
  `start_process` Python at the canonical path — never copy the DB file.
- **Tests run under `uv run pytest`** (the repo is a `uv` project; bare
  `python3 -m pytest` fails at collection). Frontend is **not** touched by
  this brief.
- **Dirty working tree is expected** (the uncommitted Build 1 + Build 2
  substrate — ~69 `git status` entries at HEAD `2329604`). Dirty-tree git
  discipline applies (§9). The §5 anchors are Python-only and do not
  intersect the frontend Build 2 work.
- **Adelaide local timestamps (ACST/ACDT) per DR-021** for every
  time-of-day reference in the report.

---

## §5 — Scope (the surgical changes, in dependency order)

The fix is one idea applied through one layer: **the promo-event spine
treats `account_id` / `book_id` / `account_at_book_id` as opaque TEXT in
the operational store's own format, never re-normalizing them through
Python `UUID`.** These three are foreign references into the operational
store; the operational store owns their format.

**Critical boundary (read before editing):** retype **only** these three
operational-store reference fields. The spine's **own** identities stay
`UUID` and are not touched — `event_id`, `promo_id`, `promo_template_id`,
`triggering_bet_id`, `triggering_promo_instance_id`, and every `*_event_id`
(`revoked_credit_event_id`, `expired_credit_event_id`,
`cleared_warning_event_id`, …). See §9 for the explicit do-not-touch list.

### §5.1 — Retype the three reference fields in the domain types

`domain/promos/__init__.py`:

- Lines **664–666** — `account_id` / `book_id` / `account_at_book_id`,
  currently `UUID | None = None` → `str | None = None`.
- Line **776** — `book_id: UUID` → `str` (verify it is the operational
  book reference, not a spine-owned id; it is a `book_id`, so it is a
  reference).
- **Sweep** the file for any other `account_id` / `book_id` /
  `account_at_book_id` typed `UUID`; retype each to `str`. Report every
  site changed.

### §5.2 — Propagate the str typing through the signatures

- `workflows/promos/v1/promo_derivations.py` — the `account_at_book_id` /
  `book_id` parameters at **108, 155, 278, 293, 401–402, 434–435** (and any
  others the sweep finds): `UUID` → `str`.
- `workflows/promos/v1/promo_store_adapter.py` — the same three reference
  parameters in the method signatures at **164, 181, 198, 240–242, 408**
  (and any others): `UUID` → `str`.

### §5.3 — Make the adapter boundary pass the text through unchanged

`workflows/promos/v1/promo_store_adapter.py` — at the DB boundary, stop
converting these three fields:

- **Write side** (currently `str(event.account_at_book_id)` at ~**537**,
  and `str(event.account_id)` / `str(event.book_id)` /
  `str(event.account_at_book_id)` at ~**702–705**): the values are already
  `str` after §5.1; store them directly, dropping the `str(...)` wrap (a
  `str(str)` is harmless but remove it for clarity, since the whole point
  is that no normalization happens here).
- **Read side** (currently `UUID(row.account_id)` / `UUID(row.book_id)` /
  `UUID(row.account_at_book_id)` at ~**670–673**): return the row text
  directly; drop the `UUID(...)` parse for these three fields. Keep the
  `None`-guards.
- Leave the `str(...)` / `UUID(...)` handling for the spine-owned id fields
  (`event_id`, `promo_*`, `triggering_*`, `*_event_id`) **exactly as is**.

### §5.4 — Drop the UUID wrap in the credit write

`workflows/promos/v1/fb_credit.py` — lines **184–186** currently wrap the
incoming hex strings: `account_id=UUID(account_id)`,
`book_id=UUID(book_id)`, `account_at_book_id=UUID(account_at_book_id)`.
Pass the strings straight through (`account_id=account_id`, etc.). The
function already receives them as the operational store's text.

`workflows/promos/v1/fb_deployment.py` — verify lines **158–160** (which
copy the three ids straight from the credit event) need **no change** once
the types are `str`; they already pass through. Report confirmation.

### §5.5 — Migrate the tests to the real production format + prove the FK

This is the anti-recurrence step. The spine tests currently seed accounts
in dashed `str(uuid4())` form, which is why F2 hid behind green tests.

- `tests/workflows/promos/v1/test_fb_credit.py` — the `A_ID` / `B_ID` /
  `AAB_ID` seeds at **37–39** (`str(uuid4())`) → **`uuid4().hex`** (the
  router's production format).
- Apply the same seed-format migration to the other promo-spine tests that
  seed account/book ids: `test_fb_deployment.py`, `test_promo_derivations.py`,
  `tests/ui/api/test_promos_credit_in.py`, and any others the sweep finds.
- **Add one new test** that exercises the credit write end-to-end against
  an `accounts_at_book` row created in the **router's hex format**, with
  `PRAGMA foreign_keys = ON`, and proves: the credit write succeeds (no
  `FOREIGN KEY constraint failed`), the credit is found by
  `compute_free_bet_inventory` (the pool fills), and a second call is
  idempotent. This test is the regression guard — it would have caught F2.
- If a cheap, explicit boundary assertion makes the format contract
  self-documenting (e.g. asserting these fields are `str` at the adapter
  write), add it; otherwise the real-format test is the guarantee. Code's
  call — report what was done.

---

## §6 — Sequencing within the session

Bottom-up, so the type change propagates cleanly and tests prove each
layer:

1. **§5.1** — retype the domain fields (the source of truth for the type).
2. **§5.2** — propagate the signatures (derivations, adapter).
3. **§5.3** — fix the adapter boundary (write/read pass-through).
4. **§5.4** — drop the credit-write wrap; confirm the deploy path.
5. **§5.5** — migrate the test seeds, add the FK regression test.
6. Run `uv run pytest -q` after the type+boundary changes (expect a small
   number of failures from the still-dashed test seeds — that is the
   divergence becoming visible), then after the test migration (expect
   green). Weave narrower runs through if helpful.

If a cleaner order emerges mid-session, Code may deviate and say so in the
report.

## §7 — Empirical verification (capture before and after)

**Before (baseline):**

- `settlement.py` SHA-256 (the bet-safety gate):
  `workflows/bet_entry/v1/settlement.py`. Record it.
- `uv run pytest -q` count (expected **1180** from the Build 2 close).
- **Reproduce F2**: a credit write against a hex-format
  `account_at_book_id` with `foreign_keys = ON` raises `FOREIGN KEY
  constraint failed`. Capture the raise.
- `git status` entry count + HEAD.

**After:**

- `settlement.py` SHA-256 — **byte-identical** to baseline (no contact).
- `uv run pytest -q` — green, at **1180 + the new test(s)**, 0 regressions.
- **F2 reproduction now passes**: the same credit write against a
  hex-format account **succeeds**, the FK holds, and
  `compute_free_bet_inventory` returns the credited amount (pool fills).
- Deploy path: confirm a deploy event against a hex-format account writes
  without the FK failure (the latent risk is closed too).
- `git status` count + HEAD **unchanged**; no git state-changing command
  run.

---

## §8 — Output spec

Single file: `interface_triage/account_id_normalization_report.md`.

Sections:

1. **Baseline** — settlement SHA, pytest count, HEAD, dirty-tree count,
   the F2 reproduction (the FK raise).
2. **Per-change** — §5.1–§5.5, each with the exact sites changed (every
   field/line the sweep touched, named).
3. **Empirical verification** — the before/after table from §7, including
   the FK-now-holds proof and the deploy-path confirmation.
4. **Findings / surprises** — anything the sweep surfaced beyond the named
   anchors (other UUID-typed reference fields, unexpected call sites),
   flagged for triage, not chased.
5. **Files touched** — complete list, production vs test.
6. **Self-assessment** — coverage, confidence, anything not done/not
   traced, repo integrity.

Rough length: **150–250 lines.** Over is fine if a finding earns it
(per the length-bends-to-detail rule); flag it in the self-assessment.
No recommendations beyond findings; no scope creep into other work.

## §9 — Hard limits (non-negotiable)

- **Settlement byte-identical.** No contact with `settlement.py`,
  `apply_manual_operator_resolution`, or `provisional.py`. SHA proven
  start and close.
- **Retype ONLY the three operational-store reference fields** —
  `account_id`, `book_id`, `account_at_book_id`. **Do NOT touch the
  spine's own UUID identities:** `event_id`, `promo_id`,
  `promo_template_id`, `triggering_bet_id`, `triggering_promo_instance_id`,
  `revoked_credit_event_id`, `expired_credit_event_id`,
  `cleared_warning_event_id`, and any other `*_event_id` / `promo_*`
  identity. These stay `UUID`.
- **No operational-store change.** Do **not** flip `accounts.py` to dashed
  ids; do **not** alter the bets table or any account/bet data; **no
  migration** of persisted rows. The operational store is the source of
  truth and stays as-is.
- **No schema change.** No column added/removed/retyped in any table.
- **No bet-id convention change** — the `bet-{uuid}` prefix and its
  `_coerce_uuid` handling stay exactly as they are.
- **No frontend, no settlement, no Piece B, no catalogue-UI** work.
- **Named anchors only** — no drift into adjacent code "while here."
- **Dirty-tree git discipline:** no `git add` / `commit` / `stash` /
  `restore` / `checkout` / `reset`. Read tree state at start; after each
  edit run `git diff <file>` to confirm only intended changes; at close run
  `git status` to confirm the dirty file list is unchanged. HEAD untouched.
- **Single bounded session.** If it doesn't fit, that's a finding.

---

## §10 — What happens after Code's session

The next operator-Claude session triages
`account_id_normalization_report.md`: confirm settlement byte-identical,
confirm the FK-now-holds proof and the deploy-path confirmation, confirm
0 regressions, surface any findings. **On a clean triage, the
promo-on-bet + credit-in arc is complete** — live crediting works against
real accounts.

Sequence after that (unchanged): the **pre-cutover live-validation sweep**
(operator-run, manual — register a real account, log a real qualifier,
credit a real free bet, deploy it, settle it, all through the launched app
with live data — to flush any other latent seam in a controlled pass) and
the **launcher brief** (F9/F10 + F12 + rebuild-if-source-newer), then
**W16 cutover scoping**. The launcher brief is independent of this fix and
can run in parallel or after — operator's routing call. The Racing-API
placings backfill remains its own parallel brief (not a blocker).

## §11 — Cross-references

- **F2** — `interface_triage/promo_attach_build2_report.md` §8 (the defect,
  proven empirically) and §10 (routed to triage as the headline).
- **Build 2 brief** — `interface_triage/promo_attach_build2_brief.md` (the
  bet-safety + dirty-tree disciplines this brief inherits).
- **DR-032** (amended S180 — the bet→promo link is the catalogue serial):
  unaffected; the credit's promo reference is unchanged by this fix.
- **DR-030** (module boundaries): the changes sit within `domain/promos`
  and `workflows/promos`; no boundary crossed.
- **DR-021** (Adelaide-local timestamps): applies to the report.
- **DR-027/028** (two-database boundary): **not triggered** — single-DB
  change, no cross-database read or write.

---

**End of brief. LOCKED — operator-approved 2026-06-23 (Session 183).**
