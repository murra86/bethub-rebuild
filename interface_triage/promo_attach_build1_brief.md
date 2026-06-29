# Build 1 — promo-attach foundation — build brief

**Status:** locked draft (Session 180). Read-write Claude Code build.
Single bounded session.
**Output:** `interface_triage/promo_attach_build1_report.md`
**Repo (read-write):** `/Users/tim/Desktop/Projects/bethub-v3`
**v2 (read-only, requirements only):** `/Users/tim/Desktop/Projects/bethub-v2`
**Tests:** v3 baseline is `uv run pytest` (NOT bare `python3` — the repo
is a `uv` project; system `python3` is 3.11 and fails collection).

---

## §1 — What this brief is, and is not

- A **build**: it adds the promo-attach foundation to v3 — a structured
  promo catalogue, the serial + EV stamped onto each bet at log time, and
  both entry paths wired to persist them. It builds **Build 1 only** of
  the two-build split locked at Session 179.
- It is **not** the credit-in build. No free-bet/cash credit write, no
  settlement read-back, no "placed?" confirm surfaces — all of that is
  **Build 2** and is explicitly out of scope here (§9).
- It does **not** touch the settlement engine in any way. `settlement.py`
  is proven byte-identical at close (§7). Build 1 attaches a promo to a
  bet; it never reads a result back or settles anything.
- **Surprises become findings, not detours.** If something doesn't match
  this brief's anchors, or a cleaner seam appears, flag it in the report's
  findings section — do not chase it into a fix or expand scope.
- Remediation of anything found routes to the next operator-Claude triage
  session, not to Code's report.

## §2 — Why this work exists

v3's free-bet pool can be drawn down but nothing fills it (S168). To run
a full Strategy 1 (Safety Net) cycle, the tool has to know a free bet was
earned when an insurance qualifier places — and that starts with the bet
knowing **which promo it was placed under**. Today it doesn't: the
race-screen promo buttons are display-only EV presets; a logged bet keeps
a strategy tag + (supposedly) one EV number, but **no promo identity**,
and even that EV number is silently dropped at the API (S179 finding O1).

The Session 179 triage of the read-only review
(`promo_attach_credit_in_review_report.md`) split the work in two. **This
brief is Build 1 — the promo-attach foundation.** It ships value on its
own: once a bet carries its promo serial + terms, promos are finally
persisted and queryable, regardless of when credit-in (Build 2) lands.

Operator calls carried in from S178/S179 and locked into this brief:

