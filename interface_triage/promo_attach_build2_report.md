# Build 2 — free-bet credit-in + cycle link — build report

**Session:** single bounded Claude Code session, 2026-06-23 (Adelaide
local, ACST). Start ~22:00 ACST, close ~22:30 ACST.
**Brief:** `interface_triage/promo_attach_build2_brief.md` (LOCKED S182).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main` (HEAD
`2329604`, unchanged at close).
**Outcome:** all six §5 pieces built and green — the credit-in write
(FB + cash), the gate, the once-per-qualifier guard, the shared endpoint,
both confirm surfaces, and the cycle link. **Two pre-existing integration
gaps surfaced that the locked design did not anticipate** (F1, F2); F1 was
resolved with a minimal, DR-032-faithful, flagged deviation; F2 is a
W11/W13 account-id-format inconsistency that blocks the credit write
against live (router-created) accounts and is **out of Build 2's scope to
fix** — surfaced as the headline finding for triage. Settlement seam
byte-identical. Zero regressions.

> **Read first.** The credit-in write functions correctly and is fully
> tested **against canonical dashed-UUID account ids** (the convention the
> W13 promo-event spine and its tests already use). The live system's W11
> accounts router generates non-canonical `uuid4().hex` ids; the W13
> UUID-typed event fields serialize those to dashed form, so the credit's
> FK to `accounts_at_book` fails against a real account (`FOREIGN KEY
> constraint failed`). This is **F2** — a latent W11/W13 seam Build 2 is
> the first to cross, shared by the deploy path, reconcilable only outside
> Build 2's anchors. Operator live-validation (brief §10) will hit it; it
> must be resolved before the launched app can credit a real qualifier.

---

## §0 — Baseline

- **HEAD:** `2329604` at start and close (no commit/checkout/reset).
- **Settlement seam (bet-safety gate):**
  `workflows/bet_entry/v1/settlement.py` SHA-256 at start **and** close:
  `9e07a75d3ab85741d5c3346521dbca25d09da632bd1140fcdb6550e55840d4a3` —
  **byte-identical**. No contact with `settlement.py`,
  `apply_manual_operator_resolution`, or `provisional.py` (the only
  mentions of those names in my code are a docstring stating the
  non-contact).
- **Dirty tree (expected substrate):** 69 `git status` entries at start
  and close; HEAD unchanged. Every new file landed in an already-untracked
  dir (`workflows/`, `ui/`, `tests/`), so no new top-level entry appeared.
  No git state-changing command run.
- **Build 1 substrate verified live at start:** `bets.promo_template_id`,
  `BetRecord.promo_template_id`, `PromoTemplate.return_pct` all present.
- **Tests:** Python `uv run pytest -q` **1166 → 1180** (+14, **0
  regressions**). Frontend `vitest run` **109 → 110** (+1); `tsc -b` clean.

Order followed §6 (1 → 4 → 2 → 3 → 5 → 6), tests woven throughout.

---

## §5.1 — The credit-in write (`record_free_bet_credit`)

**Built** — new module `workflows/promos/v1/fb_credit.py`, a near-mirror
of `record_free_bet_deployment`. `record_free_bet_credit(conn, *,
qualifier_bet_id, account_id, book_id, account_at_book_id, stake,
return_type, return_pct, promo_template_id)` writes one triggered credit:

- `event_type` = `FREE_BET_CREDITED` when `return_type == 'free_bet'`,
  `PROMO_CASH_CREDITED` when `'cash'` (one function, branch on the term —
  cash in scope per the S179 lock, pulling in `PromoCashCreditedPayload`).
- `credit_source = 'triggered'`; `status = FINALISED`;
  `amount = (stake × return_pct)` quantized to cents, `> 0` enforced (no
  cap — the cap is a stored analytics term only).
- `triggering_bet_id` = the **real** qualifier UUID (O5, below).
- `triggering_promo_instance_id` = the bet's `promo_template_id` (Option B
  — the catalogue serial doubles as the reference; **no domain validator
  relax** — see F1 for the adapter check this required).
- `account_id`/`book_id`/`account_at_book_id` from the qualifier;
  `source = OPERATOR`; timestamps via `_now_adelaide()`; `correlation_id`
  = the qualifier UUID for read-side joins.
- Written via `PromoStoreAdapter.append_event` — the same sink the deploy
  write uses. **No settlement contact.**

**O5 — real UUID or raise.** `_qualifier_uuid` strips the `bet-` prefix
and parses; on failure it **raises `CreditInError`** rather than minting a
fresh `uuid4()` the way the deploy path's `_coerce_uuid` does. A phantom
`triggering_bet_id` would silently break the §5.5 cycle resolve. Tested.

Verified (unit): FB credit (amount 20.00 = 20 × 1.0), cash credit (5.00 =
20 × 0.25), FINALISED, real `triggering_bet_id`, serial stamped as
`triggering_promo_instance_id`, and `CreditInError` on an unparseable id.

## §5.4 — Idempotency guard (O6)

**Built** — `find_existing_credit(adapter, triggering_bet_id)` scans both
credit event types for an existing event stamping this qualifier;
`record_free_bet_credit` calls it before writing and, on a hit, returns
`CreditInResult(status='already_credited', …)` with **no second write**.
Natural key: `triggering_bet_id`. Verified: a second call returns
`already_credited` with the same `event_id`, and the log holds exactly one
credit.

## §5.2 — The shared credit-in endpoint

**Built** — `POST /v1/promos/credit-in` added to `ui/api/routers/promos.py`
(the **first write** on the previously read-only router), reusing the
per-request `get_db_connection` + `BETHUB_DB_PATH` + `dependency_overrides`
seam. Request carries only the qualifier `bet_id` (`extra='forbid'`); the
server reads `strategy_tag` / `settlement_state` / `promo_template_id` /
`matched_stake` / `account_at_book_id` off the bet, resolves
`account_id`/`book_id` from `accounts_at_book`, reads the promo terms from
the catalogue, enforces the gate (§5.3), and calls `record_free_bet_credit`
(which runs §5.4). Maps: 404 unknown bet, 422 gate-fail / bad serial /
missing account, 201 `credited`, 201 with `already_credited` status. It
reads a *settled* qualifier off the bet and never touches settlement.

## §5.3 — The two confirm surfaces → one write

**Built.** Both surfaces call the one endpoint; the gate is
**server-enforced** (`safety_net` ∧ `settled_lost` ∧ `promo_template_id
IS NOT NULL`) and mirrored client-side via `isCreditInQualifier` (in the
new `ui/web/src/api/promos.ts` `creditIn` client).

- **BetLog** (`ui/web/src/routes/BetLog.tsx`): the former inert
  `placed-confirm-scaffold` button is now **enabled only for a qualifier
  row**; on click it `window.confirm`s "placed in the insured spots?" then
  fires `creditIn(bet_id)`, surfacing `Credited … ✓` / `already credited` /
  the server error inline. To gate client-side, `promo_template_id` is now
  exposed on the feed (`BetFeedItem`) — see Findings F3.
- **LogPastBet** (`ui/web/src/routes/LogPastBet.tsx`): when the
  settle-at-entry outcome is `Lost` ∧ strategy `safety_net` ∧ a promo is
  selected, an inline **"Placed in the insured spots?"** checkbox appears;
  on submit, after the bet is logged, the **same** `creditIn(bet_id)` fires
  and appends the outcome to the success line.

Verified (vitest): the BetLog button is disabled for a non-qualifier and
enabled for a qualifier, and a confirm fires `creditIn` with the bet id and
shows the credited status.

## §5.5 — Piece A: cycle inheritance

**Built** — `resolve_inherited_cycle(conn, consumed_credit_event_ids)` in
`fb_credit.py`: resolves the **oldest** consumed credit (FIFO by
`recorded_at`) → its `triggering_bet_id` (stamped by §5.1) → that
qualifier bet's `cycle_id`. Wired into `ui/api/routers/racing.py`
`log_bet`: when `is_free_bet` ∧ `consumed_credit_event_ids` ∧ no
client-supplied cycle, the deployed bet's `cycle_id` is the resolved
qualifier cycle instead of a fresh `uuid4()`. **Falls back to a fresh
cycle** when nothing is resolvable (no credits, a freebie with no
trigger, the credit/qualifier missing) rather than failing the deploy.
Verified (unit): a deployed free bet inherits its qualifier's cycle; the
oldest credit wins regardless of input order; the empty / unknown cases
return `None`.

## §5.6 — Tests + settlement-seam proof

- `tests/workflows/promos/v1/test_fb_credit.py` (**7**) — FB/cash branch;
  amount; FINALISED; real trigger id; serial as instance id; O5 raise;
  idempotency; cycle resolve (inherit / oldest / fallback).
- `tests/ui/api/test_promos_credit_in.py` (**7**) — endpoint round-trip
  (one credit, right amount/type/trigger id, pool fills); idempotent second
  call; cash credit; gate rejects 3 non-qualifier shapes (no write); 404.
- `ui/web/src/routes/BetLog.test.tsx` — the qualifier-enables-and-credits
  case + the feed-field fixture update.
- **Settlement SHA byte-identical** start→close (§0).

---

## §7 — Empirical verification (before / after)

| Check | Before | After |
|---|---|---|
| `settlement.py` SHA-256 | `9e07a75d…40d4a3` | **identical** |
| Python `uv run pytest -q` | 1166 passed | **1180 passed (+14, 0 regressions)** |
| `tsc -b` | clean | **clean** |
| `vitest run` | 109 | **110 (0 regressions)** |
| HEAD / `git status` count | `2329604` / 69 | **`2329604` / 69** |
| git state-changing commands | — | **none** |

**Round-trip proof (test `test_qualifying_loss_credits_once…`):** a
settled-lost `safety_net` bet with an attached FB serial → `POST
credit-in` → **201 `credited`**, `free_bet_credited`, amount `20.00`, the
credit stamping the real qualifier id + the serial, and
`compute_free_bet_inventory` returns `20.00`. A second call → `201
already_credited`, no second event. (All with canonical dashed-UUID
accounts — see F2.)

---

## §8 — Findings / surprises

**F1 — Option B was blocked by an adapter-side promo-reference check that
the S179 review missed; resolved with a minimal DR-032-faithful adapter
change (out-of-named-anchor, flagged).** The locked design (Option B, "no
validator relax") puts the catalogue serial (`promo_template_id`) in
`triggering_promo_instance_id`. But `PromoStoreAdapter._validate_payload_references`
calls `_require_promo(...)`, which validates that id against the **`promo`
instance table** — empirically raising `PromoReferenceValidationError`
("non-existent promo_id") for a single-level serial. The S179 review
(Area 4, which I authored) leaned Option B on the basis that the *pydantic
cross-field* validator was the only gate; it did not catch this
*adapter-layer* reference check.
- **Resolution:** I added `_require_promo_reference`, which accepts the id
  if it exists as **either** a catalogue serial (`promo_template`) **or** a
  legacy `promo` instance, and pointed the two triggered-credit paths at
  it. This preserves the existence guarantee (the credit must reference a
  *real* promo) and is faithful to DR-032-amended (S180: the bet→promo link
  is the catalogue serial). It does **not** loosen the domain payload's
  cross-field invariant (both triggering ids still required), so §9's "no
  validator relax" is honoured in letter and intent.
- **Deviation flag:** `workflows/promos/v1/promo_store_adapter.py` is **not
  a named §5 anchor**. I edited it because Option B cannot write through
  `append_event` (mandated by §5.1) without it — the alternative was a
  fully-blocked build. Backward-compatible (existing two-level promo tests
  still pass via the `promo` fallback; 150 promo/balance tests green).
  **Routes to triage to ratify.**

**F2 — W11/W13 account-id format mismatch blocks the credit write against
live accounts (headline; out of Build 2's scope to fix).** The W11
accounts router generates primary keys as `uuid4().hex` (32 hex chars, no
dashes — `accounts.py:276/367/418`). The W13 promo-event FK fields are
typed `UUID` and the adapter serializes them with `str(uuid)` → the
**dashed** canonical form. So a credit event built from a real qualifier's
`account_at_book_id` (hex) stores the dashed form, which does **not** match
the hex PK in `accounts_at_book` → with `PRAGMA foreign_keys = ON` (which
`PromoStoreAdapter` sets), `append_event` raises **`FOREIGN KEY constraint
failed`** (proven empirically this session). Even with FK off, the
hex-keyed `compute_free_bet_inventory` would not find the dashed credit, so
the pool would not fill.
- **Why it never bit before:** no production path ever wrote a credit
  (the gap Build 2 closes), and the entire W13 promo test-suite seeds
  accounts in dashed `str(uuid4())` form, so the spine is internally
  consistent in tests. Build 2 is the first to cross W11(hex) ↔ W13(UUID).
  **The existing deploy path carries the identical latent risk.**
- **Scope:** fixing it touches the W11 account-id format, the W13 event
  field typing/serialization, and the bets table — a cross-cutting
  reconciliation **outside Build 2's named anchors and its §9 limits**
  (no bets-schema change; edit only named anchors). Build 2's code is
  correct for canonical-UUID accounts; the tests use that convention (the
  established W13 test convention, not a mask). **Flagged for a dedicated
  W11/W13 account-id normalization brief before live-validation.**

**F3 — `promo_template_id` exposed on the BetLog feed (§5.3 support,
out-of-named-anchor).** §5.3 requires the BetLog "Placed?" gate to check a
promo is attached, but `BetFeedItem` did not carry `promo_template_id`. I
added it (additive, nullable, defaulted) to the server `BetFeedItem` model
+ `_to_feed_item` + the TS type. `ui/api/routers/bets.py` is not a named
§5 anchor; the exposure is a read-only additive field required by §5.3's
client gate. (The server gate is authoritative regardless.) Flagged.

**F4 — `correlation_id` on the credit = the qualifier UUID.** Not mandated
by the brief; chosen for read-side traceability (the §5.5 link itself uses
the payload's `triggering_bet_id`, not the correlation). Harmless; noted.

**F5 — Minor support edit: `BetLog.module.css` gained an `.actionSuccess`
class** for the confirm feedback line (styling sibling of the named
`BetLog.tsx` anchor).

Nothing was dropped for non-fit; all six pieces fit the session.

---

## §9 — Files touched (complete list)

**Production — Python:**
- `workflows/promos/v1/fb_credit.py` — **NEW** (§5.1 write, §5.4
  idempotency, §5.5 cycle resolver, O5).
- `workflows/promos/v1/promo_store_adapter.py` — `_require_promo_reference`
  (F1; out-of-anchor, flagged).
- `ui/api/routers/promos.py` — `POST /v1/promos/credit-in` + gate (§5.2/§5.3).
- `ui/api/routers/racing.py` — §5.5 cycle inheritance in `log_bet`.
- `ui/api/routers/bets.py` — `promo_template_id` on the feed (F3;
  out-of-anchor, flagged).

**Production — frontend:**
- `ui/web/src/api/promos.ts` — `creditIn` + `isCreditInQualifier`.
- `ui/web/src/api/bets.ts` — `BetFeedItem.promo_template_id`.
- `ui/web/src/routes/BetLog.tsx` — the "Placed?" confirm (§5.3).
- `ui/web/src/routes/BetLog.module.css` — `.actionSuccess` (F5).
- `ui/web/src/routes/LogPastBet.tsx` — inline "placed?" confirm (§5.3).

**Tests (new / modified):**
- `tests/workflows/promos/v1/test_fb_credit.py` (**new**, 7).
- `tests/ui/api/test_promos_credit_in.py` (**new**, 7).
- `ui/web/src/routes/BetLog.test.tsx` (qualifier-credits case + fixture).

**Deliberately NOT touched:** `settlement.py` (SHA-proven),
`apply_manual_operator_resolution`, `provisional.py`; no bets-schema
change; no domain payload validator relax; no `is_free_bet` path; no Piece
B / catalogue-UI / partial-draw-down work.

---

## §10 — Self-assessment

- **Coverage:** all six §5 pieces built and verified — the write (FB +
  cash), the gate (3 reject shapes + accept), idempotency, the endpoint
  round-trip (pool fills), and the cycle link (inherit / oldest / fallback).
  +14 Python tests, +1 vitest, 0 regressions.
- **Confidence:** high on the logic and the bet-safety gate (settlement
  SHA identical; the credit is a pure promo-event write). High that **F2 is
  real and blocking for live accounts** — proven empirically twice this
  session (FK raise + non-resolving inventory). Medium on F1's resolution
  being the operator's preferred fix — it's the minimal design-faithful
  option, but it edits a non-anchor validator and triage should ratify it
  (or prefer a different reconciliation).
- **Not done / not traced (honest):** I did **not** make the credit write
  function against live `uuid4().hex` accounts — that is F2, a W11/W13
  reconciliation outside scope; the build is correct for canonical-UUID
  accounts and tested as such. I did not exercise the §5.5 cycle link
  through the full racing `log_bet` HTTP path (orchestrator + Betfair) —
  it's unit-tested at the resolver and wired in the route; the deploy-path
  integration is between-session live work. The `test_cycle_resolve_picks_oldest`
  test relies on two sequential writes having distinct microsecond
  `recorded_at` (true in practice; a theoretical same-tick collision is
  the only flake surface).
- **Length:** ~330 lines — within tolerance; F1/F2 earned their detail
  (they are the triage-critical findings), flagged here per §8.
- **Repo integrity:** HEAD unchanged; no `git add`/`commit`/`stash`/
  `restore`/`checkout`/`reset`; 69 git entries unchanged; `settlement.py`
  byte-identical; no DB file copy (tests use the `BETHUB_DB_PATH` /
  `dependency_overrides` seam). Adelaide timestamps throughout.

### Routes to the operator-Claude triage (not chased here)

- **F2 (headline):** scope a W11/W13 account-id-format reconciliation
  before the launched app can credit a real qualifier.
- **F1:** ratify (or adjust) the `_require_promo_reference` adapter change.
- **F3:** ratify the feed exposure of `promo_template_id`.
