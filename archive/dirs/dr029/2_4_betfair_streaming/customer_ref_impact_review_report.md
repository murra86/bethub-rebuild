# Report — Betfair customer-reference impact & design review (READ-ONLY)

**Executed:** 2026-06-18 ACST (Adelaide-local, DR-021)
**Brief:** `dr029/2_4_betfair_streaming/customer_ref_impact_review_brief.md` (sha256 `b75e2a4a`)
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`) — read-only; no source/test/config touched, no git mutation, no suite run, no row reads.
**Output:** this file only.

> **Read-only attestation.** This review read source, schema DDL, and test
> files as evidence. It executed only inspection `grep`/`sed`/`cat`. No
> `bethub-v3` file was edited; no database row was read (schema DDL only);
> the suite was not run. Line numbers are quoted from the live tree at
> review time; the tree is dirty/in-flight, so a few may drift — where a
> brief anchor and a grep disagreed, the grep was trusted and the drift
> noted.

---

## §0 — Executive map

The 47-char reference that Betfair rejects (`INVALID_INPUT_DATA — customerRef
… 32 character limit`, S162) originates as a **`bet_id`** that is reused, in
the lay route, as the per-order Betfair reference. One generated value is
sent to Betfair in **two** capped fields (`customerOrderRef` 32 +
`customerRef` 32), and the `StrategyTag` value is sent in a **third**
(`customerStrategyRef` 15). The over-long value is generated at **two**
placement paths (lay route + hedge orchestrator), and the "canonical"
internal id (`bet-{uuid4}`, 40) is itself over 32. **The single most
decision-relevant finding:** no downstream consumer depends on the outbound
reference's value, format, or length — **reconciliation keys off
`betfair_bet_id`, settlement off `betfair_selection_id`, and nothing
reverse-maps a Betfair-returned `customerOrderRef`/`customerStrategyRef` to
an internal record or enum.** The two fix options therefore do **not**
collapse into a forced decouple; Option A is unblocked by any consumer, and
Option B's stated reconciliation rationale is already satisfied by the
existing `betfair_bet_id` column (§5.3, §5.5).

| # | Identifier | Where set | Betfair field(s) | Cap | Current value | Status |
|---|---|---|---|---|---|---|
| 1 | `bet_id` | gen sites §5.1 | — (internal PK) | none | `bet-record-{uuid4}` 47 (lay) / `bet-{uuid4}` 40 (canonical) | both >32; internal-only |
| 2 | `customer_order_ref` | = `bet_id` (lay) / sep (hedge) | `customerOrderRef` | **32** | 47 | **breaches** |
| 3 | `customerRef` | = `customer_order_ref` | `customerRef` (top-level de-dupe) | **32** | 47 | **breaches** (same value as #2) |
| 4 | `customer_strategy_ref` | `StrategyTag.value` (lay route only) | `customerStrategyRef` | **15** | `synthetic_each_way` 18 | **breaches** (only this tag; lay only) |

The 32/32/15 caps are **external Betfair limits**; there is **no client-side
length guard or truncation anywhere in v3 source** (grep for `[:32]`/`[:15]`/
`max_length`/`too long` over `clients/ ui/ workflows/ domain/` finds none on
these refs). The only enforcement today is Betfair's rejection — i.e. the
503.

---

## §5.1 — Generation map

Every site that mints a `bet_id` or a Betfair-bound reference (grep-grounded:
`uuid4`/`uuid5`/`"bet-"` across the repo):

| Site | Format | Len | Reaches Betfair? | Notes |
|---|---|---|---|---|
| `ui/api/routers/racing.py:981` (`place_lay`) | `body.bet_id or f"bet-record-{uuid4()}"` | **47** | **YES** → `customer_order_ref` (L990) → `customerOrderRef` + `customerRef` | **The live 503.** Same value also stored as `bets.bet_id` (threaded into `HedgeRecordInputs(bet_id=bet_id)`, L1037). |
| `workflows/bet_entry/v1/orchestrator.py:743` (Path B hedge) | `request.customer_order_ref or f"bet-record-{uuid.uuid4()}"` | **47** | **YES** → `customer_order_ref` | Second over-long placement site. Generated **independently** of the stored `bet_id` (see §5.4). |
| `workflows/bet_entry/v1/record_builder.py:207` `_resolve_id(prefix="bet")` | `f"bet-{uuid4()}"` | **40** | NO (internal) | **Canonical** `bets.bet_id` for hedge (L267) + soft-book (L351). Itself >32 — cannot serve as a Betfair ref. |
| `ui/api/routers/racing.py:877` (`log_bet`) | `"bet-" + str(uuid5(NS, idempotency_key))` | **40** | **NO** | **Answers the brief's open Q:** record-only. `log_bet` is a soft-book *back-bet* log (`orchestrator.log_soft_book_bet`), no Betfair placement. |
| `ui/api/dependencies/mock_transport.py:117` | `f"mock-bet-{uuid4().hex[:12]}"` | 21 | NO (mock) | Mock transport's fake `bet_id` in the place response; never a live value. |
| `record_builder.py:266` `_resolve_id(prefix="cycle")` / `racing.py:891` | `f"cycle-{uuid4()}"` 42 / `str(uuid4())` 36 | — | NO | `cycle_id`, not a bet ref — listed for completeness; not Betfair-bound. |
| `ui/api/routers/accounts.py:276/367/418` | `uuid4().hex` (32) | — | NO | account/book ids — unrelated to bets. |

**Format universe for `bet_id` (≥3, all >32):** `bet-record-{uuid4}` (47),
`bet-{uuid4}` (40), `bet-{uuid5}` (40).

---

## §5.2 — Betfair-bound consumption map

The **only** outbound site that places a customer reference into a Betfair
request is `placeOrders`. Cancel/replace/current-orders do **not** carry
customer refs (they key on Betfair `betId`/`marketIds` — confirmed in
`_build_cancel_orders_params`, `_build_replace_orders_params`,
`_build_list_current_orders_params`).

**`clients/betfair_client/v1/_translation.py` `_build_place_orders_params`** (grep lines 326/329/330; function now at ~L313):

| Betfair field | Assigned from | Cap | Source value (live) |
|---|---|---|---|
| `customerOrderRef` (L326) | `body["customer_order_ref"]` | **32** | `bet_id` (47, lay) |
| `customerRef` (L330) | `body["customer_order_ref"]` | **32** | **same value** as `customerOrderRef` — confirms the S162 flag |
| `customerStrategyRef` (L329) | `body.get("customer_strategy_ref")` | **15** | `StrategyTag.value` (lay route only) |

**Who supplies those body fields to `place_bet`:**
- `ui/api/routers/racing.py:990,995` (lay route): `customer_order_ref=bet_id` (47); `customer_strategy_ref=body.strategy_tag.value` → `synthetic_each_way` (18) **breaches 15**.
- `workflows/bet_entry/v1/betfair_adapter.py:199,204` (hedge): `customer_order_ref=<orchestrator 47>`; **`customer_strategy_ref=None`** → the 15-cap is **never** breached on the hedge path. The `customerStrategyRef` breach is **lay-route-only**, and only for `StrategyTag.SYNTHETIC_EACH_WAY`.

**`customerRef` semantics note (per review flag):** Betfair's top-level
`customerRef` is a per-request **idempotency/de-dupe** token, not a label. v3
sets it equal to `customerOrderRef` and reuses `customer_order_ref` across
retry attempts within a cycle (orchestrator L855/871/935). Any fix that
shortens or decouples it must preserve **uniqueness per logical order** so two
distinct orders cannot collide on a truncated token, and **stability across a
retry** so the de-dupe still recognises a resend. No code currently relies on
`customerRef` beyond passing it through (it is not read back — §5.3).

---

## §5.4 — Internal `bet_id` format & consumers

**Format inventory:** `bet-record-{uuid4}` (47), `bet-{uuid4}` (40),
`bet-{uuid5}` (40); mock `mock-bet-…` (21). Two real lengths (47/40), both
>32, all sharing the `bet-` prefix.

**Persistence map (`store/schema/bets.py`, `store/schema/ops.py` — DDL only):**

| Table.column | Role | Notes |
|---|---|---|
| `bets.bet_id` (TEXT) | **PRIMARY KEY** | Stores the internal id: **47** in the lay path (threaded from the route), **40** in hedge/soft-book paths. |
| `bets.betfair_bet_id` (TEXT) | Betfair-returned bet id | **The reconciliation/settlement key** (§5.3). |
| `bets.strategy_tag` (TEXT, nullable) | `StrategyTag.value` | Reconstructed via `StrategyTag(row.strategy_tag)` — `bet_store_adapter.py:118`. |
| `bet_legs.bet_id` (TEXT) | PK `(bet_id, leg_number)`, **FK → `bets(bet_id)`** | Format-agnostic; stores whatever `bets.bet_id` holds. |
| `ops_events.bet_id` (TEXT) | **FK → `bets(bet_id)`** | Audit/ops correlation by bet. |

There is **no `customer_order_ref` and no `betfair_ref` column** anywhere in
`store/` (grep confirms). The outbound `customer_order_ref` lives only on the
in-memory `AuditLogEntry.customer_order_ref` (`_audit.py:74`) and is echoed in
HTTP responses — it is **not persisted on the bet record**.

**Consumers that parse / assume `bet_id` format:**

| Consumer | Assumption | Behaviour today |
|---|---|---|
| `workflows/promos/v1/fb_deployment.py:71-79` `_coerce_uuid` | strips `"bet-"`, `UUID(rest)` | `bet-{uuid}` (40) → parses. **`bet-record-{uuid}` (47) → `ValueError` → silent `uuid4()` fallback** (L74-75; no log/raise). FB-deploy correlation already degrades for lay-route ids. |
| `ui/api/routers/racing.py:821-828` `_safe_uuid` | strips `"bet-"`/`"cycle-"`, `UUID(rest)` | `bet-record-…` → `None` (silent). FB-deploy event `correlation_id` already degrades likewise. |
| `workflows/bet_entry/v1/bet_store_adapter.py:118` `from_rows` | `StrategyTag(row.strategy_tag)` | Reconstructs the **strategy** enum from v3's own DB column (not `bet_id`). Breaks only if a stored `strategy_tag` value is not an enum member (relevant to shortening the *enum value* — see §5.5). |

**Joins / FKs keyed on `bet_id`:** `bet_legs(bet_id)→bets`,
`ops_events(bet_id)→bets`. All are format-agnostic TEXT FKs — they store and
match whatever string `bets.bet_id` holds; none parse it.

**Already-silently-failing today (finding):** the two UUID-recovery parsers
above (`_coerce_uuid`, `_safe_uuid`) **already fall back silently** for the
47-char `bet-record-` ids the lay/hedge paths generate — so free-bet-deploy
correlation on a `bet-record-` bet is already not the real UUID. This is
*pre-existing breakage*, not introduced by any fix, and it slightly raises
the value of a format that round-trips cleanly.

---

## §5.3 — Read-back & reconciliation consumption

Every site that reads a Betfair reference off a response, and an explicit
**breaks-if-shortened? Y/N**:

| Read-back site | Reads | What it does with it | Breaks if outbound ref shortened/decoupled? |
|---|---|---|---|
| `_translation.py:852` `_translate_place_orders` | `customerOrderRef` (place resp) | Echoes into parsed `customer_order_ref` (response shape) | **N** — pure echo; nothing matches on it. |
| `_translation.py:932-933` `_translate_list_current_orders` | `customerOrderRef`/`customerStrategyRef` | Maps into the parsed `CurrentOrder` shape | **N** — pass-through into a model field. |
| `clients/.../current_orders.py:104-105` | both refs | `CurrentOrder.customer_order_ref/_strategy_ref` model fields | **N** — fields only; no consumer matches on them. |
| `clients/.../_stream_parser.py:360-361` | `rfo`→`customer_order_ref`, `rfs`→`customer_strategy_ref` | Order-stream unmatched-order fields | **N** — captured into `UnmatchedOrder`; not used as a match key. |
| `clients/.../streaming.py:641-642` | both refs | Builds `UnmatchedOrder` | **N** — model only. |
| `clients/.../_audit.py:74` (`AuditLogEntry`) | `customer_order_ref` | **In-memory audit-trail join key** (§12.3): links a failed attempt + its retry by *shared outbound ref* (`tests/.../test_audit.py::test_customer_order_ref_join_key_links_retry_cycle`) | **N (to length)** — depends only on the *same* ref being reused across a cycle's retries, which the orchestrator already does. Shortening is fine **provided the reused value stays stable & unique per cycle**. Not a Betfair round-trip. |
| `workflows/.../reconciliation.py:200-218` | — | Calls `get_order_state(bet_id=record.betfair_bet_id)` | **N** — reconciliation keys off **`betfair_bet_id`**, never `customer_order_ref`. |
| `workflows/.../settlement.py:358-420` | — | Matches runner by `leg.betfair_selection_id` | **N** — settles by selection id; no customer ref involved. |

**The two specific questions (definitive):**

1. **Does any path reverse-map a Betfair-returned `customerStrategyRef` to a
   `StrategyTag`?** — **NO.** The *only* `StrategyTag(...)` reconstruction in
   the codebase is `bet_store_adapter.py:118` from `row.strategy_tag` (v3's
   own DB column). The read-back `customerStrategyRef` (current-orders /
   stream) is captured as a plain string and never converted back to the
   enum. Shortening the **outbound** `customerStrategyRef` therefore breaks
   no reverse-map. (The only strategy-shortening risk is internal: changing
   the *enum value itself* vs. stored DB rows — see §5.5.)

2. **Does reconciliation depend on outbound `customer_order_ref` == stored
   `bet_id` exactly?** — **NO.** `reconciliation._resolve_one` reads orders
   via `adapter.get_order_state(bet_id=record.betfair_bet_id, …)`
   (`reconciliation.py:215-218`); the gate at L200 even skips records with no
   `betfair_bet_id`. Reconciliation round-trips on the **Betfair-returned bet
   id**, which is stored in its own `bets.betfair_bet_id` column —
   independent of the customer reference. Decoupling `bet_id` from
   `customer_order_ref` needs **no** new stored mapping for reconciliation.

**Net:** no read-back consumer matches, joins, settles, or reverse-maps on
the outbound `customer_order_ref` / `customerStrategyRef`. The only
ref-keyed dependency is the in-memory audit retry-join, which is satisfied by
ref *stability within a cycle*, not by its length or its equality to
`bet_id`.

---

## §5.5 — Two-option design analysis (neutral; no pick)

### Option A — Unify-and-cap

Make every Betfair-bound id ≤32 at the generation sites; keep
`bet_id == customer_order_ref == customerRef`; shorten the breaching
strategy value to ≤15.

- **Generation sites that must change:** `racing.py:981` (lay) and
  `orchestrator.py:743` (hedge) — both produce `bet-record-{uuid4}` (47).
  Because the canonical `bet-{uuid4}` (40) is *also* >32, the format
  `record_builder._resolve_id(prefix="bet")` (L207) must change too if
  `bet_id` is to stay ≤32 and stay fused with the ref.
- **The hard arithmetic (the "concrete ≤32 scheme" the next session needs):**
  `"bet-"` (4) + a full uuid4 hex (32) = **36 > 32**. A ≤32 fused id
  therefore **cannot** be `bet-` + full UUID. It must either drop the `bet-`
  prefix (breaking the `startswith("bet-")` parsers `_coerce_uuid` /
  `_safe_uuid` and the tests below) **or** truncate the UUID (raising a
  collision question at volume). A bare 32-hex uuid (no prefix, no dashes)
  fits at exactly 32 but loses the human-readable prefix and the parsers.
  This trade is intrinsic to A and must be named in the fix brief, not
  hand-waved as "make it ≤32."
- **Already-stored `bet_id` "illegal"?** Existing rows hold 47/40-char ids
  (PK). Shortening generation does **not** rewrite them; they remain valid PKs
  and FKs (format-agnostic TEXT). They only matter if an order was already
  *placed on Betfair* under the old format — and **no live order has been
  placed** (5 live runs, bet-safety gate held, zero bets — §9 / brief
  context), so there is no historical Betfair order whose ref must keep
  round-tripping. New ids simply start short.
- **Strategy 15-cap under A:** close it by a **boundary mapping**
  (`StrategyTag.value → ≤15 code`) at the `customerStrategyRef` assignment,
  leaving the enum/DB value full — this avoids any migration and breaks no
  reverse-map (none exists). *Alternatively* shorten the enum value itself,
  which then also rewrites `bets.strategy_tag` semantics and forces a
  migration for stored `synthetic_each_way` rows (so `bet_store_adapter`
  `StrategyTag(row)` still resolves). The boundary-mapping form is strictly
  smaller.
- **Residual conceptual debt:** id and reference stay **fused** — the tension
  that prompted this review is *contained, not resolved*. Every future
  Betfair cap change re-touches the id scheme.

### Option B — Decouple

`bet_id` keeps a natural internal form (no Betfair cap); a separate ≤32
reference is generated per order for the Betfair fields.

- **Where the new field lives:** *named, not written* — a `betfair_ref TEXT`
  column on `bets` (or per-leg) would be the schema home **if** the outbound
  ref must be stored. **Key finding:** for *reconciliation* it need not be —
  reconciliation already round-trips via the existing `bets.betfair_bet_id`.
  Nothing reads the outbound `customer_order_ref` back to match a record
  (§5.3). So Option B's canonical rationale ("store a ref so reconciliation
  round-trips") is **already satisfied**; a new `betfair_ref` column would
  only *formalise* the outbound token (e.g. for audit/debug), not unblock any
  consumer. B can even be implemented **without** a schema change: generate a
  ≤32 ref at each placement site, stop setting `customer_order_ref = bet_id`,
  and leave `bet_id` natural.
- **Read-back sites that must switch from matching `bet_id` to `betfair_ref`:**
  **none** — no read-back site matches on `bet_id`-as-ref today (they use
  `betfair_bet_id` / `betfair_selection_id`).
- **Migration question:** none forced for historical orders (no live orders
  placed). If a `betfair_ref` column is added, existing rows get `NULL` —
  acceptable, since nothing reads it for past bets.
- **Strategy 15-cap under B:** identical close to A — boundary-map
  `StrategyTag.value → ≤15` at the `customerStrategyRef` assignment. B does
  not change the strategy story.
- **Trade:** larger surface *only if* a schema column is taken; structurally
  cleaner (id and ref separated, so future cap changes never touch `bet_id`).

### Blast-radius tables

**Option A**

| Dimension | Detail |
|---|---|
| Source files touched | `racing.py` (lay gen L981), `orchestrator.py` (hedge gen L743), `record_builder.py` (`_resolve_id`/`bet-` format L207) + the `customerStrategyRef` mapping point (`racing.py:995` or `_translation.py:329`) |
| Schema touched | **N** (unless enum-value form chosen for strategy → migration) |
| Reconciliation paths touched | **N** (keys on `betfair_bet_id`) |
| Tests touched | `tests/ui/api/test_racing.py:683` (`startswith("bet-")`), `tests/workflows/bet_entry/v1/test_orchestrator.py:1044` (`startswith("bet-record-")`), `tests/workflows/promos/v1/test_fb_deployment.py` (assumes `bet-{uuid}` parseable). Most ref tests use short fixtures (`bet-record-uuid-12345`, 21) asserting round-trip equality, not length — those are unaffected. |
| Single biggest risk | The ≤32 scheme **forces** dropping the `bet-` prefix or truncating the UUID → collision risk or breaking the prefix parsers (which already degrade silently). |

**Option B**

| Dimension | Detail |
|---|---|
| Source files touched | `racing.py:990` (stop `customer_order_ref=bet_id`; gen a ≤32 ref), `orchestrator.py:743`/`betfair_adapter.py:199` (gen a ≤32 ref), `_translation.py` (unchanged mapping) + strategy boundary-map |
| Schema touched | **Optional** — `betfair_ref` column *named* only if the token must be persisted; **not required** for reconciliation |
| Reconciliation paths touched | **N** (already on `betfair_bet_id`) |
| Tests touched | The two `startswith` tests above (the generated value changes shape); fewer format assumptions if `bet_id` keeps its natural `bet-{uuid}` form — `_coerce_uuid`/`_safe_uuid` then *improve* (a clean `bet-{uuid}` parses, unlike today's 47-char) |
| Single biggest risk | Lower-risk on consumers; the cost is conceptual/process (a schema column decision) rather than a functional break |

### Do the options collapse into one?

**No — and the reason is the headline finding.** A decouple is **not forced**:
no consumer depends on `bet_id == customer_order_ref`, so Option A is
unblocked. Conversely, Option B is *cheaper than the brief assumes* because
its reconciliation rationale is already met by `betfair_bet_id`. The genuine
trade is **A unblocks the $5 lay with the smallest change but keeps id≡ref
fused and forces the awkward "≤32 without a real UUID" scheme; B keeps `bet_id`
natural (even *fixing* the silent `_coerce_uuid` degrade) for slightly more
surface and a schema-or-not decision.** Both close the 15-cap the same way.
The review states the trade; the operator + next session pick.

---

## Open items / could-not-confirm

- **Betfair caps are external.** 32/32/15 are Betfair's documented limits
  (named by the S162 503), not encoded in v3. Confirmed there is **no**
  client-side guard; not independently re-confirmed against Betfair docs in
  this session (out of read-only scope). The S162 diagnostic is the source.
- **`customerRef` de-dupe behaviour** is reasoned from Betfair semantics +
  code (set = `customerOrderRef`, reused across retries); v3 has no test
  exercising Betfair's de-dupe, so the *consequence* of a truncated
  `customerRef` colliding is a design consideration, not an observed failure.
- **Test pass/fail not run** (read-only). Test *impact* above is from reading
  assertions, not executing; the precise set that fails under each option
  should be re-derived when the fix is scoped.
- **`record_builder._resolve_id` prefix for `bet_id` is `"bet"`** (L267/351,
  confirmed); the soft-book vs hedge callers both use it, so the canonical
  stored form is uniformly `bet-{uuid4}` (40) **except** the lay route, which
  overrides it with the route-supplied 47-char value.

---

*Reviewer's observation (labelled — observation, not decision):* the
narrowest surface that closes both breaches is a **boundary cap+map at the
placement edge** — cap `customerOrderRef`/`customerRef` and map
`customerStrategyRef → ≤15` where the body fields are assigned — because that
is the one point all paths funnel through and it touches no consumer. Whether
to take that minimal form (an A-flavoured fix) or the structural decouple (B)
is the operator's call; this review only notes where the blast radius is
smallest.

**Self-assessment:** All five §5 areas mapped and grounded by repo-wide grep
(§7) plus direct reads of every named anchor and the files the trace led to
(reconciliation, settlement, schema, adapter, store adapter, audit, fb_deploy
parsers). Every read-back site carries an explicit breaks-Y/N; both options
have full blast-radius tables; the 15-cap close is named under each. No option
chosen, no fix written, no schema written, no code touched. Length ≈ 300 lines
— within the 250–500 target.