- **Single-level model.** One promo-type reference table, each row a
  serial carrying its own terms. The bet stores the serial. No separate
  promo *instance* row (book is already on the bet; promos mature at the
  event, so there's no run-window to model). The home is the
  **kind-catalogue table** (`promo_template`), not the instance table.
- **Emulate v2's promo set.** The initial catalogue is seeded from the
  promos the operator actually runs in v2 — the v2-proven term-set, lifted
  for requirements only (no v2 code ported).
- **Keep the scope open for later additions.** New promos appear over
  time; adding one later must be a **data add through the catalogue, not a
  code change**. The catalogue is the single source and the pickers read
  from it. An in-app catalogue-management screen is later work, out of
  scope here — but nothing in Build 1 may hard-code the promo set in a way
  that blocks a later add.
- **Persist the promo EV number** on the bet (resolves O1) on the same
  schema touch that adds the serial.
- **Cash promos are in scope** alongside free-bet promos.

## §3 — Pre-reads

Required, in order:

1. `interface_triage/promo_attach_credit_in_review_report.md` — the S179
   read-only review. This brief's anchors come from it; it is the grounded
   map of what exists vs what's needed. Read it first.
2. `interface_triage/promo_attach_credit_in_review_brief.md` — the review
   brief (scope context, Areas 1–7).
3. `store/schema/promos.py` — the four promo tables; `promo_template` is
   the catalogue this build extends; `_add_column_if_missing` is present
   but unused (Build 1 is its first call here).
4. `store/schema/bets.py` — the `bets` DDL + the `_add_column_if_missing`
   additive pattern (the `side`/`commission` W12.1 additions are the
   template to follow).

Reference-only (on demand, not required):

- `interface_triage/free_bet_credit_in_design.md` — the S168 credit-in
  design Build 2 serves (context only; nothing in it is built here).
- `data_sources.md` — DR-033 (placings are the operator's manual flag;
  off Build 1's path entirely).

## §4 — System access

- **v3 read-write**, Mac filesystem direct at
  `/Users/tim/Desktop/Projects/bethub-v3`. Edit only the anchors named in
  §5. No drift into adjacent code.
- **v2 read-only**, `/Users/tim/Desktop/Projects/bethub-v2` — requirements
  lift only (the promo set + terms). The canonical source is
  `frontend/src/utils/promoPresets.js` (the 10 promos used in practice);
  cross-check terms against the v2 bets-table promo columns
  (`src/database.py` ~:414–429) and the refund rule
  (`src/services/betting.py` ~:687–695). **Do not port v2 code.**
- **No database access for inspection** beyond what the test suite and
  the seed script touch. No live operational-store reads, no capture.db.
- **Dirty working tree expected** (in-flight `betfair_client` work +
  untracked `domain/`, `workflows/`, `ui/`, `scripts/`, `migrations/` per
  the review §0). Dirty-tree discipline is a hard limit (§9): no git
  state-changing operations; `git diff <file>` after each edit; `git
  status` unchanged (bar the report) at close.
- Adelaide local timestamps (ACST/ACDT) per DR-021 for every time
  reference in the report.

## §5 — Build scope

Six pieces. File/line anchors are starting points drawn from the S179
review — **verify each against the live tree before editing** (the tree
is in-flight; line numbers drift). Where an anchor has moved, use the
named symbol, not the line number.

### §5.1 — Structured terms on the promo catalogue (`promo_template`)

The catalogue row becomes the settlement-readable home for a promo's
terms. Add four **typed** fields to `promo_template` (`store/schema/
promos.py` `_PROMO_TEMPLATE_DDL`), via the additive pattern — add each to
the DDL constant (for fresh installs) **and** a matching
`_add_column_if_missing` call in `apply_migrations` (for existing DBs).
These are the first additive-migration calls in `promos.py`.

The four fields (these are the structured terms a credit read-back will
need in Build 2):

- `refund_positions TEXT` — JSON array of finishing positions that trigger
  the refund, e.g. `[2]` or `[2,3]`. Nullable (non-insurance promos have
  none). Matches v2's `promo_insured_positions` and the seed's existing
  `places_refunded`.
- `return_type TEXT` — `CHECK (return_type IN ('free_bet','cash'))`.
  Nullable. Free-bet-vs-cash.
- `return_pct REAL` — the return percentage as a fraction (e.g. `1.0` for
  100%-back, `0.5` for 50%-back, `0.25` for 25%). Nullable. **Load-bearing
  in the Build 2 credit calc** — must be stored.
- `cap TEXT` — the advertised cap as a Decimal-as-string (matching the
  `requested_stake`/`matched_stake` convention on `bets`). Nullable
  (uncapped promos). **Stored as a term for analytics only — NOT used in
  any calc in Build 1, and per the S179 decision not in the Build 2 credit
  calc either** (the operator bets at-or-under cap, so it never changes the
  number; it is recorded, not computed against).

The domain model `PromoTemplate` (`domain/promos/__init__.py`, ~:722)
gains the four typed fields. The existing free-form `default_terms` blob
is **retained** for any genuinely non-structured mechanic notes, but the
four fields above move to typed columns and are canonical — `default_terms`
is no longer the home for insured-spots / return-type / return-pct / cap.

The adapter (`workflows/promos/v1/promo_store_adapter.py`
`create_template`/`update_template`/`list_templates`, ~:277–330 — note the
sibling promo-instance methods `create_promo` etc. at ~:336–403 are left
untouched) carries
the four new fields through create/read/update. **This CRUD surface must
stay fully functional** — it is the path by which a new promo is added
later without a schema or code change (the "scope open for additions"
requirement). Do not bypass or hard-code around it.

### §5.2 — Serial + EV columns on `bets`

Two additive columns on `bets` (`store/schema/bets.py`), following the
exact `side`/`commission` (W12.1) precedent — add to `_BETS_DDL` **and** a
matching `_add_column_if_missing` call in `apply_migrations`:

- `promo_template_id TEXT` — nullable. The promo serial: the
  `promo_template.promo_template_id` the bet was placed under. **Soft
  reference, no inline FK** — `bets` carries no outbound FK constraints
  today (only `bet_legs → bets`); match that convention. Naming: this is
  deliberately `promo_template_id`, not `promo_instance_id` — it points at
  the catalogue serial, not the instance table, and the name should say so
  (this is the DR-032 amendment made concrete; see §11).
- `promo_ev_at_log REAL` — nullable. The promo/adjusted EV number shown at
  log time (resolves O1 — today it is accepted by the API and dropped).

The domain model `BetRecord` (`domain/bets/__init__.py`, the "Promo /
free-bet context" block ~:275–278) gains `promo_template_id: str | None`
and `promo_ev_at_log: float | None`. The store adapter's row-mapping
(`bet_store_adapter.to_rows` and its read-side inverse) must persist and
re-hydrate both — **trace the full persistence hop and confirm the
round-trip**, since the review named this path from signatures but did not
trace every hop line-by-line. The full hop runs `BetRecord` ↔
`to_rows`/`from_rows` ↔ the `BetRow` dataclass + the `write_bet_record`
INSERT / `read_bet_record` SELECT in **`store/repositories/bets.py`** —
that file is an **authorised edit target** for the two columns (confirmed
at the S180 Code gate), even though this section's header names only the
adapter row-mapping. A bet written with a serial must read back
with the same serial.

This is the first `bets`-schema touch since W12.1. The change is additive
and nullable, so the blast radius is the new fields — but the value
threads through `BetRecord` (frozen pydantic) → adapter row-mapping → both
request models → both record builders → both UIs (§5.4, §5.5). That
breadth is the real test surface, not the column add itself.

### §5.3 — Seed the catalogue from v2's promo set + reconcile the two reps

The catalogue's initial content emulates v2. The canonical source is v2's
`frontend/src/utils/promoPresets.js` — **10 promos**: six insurance
variants ($25/$50 × FB/cash × 2nd / 2nd+3rd), a bare free bet, two
bonus-winnings (FB 100% / cash 25%), and one boosted odds. Seed each as a
`promo_template` row with the four typed terms populated, via
`scripts/seed_promos.py` (which today seeds 7 generic templates + 5
warnings — reconcile it to the v2-derived 10).

Reconcile the two existing term representations into this one canonical
set (O3), resolving the vocabulary drift:

- **Kind enum is canonical** (`insurance`/`bonus_winnings`/`price_boost`/
  `ew_cashback`/`other`). The two preset types that aren't kinds:
  `boosted_odds` → `price_boost` (clean); `free_bet` (the bare-free-bet
  preset, all terms null) is a **deployment marker, not a promo offering**
  — it maps to the existing `is_free_bet` path on the bet, not to a
  catalogue refund-terms row. Decide and state: either a `kind='other'`
  catalogue row with null terms, or no catalogue row (picker offers it as
  "free bet, no promo"). Flag the call in the report.
- Insured spots: `'2nd_3rd'` (TS) / `'2nd'` → `refund_positions` `[2,3]` /
  `[2]`. Return type / pct / cap map straight across from the preset
  fields (`promo_return_type`, `promo_return_pct` as a fraction,
  `promo_max_stake`).

After this piece, the v3 `presets.ts` representation is **superseded as a
source of truth** by the catalogue — see §5.4 for how the picker reads
from the catalogue instead of the hard-coded array.

### §5.4 — Race-screen path: catalogue-driven picker → serial on the bet

Today the race-screen promo buttons (`ui/web/src/promos/presets.ts`
`PROMO_PRESETS` + `ui/web/src/components/PromoBar.tsx`) are a hard-coded
array that drives the EV table only — the selection is never sent to a
persist endpoint and carries no serial.

Build 1 makes the picker **catalogue-driven**:

- Add a read endpoint that returns the catalogue rows (serial + name +
  kind + the four structured terms) — a GET on the promos surface (no
  promos router exists today; add a minimal read route under
  `ui/api/routers/`, DR-030-placed). This is the "scope open for
  additions" mechanism: a new catalogue row appears in the picker with no
  frontend change.
- `PromoBar`/`LogBetPanel` render the picker from that endpoint and carry
  the selected `promo_template_id`. The EV table computes from the
  selected row's structured terms (same numbers as today, sourced from the
  catalogue rather than the hard-coded preset).
- On log, the race path threads `promo_template_id` + `promo_ev_at_log`:
  `LogBetRequest` (`ui/api/routers/racing.py` ~:510 already declares
  `promo_ev_at_log`; add `promo_template_id`) → through `log_bet`
  (~:853–947) into `SoftBookLogRequest` → into `build_soft_book_bet_record`
  → persisted on the bet. **Anchor correction + authorised edit targets
  (S180 Code gate):** `SoftBookLogRequest` is *defined* in
  **`workflows/bet_entry/v1/orchestrator.py`** (~:467; `racing.py:906` is
  only its construction site), and its hand-off to `SoftBookRecordInputs`
  is in the same file (~:1401). So threading the two fields through the
  race path edits `orchestrator.py` (the request class + the inputs
  mapping) and `SoftBookRecordInputs` (`record_builder.py` ~:169) — both
  are **authorised edit targets** for Build 1, not scope drift. (The manual
  path in §5.5 does **not** go through the orchestrator.)

### §5.5 — Log Past Bet path: promo picker → serial on the bet

The manual path mirrors the race path so a late-logged bet carries its
promo identically:

- `ui/web/src/routes/LogPastBet.tsx` gains a promo picker reading the same
  catalogue endpoint (§5.4).
- `ManualBetCreateRequest` (`ui/api/routers/bets.py` ~:400–437) carries
  `promo_template_id` + `promo_ev_at_log`.
- `build_manual_bet_record` (`workflows/bet_entry/v1/record_builder.py`
  ~:498) persists both onto the bet.

Both paths converge on the same two `bets` fields (§5.2) and the same
catalogue (§5.1). No new term representation is introduced.

### §5.6 — Tests + settlement-seam proof

- **Python:** `uv run pytest -q`. Capture the pre-build count; all green
  at close, no regressions.
- **Frontend:** `tsc -b` clean (the type-check the BetLog/manual-entry
  builds used).
- New coverage:
  - Schema migration idempotency for both tables (`promo_template` four
    fields; `bets` two fields) — re-running `apply_migrations` on an
    already-migrated DB is a no-op.
  - Catalogue round-trip: a row written through the adapter with the four
    typed terms reads back identical (incl. `refund_positions` JSON).
  - Both entry paths: a bet logged with a `promo_template_id` +
    `promo_ev_at_log` persists and re-hydrates both (race path + manual
    path).
  - The catalogue read endpoint returns the seeded v2 set.
- **Settlement seam proof (bet-safety gate):** record the SHA-256 of
  `workflows/bet_entry/v1/settlement.py` at session start and at close —
  it must be **byte-identical**. Build 1 does not touch it. (Recorded
  hash from the Brief 2 / S178 reports:
  `9e07a75d3ab85741d5c3346521dbca25d09da632bd1140fcdb6550e55840d4a3`.)

## §6 — Sequencing within session

Suggested order (Code may deviate if cleaner — say so in the report):

1. §5.1 catalogue terms (schema + domain + adapter).
2. §5.2 `bets` serial + EV (schema + domain + adapter round-trip).
3. §5.3 seed from v2 + reconcile.
4. §5.4 race path (read endpoint → picker → persist).
5. §5.5 manual path.
6. §5.6 tests throughout, settlement SHA at start and close.

**If it won't all fit one session:** the clean split point is **after
§5.4** — schema + persistence + the catalogue-driven race path is a
coherent, shippable stop. §5.5 (manual path) then §5.6 polish becomes the
tail. Report partial-but-coherent and stop rather than rushing both UIs.
The dynamic-picker endpoint (§5.4) is the piece most likely to stretch the
budget; flag early if so.

## §7 — Empirical verification

Capture before-and-after so the report shows what moved:

- **Test baseline:** `uv run pytest -q` count pre-build and post-build
  (+N, 0 regressions). `tsc -b` clean post-build.
- **Schema:** `PRAGMA table_info(promo_template)` and
  `PRAGMA table_info(bets)` before and after — the four / two new columns
  present after, idempotent on re-run.
- **Catalogue:** the seeded v2 set present and readable through the
  endpoint (row count + a spot-checked insurance row's terms).
- **Round-trip:** one race-path bet and one manual-path bet, each written
  with a serial + EV and read back identical.
- **Settlement SHA:** `settlement.py` byte-identical start → close.

## §8 — Output spec

- Single file: `interface_triage/promo_attach_build1_report.md`.
- Sections: a §0 baseline (HEAD, dirty-tree state, settlement SHA, test
  count, what was read), one section per build piece (§5.1–§5.6) with what
  was built + evidence, an empirical-verification section (the §7
  before/after), a findings section (anything surfaced, incl. the §5.3
  bare-free-bet reconciliation call), and a self-assessment (coverage,
  confidence, what wasn't traced, any partial-stop).
- Length: ~250–400 lines. Over is fine if a piece earns it (flag in
  self-assessment); don't pad.
- Does **not** contain: any credit-in write, read-back, or confirm-surface
  work; any settlement edit; any DR amendment text (governance is
  operator-Claude's); a "Build 2 brief"; v2 code ported across.

## §9 — Hard limits (non-negotiable)

- **Build 1 only.** No `free_bet_credited` / `promo_cash_credited` write,
  no settlement read-back, no "placed?" confirm surface, no idempotency
  guard, no cycle-link work — all Build 2.
- **Never touch `settlement.py`** (read or write) — SHA byte-identical at
  close. Do not touch `apply_manual_operator_resolution` or
  `ui/api/routers/provisional.py` (inside the settlement spine).
- **No Racing-API / placings / capture.db work** — that's a separate
  parallel brief; placings are the operator's manual flag (DR-033) and
  play no part in Build 1.
- **No in-app catalogue-management UI** — adding promos in-app is later
  work. Build 1 only keeps the door open (catalogue is the data source;
  the adapter CRUD stays intact; the picker reads from the catalogue).
- **No schema sprawl.** Terms live once on the catalogue row; only the
  serial + EV go on the bet. Do not denormalise the term-set onto `bets`
  (that was v2's worst debt and the reason for the rebuild).
- **Additive schema only.** No column drops, no table drops, no rename of
  existing columns. New columns nullable.
- **Dirty-tree discipline.** No `git add`/`commit`/`stash`/`restore`/
  `checkout`/`reset`. Read tree state at start; edit only §5 anchors;
  `git diff <file>` after each edit; `git status` unchanged (bar the
  report) at close. If a dirty region intersects an edit anchor, stop and
  report it rather than editing through it.
- **Named anchors only** — no drift into adjacent code "while here".
- **Single bounded session.** If it won't fit, partial-but-coherent at the
  §6 split point, then stop and report.

## §10 — What happens after Code's session

The next operator-Claude session reads
`promo_attach_build1_report.md`, triages it (inventory pass, classify by
operational impact, surface operator-relevant findings — incl. the
bare-free-bet reconciliation call from §5.3), confirms the bet-safety gate
(settlement SHA), and — on a clean triage — drafts the **Build 2 brief**
(credit-in + cycle link). Build 2 hard-depends on Build 1: its "placed?"
confirm gate needs a promo on the bet, which Build 1 provides. Code does
not write the Build 2 brief; this build feeds it.

The **Racing-API placings backfill** runs as its own parallel brief — it
is the future auto-surfacing enabler (Piece B), not a dependency of Build
1 or Build 2.

## §11 — Cross-references

- **Review:** `promo_attach_credit_in_review_report.md` (S179),
  `promo_attach_credit_in_review_brief.md` (S178). This brief's anchors
  derive from the review.
- **Design (context):** `free_bet_credit_in_design.md` (S168, Piece 0 +
  A) — served by Build 2.
- **DRs:**
  - **DR-032** (Betfair canonical / the promo-on-bet link) — **amended
    alongside this brief.** The link target shifts from the `promo`
    instance row to the `promo_template` catalogue serial (single-level);
    the bet column is `promo_template_id`. The amendment text is authored
    by operator-Claude in `decisions.md`, not by Code.
  - **DR-030** (module boundaries) — the new promos read route is placed
    per DR-030; `store/schema/` stays stdlib-only.
  - **DR-031** (tech stack) — additive `_add_column_if_missing` migration;
    Alembic adoption stays deferred to its own later brief.
  - **DR-019** (derived P&L on read) — unaffected; no P&L change here.
  - **DR-027/028** (cross-DB boundary) — **not triggered.** Build 1 is
    single-DB (the v3 operational store only); no capture.db read.
  - **DR-033** (data-source roles) — placings are the operator's manual
    flag; off Build 1's path.
- **Excluded (parking-lot):** Build 2 (credit-in + cycle link, carrying
  O5 real-UUID stamp / O6 idempotency / O7 FINALISED); the placings
  backfill; the in-app catalogue-management UI; Piece B (auto-surfacing);
  partial free-bet draw-down.
