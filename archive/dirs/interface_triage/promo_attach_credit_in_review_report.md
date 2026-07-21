# Promo-on-bet + free-bet credit-in — read-only review report

**Run:** 2026-06-23 ~16:57 ACST (Session 178 follow-on, single bounded
Code session) against the brief at
`interface_triage/promo_attach_credit_in_review_brief.md` (locked draft).
**Method:** source read of the files named in §5 (verified against the
live tree, not trusted from the brief's line anchors), plus targeted
repo-wide greps to prove the negative findings. v2 read for requirements
only (promo term-set + refund rule), no engineering mapped.
**Repo state:** `bethub-v3` left exactly as found. No edits, no build, no
migration, no DB access, no git state-changing ops. The only file written
is this report.

> **Headline (read first).** Both halves are greenfield-on-substrate.
> **(a) Promo-on-bet:** the bet carries *no* promo reference — no
> `promo_instance_id`, no serial, and even the `promo_ev_at_log` the brief
> assumed is persisted is silently dropped at the API boundary (Area 2,
> O1). **(b) Credit-in:** still true at S178 — *no production path writes a
> `free_bet_credited` event* (Area 4 neg-grep). The promo-event log, deploy
> write, pooled balance and inventory read are all built; the credit
> *write* and the promo *attach* are both absent. The structured term-set
> the brief wants exists only in **two disconnected free-form
> representations** (frontend EV presets + seed-template JSON), neither
> typed, neither on a settlement-readable serial (Area 1). The biggest
> *design* ambiguity isn't effort — v3 ships a **two-level** model
> (`promo_template` + `promo` instance) while the brief mandates
> **single-level**; reconciling those is the load-bearing call (O2).

Order taken: **1 → 2 → 4 → 3 → 5 → 6 → 7** (the brief's suggested
sequence). It held cleanly — Area 4 reads naturally right after the
write-on map (both are "promo identity on the bet"), and Area 3's
read-back seam is easier to size once you've seen where the credit write
lands. No reordering needed.

---

## §0 — Baseline (repo state + what was read)

- **HEAD:** `2329604` on `main` — same commit the manual-entry build
  report (Brief 2) closed against. Working tree **dirty as expected**
  (in-flight `betfair_client` work + untracked `domain/`, `workflows/`,
  `ui/`, `scripts/`, `migrations/`). All target files present on disk.
- **Settlement seam proven untouched (read-only check):**
  `workflows/bet_entry/v1/settlement.py` SHA-256 =
  `9e07a75d3ab85741d5c3346521dbca25d09da632bd1140fcdb6550e55840d4a3` —
  byte-identical to the hash recorded in the Brief 2 report. I read it; I
  did not touch it.
- **Read in v3:** `domain/{promos,bets}/__init__.py`,
  `store/schema/{promos,bets}.py`,
  `workflows/promos/v1/{fb_deployment,promo_store_adapter}.py`,
  `scripts/seed_promos.py`, `ui/api/routers/{racing,bets}.py`,
  `ui/web/src/promos/presets.ts`, `ui/web/src/components/PromoBar.tsx`,
  `ui/web/src/routes/{BetLog,LogPastBet}.tsx`, plus targeted greps over
  `settlement.py`, `record_builder.py`, `LogBetPanel.tsx`.
- **Read in v2 (requirements only):** `frontend/src/utils/promoPresets.js`,
  `src/database.py` (bets-table promo columns), `src/services/betting.py`
  (`settle_bet` refund rule).
- **Read in rebuild folder:** the four pre-reads + `data_sources.md`
  (DR-033 placings picture). **No DB opened**; the placings dependency is
  assessed from source + `data_sources.md` per §4.

---

## Area 1 — Promo reference table (the "single page of serials")

**Verdict: BUILT but two-level + free-form; the single-level,
structured, settlement-readable serial does NOT exist.**

What's built:

- **Schema** (`store/schema/promos.py`): four tables DDL'd in
  FK-dependency order — `warning_catalogue`, `promo_template`, `promo`,
  `promo_events` — with CHECK constraints on the closed enums and the
  `_add_column_if_missing` additive-migration helper already present.
- **`promo_template`** = the *kind-level* catalogue (`promo_template_id`,
  `name`, `kind` ∈ insurance/bonus_winnings/price_boost/ew_cashback/other,
  `mechanic_description`, **`default_terms` = free-form `TEXT`/JSON**).
  Domain model `PromoTemplate` (`domain/promos:722`); `default_terms` typed
  as `dict[str, object] | None` (`:741`).
- **`promo`** = the *per-instance* row (`domain/promos:752`), and the
  docstring states **DR-032 `bets.promo_instance_id` FKs to this table's
  `promo_id`** (`:756-759`). It carries `book_id` + a **run-window**
  (`start_date`/`end_date`, `:769-770`) — exactly the book + run-window the
  brief puts **out of scope**.
- **Adapter CRUD** (`workflows/promos/v1/promo_store_adapter.py`):
  `create_promo`/`get_promo`/`update_promo`/`list_promos` (`:336-403`),
  plus `create_template`/`update_template`/`list_templates` — full
  reference-data surface for *both* levels.
- **Seed** (`scripts/seed_promos.py`): seeds **7 templates + 5 warnings**
  (not credits — confirmed, docstring + body). The seeded `default_terms`
  *are* structured-ish JSON — e.g. `free_bet_if_2nd_or_3rd` carries
  `{"payout_type":"free_bet","places_refunded":[2,3],"refund_cap_default":25}`
  (`seed_promos.py:106-120`) — but inside the free-form blob, **not** typed
  columns, and **template-level defaults**, not per-serial terms.

The presets (the 10 buttons):

- `ui/web/src/promos/presets.ts` `PROMO_PRESETS` (10) **do** carry the
  structured fields a read-back needs: `promo_type`, `promo_return_type`
  (`'cash' | 'free_bet'` — FB-vs-cash), `promo_max_stake` (the cap),
  `insured_positions` (`'2nd' | '2nd_3rd' | …`). But this is **pure
  client-side EV config**: `PromoBar.tsx` writes it into a
  `PromoConfigState` that drives the EV table only — it is **never sent to
  a persist endpoint** and **never linked** to any `promo_template`/`promo`
  row (no id correspondence; preset ids are strings like `ins_25_fb_2nd`,
  not the seed's UUID5s).

The gap (presets-as-EV-config → settlement-readable term-set):

1. **No typed structured terms anywhere.** Insured-spots / FB-vs-cash /
   cap exist *only* as (i) TS preset fields (client, unpersisted) and (ii)
   `default_terms` JSON (persisted, free-form, template-level). A
   settlement read-back ("did this finish in the insured spots, and what's
   the cap?") has no typed field to read.
2. **Vocabulary drift between the two representations.** Preset
   `promo_type` ∈ {insurance, bonus_winnings, **free_bet**, **boosted_odds**}
   vs `PromoTemplateKind` ∈ {insurance, bonus_winnings, **price_boost**,
   **ew_cashback**, other} — `free_bet`/`boosted_odds` aren't kinds;
   `price_boost`/`ew_cashback` aren't preset types. Insured spots are
   `'2nd_3rd'` (TS) vs `places_refunded:[2,3]` (seed JSON). Whichever
   becomes canonical, the other needs reconciling.
3. **Two-level vs single-level.** The brief wants one promo-type table,
   each row a serial-with-terms, bet stores the serial. v3 ships
   *template + instance*. The cleanest single-level home is a structured
   extension of `promo_template` (kind catalogue, no run-window) — but the
   DR-032 link points at `promo` (instance). This fork is unforced and
   load-bearing (O2).

**v2 requirements lift (cited).** v2 stored the term-set as **typed
columns directly on `bets`**: `promo_type`, `promo_insured_positions`,
`promo_return_pct`, `promo_max_stake`, `promo_return_type` (+
`promo_triggered`) — `src/database.py:414-429`. That is the structured
term-set the brief wants made persistent, but achieved by denormalising
the whole set onto every bet row — precisely the bet-schema sprawl named
as v2's worst structural debt. v3's single-serial-reference is the
intended antidote: store the term-set *once* per serial, put only the
serial on the bet.

**Effort to close Area 1:** **M** (confidence: medium). Adding structured
term columns/JSON-schema to a single-level table is small; the cost is the
*decision* (which table is the serial; reconcile the two vocabularies),
not the typing.

---

## Area 2 — Writing the promo onto the bet at log

**Verdict: NOT built. The bet carries no promo reference on either path.
DR-032 `promo_instance_id` is documented, unbuilt.**

Evidence (negative, grepped):

- **No promo column on `bets`.** `store/schema/bets.py` columns
  (`:18-46`) carry `cycle_id`, `strategy_tag`, `is_free_bet`,
  `free_bet_conversion_rate`, `realised_conversion_rate`, … but **no**
  `promo_instance_id` / `promo_id` / `promo_serial`. Grep for those over
  the schema **and** `domain/bets/__init__.py` → **zero hits**. The
  `BetRecord` model's "Promo / free-bet context" block (`:275-278`) holds
  only the free-bet flags, no promo identity.
- **Race path** (`ui/api/routers/racing.py` `log_bet`, `:853-947`):
  builds `SoftBookLogRequest` with `strategy_tag`/`is_free_bet`/
  `free_bet_conversion_rate` (`:906-908`) — **no promo field threaded**.
  `cycle_id = body.cycle_id or str(uuid4())` (`:892`).
- **O1 — `promo_ev_at_log` is accepted then dropped.** `LogBetRequest`
  declares `promo_ev_at_log: float | None` (`racing.py:510`) and
  `LogBetPanel.tsx` sends it (`:231`), but it is **the only occurrence in
  production** — not threaded into `SoftBookLogRequest`, and there is no
  `promo_ev_at_log` column on `bets`. **So the brief's premise that "a
  logged bet persists … a single `promo_ev_at_log` number" is incorrect —
  the bet persists neither the promo serial nor the EV number.**
- **Manual path** (`ui/api/routers/bets.py` `ManualBetCreateRequest`,
  `:400-437`; `build_manual_bet_record`, `record_builder.py:498`): same
  shape — `strategy_tag`/`is_free_bet`/`free_bet_conversion_rate`, **no
  promo identity**.

**What it takes to carry the serial through:** a **clean additive
column** on `bets` (e.g. `promo_serial TEXT` nullable) — the
`_add_column_if_missing` pattern is established and exercised
(`store/schema/bets.py:115-129`, e.g. `settlement_state` at `:120`). The
schema change itself is low-risk and additive. **The honest cost is
breadth, not depth:** the serial must thread through `BetRecord` (frozen
pydantic) → `bet_store_adapter.to_rows` → both request models
(`LogBetRequest`, `ManualBetCreateRequest`) → **both** record builders
(`build_soft_book_bet_record`, `build_manual_bet_record`) → both UI panels
(`LogBetPanel.tsx` race screen, `LogPastBet.tsx`) + their API clients. The
race-screen picker also needs to *emit* a serial — today `PromoBar`
produces unpersisted EV config with no serial to send (depends on Area 1).

**Effort:** **M** (confidence: medium-high on mechanics; medium overall
because it's gated on the Area 1 serial existing). Risk: this is the first
`bets`-schema touch since W12.1 `side`/`commission`; additive-nullable
keeps blast radius to the new field, but the cross-builder/cross-UI thread
is the real surface to test.

---

## Area 4 — Credit-in write + cycle link

**Verdict: credit write does NOT exist (greenfield); the write *zone* and
its template are clear; the validator and cycle-link questions are real
but bounded.**

Where the write lands:

- **No production `free_bet_credited` write anywhere.** `grep
  "FreeBetCreditedPayload("` (non-test) → **only the class definition**;
  every constructor call is under `/tests/`. `grep ".append_event("`
  (non-test) → exactly **two** callers:
  `workflows/promos/v1/fb_deployment.py:166` (the **deploy** write) and
  `ui/api/routers/bets.py:267` (the *bet-mutation audit* log — a different
  event spine). **No promos router exists** (`ui/api/routers/` =
  accounts, bets, health, provisional, racing). Confirms the S168 pool
  finding holds at S178.
- The credit write is a near-mirror of `record_free_bet_deployment`
  (`fb_deployment.py:82-169`): a new `record_free_bet_credit` in the same
  `workflows/promos/v1/` zone, constructing `FreeBetCreditedPayload` +
  `PromoEventBase(event_type=FREE_BET_CREDITED)` and calling
  `PromoStoreAdapter.append_event`. It reads the qualifier bet for
  `account_id`/`book_id`/`account_at_book_id` (all three REQUIRED on
  credits per the FK matrix, `domain/promos:592-594`) and stamps
  `triggering_bet_id`. **This is the promo-event write zone, not
  settlement** — the safety seam holds by construction.

The validator question (size both, lean, do **not** decide):

`FreeBetCreditedPayload` with `credit_source='triggered'` **requires both**
`triggering_bet_id` *and* `triggering_promo_instance_id`
(`domain/promos:330-346`). Under single-level there is no promo *instance*.

- **Option A — relax the validator to bet-linked-only** (require only
  `triggering_bet_id` for `triggered`). Cost: touches a load-bearing
  cross-field invariant **and its symmetric twin** —
  `PromoCashCreditedPayload` carries the identical validator
  (`:474-490`) — plus their tests. Loosens an invariant shared with the
  cash-credit path (O4).
- **Option B — the promo serial doubles as the reference.** The
  single-level promo-type row id *is* `triggering_promo_instance_id`. No
  validator change; the bet already stores the serial (Area 2), so the
  credit reads it back and stamps it. It also keeps the existing
  deploy-side inventory plumbing working unchanged — `AvailableFreeBetItem`
  already surfaces `source_promo_instance_id` + `source_template_id` per
  credit (`racing.py:385-386`, populated at `:727-728`).
- **Leaning (not a decision):** **Option B** — it preserves the invariant
  and the inventory's promo-id plumbing, and is consistent with "the bet
  stores the serial; settlement reads it back." The caveat to flag: the
  field is *named* `…_instance_id` while pointing at a type/serial — a
  semantic stretch, and a doc/rename question for the next session.

Cycle link (Piece A) — **unchanged from the S168 pool map:**
`racing.py:892` still mints a fresh `uuid4()`; the deploy's
`correlation_id` is the *deployed* bet's own cycle (`:935`), not the
qualifier's. `fb_deployment.record_free_bet_deployment` iterates
`consumed_credit_event_ids` in **operator-supplied order** (`:126`), no
oldest-first sort. For a deployed free bet to inherit its qualifier's
cycle: resolve oldest consumed credit → its `triggering_bet_id` → that
qualifier's `cycle_id`, and pass that instead of `uuid4()`. **Piece 0's
source-stamp (`triggering_bet_id` on the credit) hands Piece A its link
for free** — once the credit write exists.

**Supersession tension (flag, don't resolve).** The S168 design defaulted
the credit *amount* to the qualifier's stake (free-form, stake-back). v2's
production rule was `min(actual_stake, promo_max_stake) × return_pct`
(`betting.py:687-695`) — i.e. **capped**. The brief's structured term-set
(Area 1 cap) makes `min(stake, cap)` computable; `FreeBetCreditedPayload.
amount` is `Decimal gt 0` (`domain/promos:311`) and supports either — the
*default policy* (raw stake vs capped) is the open call the structured
terms now enable. Per §2-supersession, this bears on Area 4 and is flagged,
not decided.

**Effort:** credit write **M**, cycle link **S–M** (confidence: medium).

---

## Area 3 — Reading it back at settlement (the delicate seam)

**Verdict: the read-back is an operator-flag step that reads a settled
qualifier off the bet — it does NOT touch settlement, and (the precise
finding) it is NOT blocked on the placings backfill.**

- **Settlement reads win/lose only, no finish position.** A targeted grep
  over the full `settlement.py` (1,354 lines) for
  `promo|free_bet|credit|finish|placing|position|insured|2nd` returns only
  unrelated tokens (`finished_at` timestamps, threshold constants) — **no**
  finish-ordinal logic. `_resolve_settlement_for_bet` (`:319`) resolves
  WINNER→won / LOSER→lost / market-voided / provisional; it cannot tell 2nd
  from last. SHA confirms it's untouched (§0).
- **The placing source is the operator, by DR-lock.** `data_sources.md`
  Part 2 assigns *"Place/ordinal settlement (Safety Net 2nd–4th) → Manual
  (operator flag)"* (`:45`), explicitly *"keeps the operational engine out
  of the analytical source."* So "finished in the insured spots?" is
  answered by the operator's confirm (Area 5), reading the **settled
  qualifier off the bet** (`settlement_state=settled_lost` +
  `strategy_tag=safety_net` + a promo attached), **strictly off** the live
  write path. The credit-in step reads settled qualifiers; it never wires
  into `settlement.py` internals — matching the design's load-bearing seam.
- **Do NOT hook the manual-resolve path either.** `apply_manual_operator_
  resolution` (`settlement.py:1128`) and `ui/api/routers/provisional.py`
  are *inside* the settlement spine (they drive the
  PROVISIONAL→terminal transition). The credit-in confirm is a **separate,
  post-settlement promo write**, not a branch of either — that distinction
  is the seam.
- **The placings dependency, named precisely.** The finishing ordinal
  lives in `capture.db runners.finish_position` (Racing API analytical
  line, `results_source='subscription'`, pulled by VPS
  `subscription/racing_api.py sync_day()`; `data_sources.md:32-34,47`) —
  a **cross-DB read** across the DR-027/028 boundary. **That data is the
  dependency for FUTURE auto-detection (Piece B / auto-settle), which is
  explicitly deferred** (`data_sources.md:60-63` — auto-settle needs free
  bets layable in-tool *and* a decision on the operational engine reading
  an analytical source). **So for Piece 0 the read-back is neither inert
  nor a hard blocker — it does not depend on the placings backfill at all,
  because the operator supplies the placing manually.** This slightly
  corrects the brief's framing: the "earned credits appear once placings
  land" graceful-degradation shape belongs to Piece B, not to the
  pre-cutover credit-in.

**Effort:** **S–M** for the read-back step itself (it's an
operator-confirm → credit-write; the hard part is the gate, Area 5), and
the placings risk the brief worried about is **off the critical path**
(confidence: medium-high).

---

## Area 5 — The two "placed?" confirm surfaces

**Verdict: both surfaces exist but neither asks the question or writes a
credit; making them fire ONE write is the work, and it is gated on
Areas 1–2.**

- **BetLog** (`ui/web/src/routes/BetLog.tsx:506-514`): the
  `placed-confirm-scaffold` button — **disabled, wired to nothing**, title
  "Coming soon — the free-bet credit-in confirm (brief 3)". Inert by
  design. This is the *post-settlement* surface (bet was logged live, then
  auto-settled `settled_lost`; operator opens the tuck-in later).
- **LogPastBet** (`ui/web/src/routes/LogPastBet.tsx`): the settle-at-entry
  Won/Lost/Void toggle (`SETTLEMENT_OPTIONS`, `:38-41`; posted as
  `settlement_state`, `:146`). The bet is written settled at entry, but
  **no "placed in the insured spots?" question is asked** — so a
  past-logged losing insurance qualifier never earns its credit.
- **Making both ask one question + fire one write:** a single shared
  credit-in endpoint/client both surfaces call.
  - BetLog: enable "Placed?" only on a `settled_lost` + `safety_net` +
    promo-attached bet; on *yes* → call credit-in.
  - LogPastBet: when outcome=Lost ∧ strategy=safety_net ∧ promo attached,
    surface the same inline question at entry and fire the **same** write.
- **The gate** (per brief): `strategy_tag = safety_net` ∧ settled-lost ∧
  **a promo attached**. The promo-attached predicate **cannot be evaluated
  today** — there is no promo on the bet (Area 2). **So Area 5 is blocked
  on Areas 1 + 2.**
- **"Single write, not two" needs an idempotency guard.** Nothing today
  prevents a second credit for the same qualifier (there's no credit path
  at all). The two surfaces must converge on one write keyed to the
  qualifier (e.g. once-per-`triggering_bet_id`); no such guard exists (O6).

**Effort:** **M** (confidence: medium) — the UI wiring is routine; the
gate + idempotency + the shared-write convergence are the substance.

---

## Area 6 — Overall buildable read

**Effort per area:**

| Area | Build-vs-needed | Effort | Confidence |
|---|---|---|---|
| 1 — promo table | two-level + free-form exists; single-level structured serial doesn't | **M** | medium |
| 2 — write-on-bet | not built; additive column + cross-builder/UI thread | **M** | med-high (mech.) |
| 4 — credit write | greenfield; mirrors deploy write; validator + cycle-link calls | **M** (+ S–M cycle) | medium |
| 3 — read-back seam | operator-flag read; off settlement; **not** placings-blocked | **S–M** | med-high |
| 5 — confirm surfaces | both exist inert; one shared gated write | **M** | medium |

**Split: cleanly TWO builds.**

- **Build 1 — promo-attach foundation:** settle the single-level table +
  structured terms (Area 1) → additive `bets` serial column + thread both
  paths + both UIs (Area 2). Self-contained; ships value (promos are
  finally persisted/queryable) even before credit-in.
- **Build 2 — credit-in + cycle link:** the credit write (Area 4) + the
  read-back framing (Area 3) + the two confirm surfaces (Area 5) + Piece A
  cycle inheritance. **Hard-depends on Build 1** — the Area 5 gate needs a
  promo on the bet.

**Single-session feasibility.** Build 1 is plausibly one session *if* the
Area 1 single-vs-two-level reconciliation is decided up front (that's the
wildcard, not the typing). Build 2 is plausibly one session *given Build
1*: the credit write mirrors an existing one, the cycle link is S–M
(pool-mapped), the confirm surfaces are bounded UI. Attempting both in one
session is **not** advised — the schema thread (Build 1) and the
greenfield write + gate (Build 2) are each a full session's testing
surface.

**Named risks, front-and-centre:**

1. **The Area 1 model reconciliation** (two-level `promo`/`promo_template`
   vs single-level serial; two disconnected term representations + vocab
   drift) — the biggest *design* risk; everything downstream keys off
   which table is the serial.
2. **Bet-schema touch breadth** (Area 2) — low-risk per column, wide per
   thread (builders × request models × UIs).
3. **Validator change** (Area 4) — touches a shared cross-field invariant
   (FB + cash credit) if Option A; Option B avoids it.
4. **Settlement read-back seam** (Area 3) — *low* risk: the operator-flag
   design keeps it provably off `settlement.py`; the main discipline is
   not hooking the manual-resolve path.
5. **Placings dependency is OFF the cutover path** — a de-risking finding:
   the brief's worry is a Piece-B concern; Build 2 does not wait on it.

---

## Area 7 — Open findings (operator-requested latitude)

- **O1 — `promo_ev_at_log` is accepted but silently dropped**
  (`racing.py:510`, sent by `LogBetPanel.tsx:231`, persisted nowhere, no
  column). The API contract implies it's captured; it isn't. Corrects the
  brief's grounding premise. Decide whether it should persist alongside the
  new serial or be removed from the contract.
- **O2 — the two-level vs single-level fork is unforced and load-bearing.**
  `promo` (instance, has run-window + book) is what DR-032 points at;
  `promo_template` (kind catalogue, no run-window) is the closer fit for
  "single page of serials." The build must pick a serial home; reusing
  `promo_template` may strand the `promo` table, or vice-versa.
- **O3 — structured terms live twice, disconnected, with vocabulary
  drift** (TS presets vs seed `default_terms` JSON; `promo_type` vs
  `kind`; `'2nd_3rd'` vs `places_refunded:[2,3]`). Whichever becomes
  canonical, the other is reconcile-or-discard.
- **O4 — the cash-credit sibling is in the blast radius.**
  `PromoCashCreditedPayload` shares the triggered-fields validator
  (`domain/promos:474-490`) and there's a live `bonus_winnings (cash)`
  preset. An Area-4 Option-A relax touches it; the build should decide
  whether cash promo-on-bet + cash credit-in is in scope or explicitly out.
- **O5 — `_coerce_uuid` soft-coupling** (`fb_deployment.py:59-79`) falls
  back to a *fresh* UUID for any bet id not matching `bet-<uuid>`. A credit
  write stamping `triggering_bet_id` should use the real bet UUID, not a
  coerced fallback, or the Piece-A cycle resolve can chase a phantom id.
- **O6 — no once-per-qualifier idempotency** exists for crediting; needed
  so the two Area-5 surfaces can't double-credit. Natural key:
  `triggering_bet_id`.
- **O7 — `CreditStatus` (provisional/finalised/rejected) is unused by the
  inventory derivation** (per S168 pool review §4.3:
  `compute_free_bet_inventory` doesn't filter on `status`). A credit-in
  write choosing FINALISED vs PROVISIONAL has no derivation effect today —
  fine for Piece 0 (write FINALISED), but a latent gap if Piece B later
  leans on provisional credits.

---

## Self-assessment

- **Coverage:** all seven areas answered with file/line evidence; every
  BUILT/NOT-BUILT call carries a citation or a named negative grep. The
  three load-bearing negatives — no credit write, no promo column on the
  bet, no promos router — are each grep-proven (non-test scoped).
- **Confidence:** high on the negatives (Area 2 schema, Area 4 no-write,
  settlement isolation via SHA + whole-file grep) and on the Area 3
  placing-source DR-lock. Medium on the effort sizes and on the Area 1
  single-vs-two-level recommendation surface (I sized it; the operator
  decides). Medium on the Area 4 validator leaning — both options are
  viable; I named B and its caveat without choosing.
- **Not traced exhaustively (honest gaps):** I did not re-read
  `promo_derivations.py` / `balance_derivation.py` in full — I relied on
  the S168 pool review's verified map for the inventory/balance read side
  and confirmed only the `source_promo_instance_id` surfacing in
  `racing.py`. I did not open the orchestrator or `bet_store_adapter.to_rows`
  line-by-line — the Area 2 thread is named from the request/builder
  signatures, not a full trace of every persistence hop. No tests were run
  (read-only). No DB was opened, so the seed's actual row contents and the
  presence/absence of any hand-seeded credit events were assessed from
  source only.
- **The "report partial and stop" clause was not needed** — the map
  completed within the single session.
- **Length:** ~490 lines — over the 250–450 target by ~40, flagged here
  per §8. Areas 1 and 4 earned the overage: the two-level/single-level
  tension and the validator sizing both needed their evidence laid out
  rather than asserted. No padding; the negatives carry the citations they
  need, and the v2 requirements-lift is cited inline rather than summarised.
- **Repo integrity:** no file in `bethub-v3` or `bethub-v2` was created,
  edited, moved, or deleted; no DB read or write; no git state-changing op;
  `settlement.py` SHA-proven untouched. The only file written is this
  report, in the rebuild folder.

### Open questions for the operator-Claude triage (not chased into code)

- Q1. **Which table is the serial** — extend `promo_template` (kind
  catalogue, single-level fit) or repurpose `promo` (DR-032 target, but
  carries the run-window the brief drops)? (O2 — gates Build 1.)
- Q2. **Validator** — relax to bet-linked-only (Option A) or serial-as-
  reference (Option B)? Affects the cash-credit twin either way (O4).
- Q3. **Credit amount default** — raw stake-back (S168 design) or
  `min(stake, cap)` now that structured terms make the cap readable (v2's
  production rule)? (Area 4 supersession tension.)
- Q4. **Cash promos** — is `bonus_winnings (cash)` / insurance-cash
  credit-in in scope for cutover, or FB-only? (O4.)
