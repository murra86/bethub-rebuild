# BetLog codebase-review brief (Code, read-only)

**Status:** locked, Session 170 (2026-06-20 ACST).
**Type:** read-only codebase review. Code inspects and
reports findings. Code builds nothing, edits nothing.
**Serves:** `interface_triage/betlog_scope.md` (BetLog scope,
locked S169) — pre-cutover brief 1 of 3.
**Output:** `interface_triage/betlog_review_report.md`
(findings only).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3`.

---

## §1 — What this brief is and is not

This is a **read-only codebase review**. Code reads the v3
bets data layer, API surface, settlement seam, and frontend
scaffold, and reports whether the BetLog page described in
`betlog_scope.md` is buildable as scoped — naming every gap,
risk, and decision the build brief will have to resolve.

- **Single bounded Code session.** If the review needs more
  than one session, that is itself a finding — surface it
  and stop. Partial-but-coherent beats complete-but-lost.
- **Code builds nothing and edits nothing.** No new files,
  no edits to existing files, no schema changes, no tests
  written, no git operations. Inspection and report only.
- **Surprises become findings, not detours.** If Code finds
  something off (a schema field that contradicts the scope,
  a boundary the endpoint can't satisfy), it records the
  finding and moves on — it does not fix it or redesign.
- **Remediation routes to the next operator-Claude session**,
  not to this report. The report informs the build brief;
  it does not pre-write it.

## §2 — Why this work exists

The operator is cutting v3 over for live operational use and
must be able to **see his book**. v3 has no bet-viewing
surface today — a settled-lost insurance qualifier vanishes
into the data with nowhere it shows up, and the free-bet
"placed?" confirm (brief 3) has no home until BetLog exists.

`betlog_scope.md` locked the BetLog shape at S169. Before
committing Code to build it, this review validates the scope
against the real v3 codebase — the same de-risking move as
the S165–166 racing-page review that fed the S167 fix set.
The build brief is drafted next session off what this review
finds.

## §3 — Pre-reads

**Required (read before starting):**

1. `interface_triage/betlog_scope.md` — the locked BetLog
   scope. This brief reviews the codebase *against* it; Code
   must hold it in full.

**Reference (read as each review area needs):**

- v2 port-basis (what BetLog ports *from*, for shape only —
  v2 is a different stack, do not copy code):
  `bethub-v2/frontend/src/components/BetsPage.jsx`,
  `PendingSettlementTab.jsx`, `SettledHistoryTab.jsx`.
- `decisions.md` — DR-030 (module boundaries / import-linter),
  DR-032 (Betfair canonical + cycle axis), DR-019 (derived
  state on read), DR-022 (account / book / account-at-book
  vocab).

## §4 — System access

- **Mac filesystem, READ-ONLY**, against
  `/Users/tim/Desktop/Projects/bethub-v3`. Code reads source;
  it writes exactly one file — the report at §8's path.
- **No database access required.** This is a code review, not
  a data query. Do not open, copy, or query any `.db` file.
- **Dirty tree — do not touch it.** The v3 tree is dirty
  (streaming/placement work modified; the operational store,
  domain modules, `migrations/`, `scripts/`, and `ui/web/`
  untracked). Because this review is read-only, the discipline
  is simple: **no `git add/commit/stash/restore/checkout/
  reset`, no edits to any tracked or untracked file.** Reading
  untracked files is fine. Leave `git status` identical to how
  it started.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for
  every time reference in the report.

## §5 — Review areas

Seven areas, each anchored on something the build depends on
being true. For each: answer the questions, cite the file +
line/region the answer comes from, and flag any gap between
what `betlog_scope.md` assumes and what the code actually
provides. Where a gap exists, name what the build brief would
have to do about it — but do not do it here.

### §5.A — Bets read surface

**Anchors:** `store/schema/bets.py` (DDL — already grounded:
`bets` + `bet_legs`), `store/repositories/bets.py` (~33 KB,
the read/write methods), `domain/bets/__init__.py` (~14 KB,
domain models).

**Questions:**

1. The scannable row needs: selection/runner, side, free
   marker, stake @ odds, state, P&L, book + persona. Map each
   to a real field or a clean derivation. Confirmed available
   from schema: `bet_legs.betfair_selection_name` (runner),
   `bets.side`, `bets.is_free_bet` (free marker),
   `bets.matched_stake`/`matched_price` (stake@odds),
   `bets.settlement_state`/`match_status` (state),
   `bets.book_or_exchange` + `bets.account_at_book_id`
   (book + persona). **P&L is not a stored column** — confirm
   how it is derived on read (DR-019) and whether a
   derivation already exists anywhere, or the endpoint must
   compute it.
2. The tuck-in detail needs: bet id, exact placed time,
   commission, full promo terms, cycle chain. Map each.
   Confirmed: `bets.bet_id`, `bets.placed_at`,
   `bets.commission` (NULL → 8% fallback — confirm where that
   fallback lives so the endpoint reads it consistently),
   `bets.cycle_id` (the cycle-chain key). **"Full promo terms"
   has no obvious home** — `bets.strategy_tag` is the closest
   field. Determine what promo metadata actually exists on a
   bet and whether the row's promo tag + the detail's "full
   terms" can both be satisfied, or whether this is a scope
   gap the build brief must resolve (e.g. promo terms live in
   a promos table, joined by some key).
3. **Persona name:** `account_at_book_id` is an id. Confirm
   the join path from a bet to a human-readable persona +
   book label (likely via the accounts store /
   `store/repositories/accounts.py`), and whether it is one
   query or an N+1 risk for a list.
4. **Cycle chain:** grouping bets by `cycle_id` gives the
   insurance → free-bet → deployed chain. Confirm `cycle_id`
   is populated on real bets and that the chain is
   reconstructable read-side (order within a cycle, net
   result) without writing anything.

### §5.B — Filter feasibility

**Anchors:** same read surface as §5.A, plus the accounts
store for the persona/book dimensions.

**Questions:**

1. Are all six filters queryable from the bets data layer:
   **account** (persona — all that persona's bets),
   **account-at-book** (one persona at one book), **book**
   (all personas at one book — the account-health lens),
   **promo type**, **date range** (on `placed_at`), **state**
   (Pending / Settled / All)? For each, name the field/join
   the filter would key on.
2. The **book** filter is the load-bearing account-health
   lens — "how hard am I running this one bookie across all
   my identities." `bets.book_or_exchange` is the field;
   confirm it is a clean book identifier (not free-text drift)
   and that filtering across personas by book is a single
   query.
3. **Promo type** filter: depends on §5.A.2 — if promo
   metadata is thin, flag that this filter may be limited to
   `strategy_tag` granularity rather than true promo type.
4. Flag any filter that is **not** cleanly queryable as-is and
   what the build brief would need (an index, a join, a
   derived column on read).

### §5.C — API surface

**Anchors:** `ui/api/routers/racing.py` — grounded: existing
GETs `list_races` (~L614), `get_log_context` (~L707),
`list_accounts` (~L753); POSTs `log_bet` (~L853),
`place_lay` (~L994); DI providers `get_bet_storage` (~L167),
`get_accounts_storage` (~L176), `get_db_connection` (~L185);
response helpers `_envelope_to_http` (~L303),
`_models_to_jsonable` (~L335). Other routers:
`ui/api/routers/{accounts,provisional,health}.py`.

**Questions:**

1. **There is no bets-list / bets-feed GET endpoint today** —
   confirm. The build needs one (the read-side feed powering
   the list + filters). Recommend where it belongs:
   **extend `racing.py`** (which already hosts the non-racing
   `list_accounts` GET) **or a new bets router**
   (`ui/api/routers/bets.py`). Give the DR-030 module-boundary
   read (import-linter) for each option — does a new router or
   an extended `racing.py` keep the `ui → domain/store`
   boundaries clean, and does `.importlinter` already define
   contracts the new code must satisfy?
2. The existing GET feeds use the `_envelope_to_http` /
   `_models_to_jsonable` response shape and the DI providers
   above. Confirm the bets-feed endpoint can reuse them, and
   name the provider it would depend on (`get_bet_storage`
   and/or `get_accounts_storage`).
3. **Filtering + pagination:** does the existing read surface
   support server-side filtering and any pagination, or would
   the endpoint pull all bets and filter in memory? Flag the
   shape (1,900+ bets exist in v2; v3 grows from zero but the
   design should not assume tiny).
4. **Edit + delete** need write endpoints (PATCH/PUT + DELETE)
   — confirm none exist today and name where they belong
   (same router as the feed). The *semantics* of delete are
   §5.D; here just confirm the endpoint slots.

### §5.D — Edit / delete safety  *(settles an operator call)*

**Anchors:** `store/repositories/bets.py`, `domain/bets`,
`bets`/`bet_legs` schema (FK `bet_legs.bet_id → bets.bet_id`),
plus anything that references a bet downstream:
`workflows/bet_entry/v1/` (settlement, reconciliation,
record_builder), and the cycle/promo stores
(`store/repositories/{promos,cash_flow,ops}.py`).

**The operator call this answers:** when he deletes a
wrongly-logged bet, should it be **hard delete** (row gone)
or **soft delete** (marked-removed, retained for audit)? His
provisional lean is hard-delete for an unsettled, un-cycled
bet; block delete on anything settled or part of a free-bet
cycle (edit instead). This review tells him whether that is
structurally safe.

**Questions:**

1. **What is linked downstream of a bet?** Map every
   reference to `bet_id` / `cycle_id` across the store and
   workflows — `bet_legs` (FK), cycle attribution, settlement
   state, reconciliation bookkeeping, promo/free-bet credit
   events, cash-flow events, ops log. List them.
2. **Does a hard delete orphan anything?** If a bet is part of
   a cycle (`cycle_id` shared with a triggered free bet), or
   has settlement/reconciliation/promo rows pointing at it,
   would deleting the row leave dangling references or break a
   cycle's net calculation? Is there a FK cascade, or nothing?
3. **Edit:** which fields are safe to edit post-hoc (stake,
   price, promo tag) vs which would corrupt settlement or
   cycle logic if changed after the fact? Recommend the safe
   editable set.
4. **Verdict:** is the operator's lean (hard-delete only when
   unsettled AND un-cycled; otherwise block) the right rule,
   or does the code support something simpler/safer? State the
   rule the build brief should implement.

### §5.E — Settlement seam (do-not-touch boundary)

**Anchors:** `workflows/bet_entry/v1/settlement.py` (~49 KB),
plus `reconciliation.py`, `orchestrator.py` in the same dir.

**Questions:**

1. **Pin the exact read interface** settlement uses off a bet
   — the fields it reads from `bets`/`bet_legs` (confirmed at
   S169: it reads `leg.betfair_market_id` /
   `betfair_selection_id` to match the market). Name the exact
   functions + line regions so the build brief can state
   precisely what BetLog's read/edit/delete must not disturb.
2. **Is there any write path from a viewing/edit action that
   could reach settlement?** Confirm BetLog's edit/delete can
   be built so it never calls into the settlement engine —
   name the clean seam (repository-level writes that bypass
   settlement vs orchestrator paths that trigger it).
3. **The "placed?" confirm forward pointer (brief 3):**
   identify where the eventual confirm *write* would land —
   the promo / free-bet credit-in write zone (per the S168
   `free_bet_credit_in_design.md`). Name the seam only; this
   review does not design or build it. BetLog scaffolds the
   button; the write is brief 3.

### §5.F — Frontend scaffold

**Anchors:** `ui/web/` — `src/App.tsx`, `src/main.tsx`,
`src/App.module.css`, `src/index.css`, `src/App.test.tsx`,
`vite.config.ts`, `package.json`, `tsconfig*.json`,
`eslint.config.js`.

**Questions:**

1. **What exists today?** The frontend is an early Vite +
   React + TypeScript scaffold. Report: is there any routing
   / nav (react-router or equivalent), or is `App.tsx` a
   single view? A new BetLog page needs somewhere to mount and
   a way to navigate to it — name what the build adds vs
   reuses.
2. **Data-fetching pattern:** how does the frontend currently
   call the API (fetch wrapper, react-query, bare `fetch`,
   typed client)? The BetLog page should follow the existing
   pattern, not invent one. If there is no pattern yet, flag
   that the build brief must establish one (and recommend the
   lightest fit).
3. **Component / styling conventions:** CSS modules
   (`App.module.css` suggests yes), component file layout,
   any shared UI primitives. Name what a new page conforms to.
4. **vitest setup:** `App.test.tsx` exists — confirm vitest is
   wired and runnable, and what the test command is, so the
   build brief can name it as a gate.

### §5.G — Test baseline

**Anchors:** repo root (`pyproject.toml`, `uv.lock`,
`.python-version`), `tests/`, `ui/web/package.json` scripts.

**Questions:**

1. Capture the **current Python baseline**: run
   `uv run pytest -q` (DR-031 — v3 is a `uv` project; bare
   `python3 -m pytest` fails on httpx). Report pass/fail/skip
   counts. This is the number the build brief's gate is
   measured against ("suite N → N, no regressions").
2. Capture the **current vitest baseline**: the TS test
   command from `ui/web/package.json` and its pass count.
3. Note any already-failing or skipped tests so a post-build
   comparison is not misread.

### §5.H — Overall read

After A–G, give a single plain verdict: **is BetLog buildable
as scoped in `betlog_scope.md`, or does the scope need
adjusting first?** Name anything in the scope that the code
can't cleanly support (a row field with no home, a filter
that can't be queried, a promo-terms gap, an unsafe delete)
and what the build brief would have to change or add. This is
the section the next operator-Claude session triages first.

## §6 — Sequencing within session

Suggested order; deviate if a different order reads cleaner —
this is a review, not a build, so dependencies are light:

1. §5.G test baseline first (cheap, runs while context loads).
2. §5.A bets read surface → §5.B filters (B builds on A).
3. §5.C API surface (depends on knowing the read surface).
4. §5.D edit/delete safety → §5.E settlement seam (D and E
   share the downstream-reference map; do them together).
5. §5.F frontend scaffold.
6. §5.H overall read last — it synthesises A–G.

## §7 — Success criteria

This review succeeds when the report:

- Answers every question in §5.A–§5.G with a file + line/region
  citation for each answer (not assertion without anchor).
- States a clear delete-safety rule (§5.D verdict).
- Pins the settlement read seam precisely (§5.E.1).
- Captures both test baselines (§5.G).
- Gives the §5.H buildable / not-buildable verdict in plain
  language.

A "buildable with these N adjustments" verdict is a success,
not a failure — naming the adjustments is the point.

## §8 — Output spec

- **Single file:** `interface_triage/betlog_review_report.md`
  (Mac path: `/Users/tim/Desktop/Projects/bethub-rebuild/
  interface_triage/betlog_review_report.md`).
- **Structure:** one section per review area (A–H), each with
  its questions answered and anchors cited; then the §H overall
  read; then a short self-assessment (what was covered, any
  area Code couldn't fully answer and why).
- **Length:** roughly 300–550 lines. Range, not a hard line —
  exceed it if a finding genuinely warrants, and flag the
  overshoot in the self-assessment.
- **The report does NOT contain:** fixes, code, a build plan,
  the build brief, schema changes, or recommendations beyond
  "the build brief should resolve X." Findings + the buildable
  verdict only.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021.

## §9 — Hard limits

Non-negotiable. Code:

- **Edits no file** and **builds nothing.** Read-only review;
  the only write is the one report file at §8.
- **No git operations** of any kind. Leaves `git status`
  identical to start.
- **No schema changes**, no migrations, no `.db` access.
- **Does not touch the settlement engine** —
  `settlement.py` / `reconciliation.py` / `orchestrator.py`
  are *read for §5.E*, never modified.
- **No scope creep into briefs 2 or 3.** Manual after-the-fact
  entry (brief 2) and free-bet credit-in (brief 3) are out of
  scope. §5.E.3 may *name* the credit-in write seam as a
  forward pointer — naming only, no design, no build.
- **Single bounded session.** If it won't fit, that's a
  finding — surface and stop.

## §10 — What happens after Code's session

The next operator-Claude session (S171) reads
`betlog_review_report.md`, triages §5.H first, then the
per-area findings. If buildable as-is → draft the BetLog
**build** brief off the confirmed anchors. If buildable with
adjustments → fold the adjustments into the build brief (and,
if any touch the locked scope, update `betlog_scope.md`
first). Then brief 2 (manual entry) and brief 3 (free-bet
credit-in) follow in sequence. Code does not write the build
brief — that is the next Chat session's work.

## §11 — Cross-references

- **Scope:** `interface_triage/betlog_scope.md` (locked S169).
- **DRs:** DR-030 (module boundaries / import-linter — §5.C),
  DR-032 (Betfair canonical + cycle axis — §5.A, §5.E),
  DR-019 (derived state on read — P&L, §5.A), DR-022
  (account / book / account-at-book vocab — §5.B), DR-021
  (Adelaide timestamps).
- **Prior:** `sessions/SESSION_169.md` (BetLog scoping +
  three-brief resequence); the S165–166 racing-page review is
  the precedent for this read-only-review-feeds-build pattern.
- **Excluded (parking lot / later briefs):** manual after-the-
  fact entry (brief 2), free-bet credit-in (brief 3), the
  launcher brief (F9/F10), and the `capture.db` retention
  check (brief 2's first step — not this review).

---

*End of brief. Locked S170. Read-only review; findings only;
builds nothing.*
