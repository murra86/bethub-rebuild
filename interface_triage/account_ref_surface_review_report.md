# Account-reference format-mismatch class — surface & approach review (READ-ONLY)

**Session:** single bounded Claude Code session, 2026-06-24 ACST.
Start ~14:30 ACST, close ~14:55 ACST.
**Brief:** `interface_triage/account_ref_surface_review_brief.md` (LOCKED
S184). **Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main`
(HEAD `2329604`, unchanged at close).
**Mode:** READ-ONLY. Zero source edits. No git state-changing ops.

---

## Outcome (read first)

The account-reference format-mismatch class is **proven complete and
bounded**. Beyond the operational store (correct) and the promo spine
(fixed + proven by F2), the defect lives in **exactly three modules**:

1. `domain/cash_flow` + its store adapter (F-B) — **LATENT** (no
   production writer exists yet; only tests + the balance read path
   touch it).
2. `workflows/balances/v1/balance_derivation.py` (F-A / F-C) — the
   **live read/pool-display path**, broken against real hex accounts.
3. `ui/api/routers/racing.py` `/log-context` (F-A) — the wired
   endpoint param + its response model.

**All three escalation triggers are NO-HIT.** The frontend already
sends **hex dashless verbatim** (so F-A is backend-only); there is **no
schema dimension** (every column is already `TEXT`); and a shared
canonical account-ref type is **not required pre-cutover**. The proven
surface argues for the **minimal-holistic** altitude — retype the
in-scope sites to `str`-verbatim + per-path FK-on regression guards, no
new cross-domain type — with one coupling caveat (§D).

The single most important new finding for the fix brief: **the cash_flow
fix and the balance-read fix are COUPLED** through shared cross-domain
balance tests (F2 deliberately seeded them dashed). They must land
**together**, not piecemeal (§B-note, §D).

---

## Baseline

| Check | Start | Close |
|---|---|---|
| HEAD | `2329604aa80b34937a24644ea2eb18477749be85` | **identical** |
| Dirty-tree entries (`git status --porcelain`) | 69 | **69** |
| `settlement.py` SHA-256 | `9e07a75d…40d4a3` | **identical** |

`settlement.py` untouched (read-only; named for the record). No
`git add/commit/stash/restore/checkout/reset`. No DB write. No schema
change. No source edit — not even the four known sites.

---

## §A — Surface map (complete site inventory)

Operational/canonical form = **hex** (`uuid4().hex`, 32-char, dashless),
verbatim. The three in-scope refs: `account_id` · `book_id` ·
`account_at_book_id`. Spine-owned UUIDs (`event_id`, `parent_event_id`,
`supersedes_event_id`, `correlation_id`, `promo_id`, `promo_template_id`)
are **NOT** flagged — boundary calls noted inline where close.

### A.0 — Correct today (NOT defects) — the reference floor

| Area | Sites | Form | Note |
|---|---|---|---|
| `domain/accounts/__init__.py` | 58, 79, 107–109 | `str` | Source of truth; docstring states TEXT hex convention |
| `domain/bets/__init__.py` | 304 | `str` | ✓ |
| `store/repositories/accounts.py` | — | str-native | No `UUID` usage at all |
| `store/repositories/bets.py` | 1441 only | `UUID` | `correlation_id` normalisation — **spine-owned, correctly excluded** |
| `ui/api/routers/accounts.py` | 119/145/171–182/207–229; mints 276/367/418 `uuid4().hex` | `str`/hex | Operational mint + read, all hex |
| `ui/api/routers/bets.py` | 330–333, 427, 478–480, 643–645 | `str` | str-native filter/resolve; no `UUID()` |
| `ui/api/routers/provisional.py` | 156, 253 | `str` | ✓ |
| `workflows/bet_entry/*` (adapter/orchestrator/record_builder) | all ref sites | `str` | Write path entirely str-native |
| `ui/api/routers/promos.py` (credit-in) | 222, 271–273 | `str`/hex | Hex flows through; `UUID(str(promo_template_id))` @235 is **spine-owned, correctly excluded** |
| `store/schema/*` | accounts/bets/cash_flow/promos | `TEXT` | **All PK + FK columns TEXT** — no schema dimension |

### A.1 — Promo spine (FIXED by F2, NOT re-litigated)

`domain/promos`, `workflows/promos/promo_derivations.py` (108/155/278/
293/401–402/434–435), `workflows/promos/promo_store_adapter.py`
(164/181/198/240–242/408) — all three refs now `str`. Verified str-typed
at close. `store/repositories/promos.py` `str(...)` query sinks
(277/294/311/389/392/395/784) are **format-agnostic** — they faithfully
stringify whatever they receive; correct as-is. **Per §9 not re-opened.**

### A.2 — IN-SCOPE DEFECT SITES

**C1 — `domain/cash_flow` + adapter (F-B) — LATENT (no production writer)**

| file:line | Operation | Form produced/expected | Verdict |
|---|---|---|---|
| `domain/cash_flow/__init__.py` 409–411 | `account_id`/`book_id`/`account_at_book_id: UUID \| None` (root type) | UUID object | **DEFECT (root)** |
| `…cash_flow_store_adapter.py` 119, 136, 153 | list-query params typed `UUID` | UUID → repo `str()` → dashed | DEFECT (caller-facing) |
| `…cash_flow_store_adapter.py` 195–197 | `latest_non_superseded_by_scope` params `UUID` | dashed | DEFECT |
| `…cash_flow_store_adapter.py` 312–316 | **read**: `UUID(row.account_id/book_id/account_at_book_id)` | re-wraps hex TEXT → UUID | DEFECT |
| `…cash_flow_store_adapter.py` 344–348 | **write**: `str(event.account_id/book_id/account_at_book_id)` | `str(UUID)` → **dashed** | **DEFECT (F2-class write bug)** |
| `store/repositories/cash_flow.py` 52–54, 224/241/258, 336–342 | row dataclass `str`; query params `str(...)` | format-agnostic sink | **correct as-is** once callers pass `str` |

> Boundary note: `event_id` (405/308/340), `parent_event_id` (412/320/352),
> `supersedes_event_id` (413/323/357), `correlation_id` (416/330/364)
> keep `UUID` — **correct, not flagged.**

**C2 — `workflows/balances/v1/balance_derivation.py` (F-A / F-C) — LIVE read path**

| file:line | Operation | Form | Verdict |
|---|---|---|---|
| 112 | `AccountAtBookBalance.account_at_book_id: UUID` (output model) | UUID → dashed JSON | DEFECT |
| 128 + **147** | `_read_bet_rows_for_account_at_book(... : UUID)` → `(str(account_at_book_id),)` query of **`bets`** | **`str(UUID)` dashed vs hex PK → 0 rows** | **DEFECT (live)** |
| 392 | `compute_account_at_book_balance(account_at_book_id: UUID)` | fans UUID to cash_flow (413), promo (431, now hex), bets (444→147), inventory (456) | **DEFECT (live, hub)** |
| 496–497 + **510** + **512** | `_list_account_at_book_ids_for_holder(account_id: UUID)` → `(str(account_id),)` query of **`accounts_at_book`**, then `UUID(row[0])` re-wrap | **dashed query vs hex; re-wraps fetched hex → UUID** | **DEFECT** |
| 517 | `compute_account_holder_cash_holding(account_id: UUID)` | latent (no router) | DEFECT (latent) |
| 481 | `AccountHolderCashHolding.account_holder_id: UUID` (output) | dashed JSON | DEFECT (latent) |
| 580 | `BookNetFlow.book_id: UUID` (output) | dashed JSON | DEFECT (latent) |
| 589 | `AccountNetFlow.account_id: UUID` (output) | dashed JSON | DEFECT (latent) |
| 656, 667–680, 685–692 | `by_account: dict[UUID,…]` keyed by `event.account_id`; `AccountNetFlow(account_id=…)` | UUID keys/values | DEFECT (latent, net-flow) |

> Boundary note: 535 `cf_adapter.list_by_account(account_id, …)` and 431
> `promo_adapter.list_by_account_at_book(…)` are the **sinks** where the
> UUID becomes dashed against the now-hex promo store and the operational
> tables — the root is the UUID typing above, not the adapter call.

**C3 — `ui/api/routers/racing.py` (F-A) — WIRED endpoint**

| file:line | Operation | Form | Verdict |
|---|---|---|---|
| **714** | `get_log_context(account_at_book_id: UUID)` query param | FastAPI coerces incoming **hex → UUID**; downstream `str(UUID)` → **dashed** | **DEFECT (live — empty pool)** |
| 399 | `LogContextResponse.account_at_book_id: UUID` (response) | echoes dashed JSON back | DEFECT (inconsistency) |

> Boundary note: `credit_event_id` (381), `source_promo_instance_id`/
> `source_template_id` (386–387), `consumed_credit_event_ids: list[UUID]`
> (492), idempotency `uuid5`/`UUID(candidate)` (884/833) all keep `UUID`
> — **spine-owned / bet-id, correctly excluded.** The bet-write path
> (`LogBetRequest.account_at_book_id: str` @484 → 918) is **str-native,
> correct.**

**Confidence:** HIGH that the surface is complete. The enumeration was
not annotation-only — it swept `: UUID` annotations, `UUID(...)` wraps,
`str(...)`/f-string/`.hex` serialisation, and query/lookup construction
across `domain/`, `workflows/`, `ui/api/`, `ui/web/` (frontend),
`store/`, `scripts/`, `contracts/`, `clients/`. No in-scope ref typed
`UUID` or wrapped `UUID()` exists outside the three modules above (proven
by repo-wide regex, non-test). `scripts/`, `contracts/`, `clients/` carry
**no** in-scope ref sites.

---

## §B — Per-site treatment verdict

**The uniform fix is correct for every defect site: retype `UUID → str`,
drop the `UUID(...)` read-wrap and the `str(...)` write-wrap, pass the
operational-store TEXT through verbatim.** This is mechanically identical
to the proven F2 promo-spine fix. No site needs a different treatment;
**no site would be broken by hex-verbatim** — there is no legitimate
consumer of these three refs that requires the dashed/UUID form (every
UUID consumer is a spine-owned id, which stays UUID and is untouched).

Per-site nuances:

- **cash_flow read/write (312–316 / 344–348):** retype-to-passthrough,
  mirroring F2 exactly. Because cash_flow has **no production writer
  yet**, this is *verify-and-fix*: the write bug is latent but real (same
  FK mechanism — `str(UUID)` dashed vs hex `accounts_at_book` PK, and the
  cash_flow tables carry FK constraints to it, schema §A.0).
- **cash_flow query params (119/136/153/195–197) + repo (224–342):** the
  repo `str()` sinks need **no change** — they correctly stringify
  whatever they get. Retyping the adapter params to `str` is sufficient.
- **balance_derivation 147 / 510:** once params are `str`, the existing
  `str(...)` wrappers become harmless `str(str)` no-ops; the substantive
  change is retyping the params + **dropping `UUID(row[0])` at 512**
  (return the hex TEXT directly). This is the F-A read-path fix.
- **racing 714:** retype the param to `str` — **and this alone makes the
  pool display**, because the frontend already sends hex (§C). No `Query`
  validation change needed beyond the type.
- **racing 399 + balance output models (112/481/580/589) + by_account
  (656):** retype to `str` so the JSON carries hex, not dashed — keeps
  the API contract format-consistent with the listing endpoint.

**B-note — COUPLING (decisive for sequencing):** F2 deliberately seeded
the cross-domain balance tests (`test_balance_derivation.py`,
`test_balance_lay_branch.py`) as **dashed `str`**, *because* cash_flow
was still `UUID` (F2 report F-E). The moment cash_flow retypes to
hex-`str`-verbatim, those seeds must flip to **hex**, and the balance
read path (which queries the hex operational tables) aligns. Therefore
**the cash_flow fix (C1) and the balance-read fix (C2) are coupled and
must land in one change** — fixing one without the other re-creates the
mismatch in the shared tests. The racing fix (C3) rides on C2.

---

## §C — Frontend trace (the §5.3 unknown) — RESOLVED

**Origin format: HEX, dashless, verbatim. The frontend sends exactly the
string it received from the listing endpoint — no UUID construction, no
dashing, no transform.**

Trace (file:line):

1. `ui/api/routers/racing.py:791` — `/v1/racing/accounts` returns
   `AccountAtBookItem.account_at_book_id` typed **`str`** (447), sourced
   from `r.account_at_book_id` (the DB row, hex).
2. `ui/web/src/api/racing.ts:194` — `AccountAtBookItem.account_at_book_id:
   string` — received verbatim.
3. `ui/web/src/components/LogBetPanel.tsx:137` — passes
   `accountAtBook.account_at_book_id` straight to `fetchLogContext`.
4. `ui/web/src/api/racing.ts:161–166` — `fetchLogContext(accountAtBookId:
   string)` interpolates it **raw** into
   `/api/v1/racing/log-context?account_at_book_id=${accountAtBookId}`.
   **No formatting helper, no `UUID`, no dashing anywhere in the chain.**

The mismatch is therefore created **entirely on the backend**: the
`/log-context` route param `: UUID` (racing.py:714) coerces the inbound
hex into a `UUID` object (Python/pydantic `UUID` accepts 32-char dashless
hex), which then `str()`s to **dashed** downstream — so the query misses
the hex-stored rows and the pool shows empty.

**Conclusion: the F-A fix is backend-only — retype the route param (and
the balance read chain) to `str`. The frontend needs NO change.** This is
the highest-value de-risking result: the worst-case "client sends dashed,
backend retype insufficient" scenario does **not** hold.

---

## §D — Altitude verdict (independent)

**Verdict: MINIMAL-HOLISTIC HOLDS. Do not introduce a shared canonical
account-ref type pre-cutover.** Retype all in-scope sites to
`str`-verbatim + per-path FK-on regression guards; park the shared type
as the post-cutover hardening item (already §11 of the brief).

Reasoning:

- **The canonical form already exists.** The operational store *defines*
  it — TEXT hex, documented in `accounts.py` / `domain/accounts`. The
  promo spine already conforms (`str`, opaque). "These three are opaque
  operational-store TEXT" is the existing contract; `str` + the
  convention already express it. A new type re-encodes what is already
  true.
- **The surface is small, uniform, and now PROVEN bounded** — three
  modules, ~25 sites, one root cause. That is precisely the condition
  under which minimal-holistic is *safe*: the ceiling is found, so we are
  not patching blind. (The brief's fear — "discover a fifth live site
  mid-cutover" — is retired: the repo-wide sweep shows no in-scope
  `UUID`-typed/wrapped ref outside these three.)
- **A shared type carries real DR-030 cost for little gain.** A canonical
  type/normaliser would have to be importable across `domain/promos`,
  `domain/cash_flow`, `workflows/balances`, and `ui/` — a cross-cutting
  dependency DR-030 resists. And a Python `NewType`/alias gives **no
  runtime enforcement** (FastAPI would still coerce a `UUID`-typed param);
  a true boundary normaliser is *more* invasive than the retype, not
  less. The structural-elimination promise is weaker than it looks.
- **The real anti-recurrence lever is not a type — it is the test-seed-
  to-hex migration + per-path FK-on regression guards** (the exact lever
  that would have caught F2). Applied to (a) the cash_flow write under
  `foreign_keys = ON` against a hex account, and (b) the racing
  `/log-context` returning a non-empty pool against a hex account, these
  guards structurally pin the format at every live boundary.

**Conditions on the verdict:** (1) the cash_flow + balance fixes land
**together** (§B-note coupling); (2) **mandatory** per-path FK-on
regression guards, not optional; (3) the latent sites (cash_flow writer,
`compute_account_holder_cash_holding`, net-flow outputs) are retyped in
the same pass even though unwired — leaving them `UUID` would re-seed the
class for the next wiring session.

---

## §E — Escalation-trigger calls (explicit)

| Trigger (§9) | Call | Basis |
|---|---|---|
| Frontend non-hex origin (§5.3) | **NO-HIT** | Frontend sends hex dashless verbatim; no transform (§C). F-A is backend-only. |
| Schema dimension | **NO-HIT** | Every PK/FK column is `TEXT` (§A.0); fix stores hex verbatim with zero schema change. |
| Shared canonical type needed pre-cutover | **NO-HIT** | Surface is small/uniform/bounded; canonical form already exists; shared type adds DR-030 cost without runtime enforcement (§D). |

No escalation-class finding fires. The one finding that earns prominence
is **non-escalation**: the **C1↔C2 coupling** (§B-note) — a sequencing
constraint for the fix brief, not a scope expansion.

---

## Self-assessment

- **Coverage:** Complete. Enumeration spanned every form the brief names
  (annotated + unannotated typing, `UUID()`/`str()`/f-string/`.hex`
  serialisation, query/lookup/filter construction) across `domain/`,
  `workflows/`, `ui/api/`, `ui/web/` (frontend), `store/` (repos +
  schema), `scripts/`, `contracts/`, `clients/`. Operational store and
  promo spine confirmed correct; defect surface isolated to three
  modules; frontend traced end-to-end; altitude judged independently.
- **Confidence:** HIGH on the surface (repo-wide regex floor + per-file
  read of every hit). HIGH that F-A is live and backend-only (frontend
  trace + the FastAPI `UUID`-coercion mechanism). HIGH that F-B is the
  identical F2-class write bug but **latent** (no production constructor —
  only tests + the balance read path touch cash_flow; verified by
  searching all of `ui/`, `scripts/`, `contracts/`, `clients/`).
- **Boundary discipline:** No spine-owned UUID misclassified as in-scope;
  the close calls (`correlation_id` in bets repo, `promo_template_id` in
  promos router, `credit_event_id`/idempotency in racing, all `*_event_id`
  in cash_flow) are named and correctly excluded.
- **Not fully provable in one session:** Whether the *latent* cash_flow
  write bug would manifest in production depends on a future writer that
  does not yet exist — I proved the *mechanism* (UUID typing → `str(UUID)`
  dashed → FK-on vs hex `accounts_at_book` PK, with the FK constraint
  present in schema) but could not exercise it end-to-end (no constructor
  to drive, and read-only forbids writing one). The net-flow / holder-
  cash-holding output-model sites (481/580/589/656) are likewise unwired,
  so their dashed-JSON impact is inferred from the type, not observed.
- **Repo integrity:** HEAD `2329604` unchanged; 69 dirty entries
  unchanged; `settlement.py` SHA byte-identical; no source edit, no git
  state-changing op, no DB write, no schema change. No fix applied, no
  next-brief drafted, no "ship it" beyond the §D verdict.

*End of report. READ-ONLY session, 2026-06-24 ~14:55 ACST.*
