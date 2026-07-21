# Settlement-correctness fix — design proposal

**Session:** S222 design pass (operator-reviewed; follows `settlement_correctness_investigation.md`).
**Type:** Read-only design proposal for operator review — **no code touched, no test changed, no flag flipped, no brief locked, no DB/Betfair write.**
**Codebase:** bethub-v3 @ HEAD `e2638fa` (byte-identical; dirty tree — the in-progress settlement-worker build — unchanged).
**Anchor:** 2026-07-03 ACST (DR-021).
**Grounds:** `settlement_correctness_investigation.md` (S222 diagnosis, leans Option A), `settlement_pending_sweep_nullfix_report.md` (Code's STOP report F1–F3), `settlement_liveproof_plan.md` (the "correct, not just settled" / park-not-overpay proving bar).
**Governing DRs:** DR-032 (Betfair settlement spine), DR-033 (settlement Betfair-only / placings analytical), DR-030 (module boundaries), DR-027/028 (two-DB boundary), DR-021 (Adelaide anchors).

---

## Context — why this exists

The auto-settlement worker (built in the working tree; flag `BETHUB_SETTLEMENT_WORKER` **OFF**) has two
confirmed money-path gaps that block cutover **B2** (`settlement_liveproof_plan.md`):

1. **Pending-state gap** — nothing in the codebase ever writes `settlement_state="pending"`; live bets
   are born NULL and stay NULL, so the worker's `("pending",)` sweep is permanently empty
   (`settlement_correctness_investigation.md` §1; `settlement_pending_sweep_nullfix_report.md` F1).
2. **LAY inversion** — the resolver maps the Betfair runner's *market-objective* status to a settlement
   state (WINNER→SETTLED_WON, LOSER→SETTLED_LOST), but the P&L layer reads that state as the *bet's own*
   perspective. For a LAY these are exact inverses, so a winning lay would be booked as a full-liability
   loss and a losing lay as a win — a silent ledger inversion (investigation §2; report F3).

The single live bet in the operational store is the repro bet: `bet-df31ffcd-…`, **side=LAY,
settlement_state=NULL**, a $5.26 lay at 3.5 on a WIN market — so **both** gaps bite it directly. (DB
state distribution: exactly one row, NULL, LAY.)

This proposal resolves the two open calls the investigation left to the operator (Option A vs B; lay
dead-heat/Rule-4 liability), designs the LAY fix across **both** resolvers, specifies the complete
bounded fix that must land together, and surfaces two forward-looking scope items the blast-radius
traces uncovered. The one-line nullfix brief is **superseded**. The worker stays **OFF** throughout and
until the whole thing re-proves.

*Evidence base: first-hand reads of every anchor at HEAD `e2638fa` (dirty tree) + three read-only
blast-radius sub-agents (Option-A create path, Option-B NULL convention, LAY resolver/guard/side). All
anchors below are confirmed; confidence is high unless noted.*

---

## 1. Q1 — pending-state fix: Option A vs Option B (resolved)

### 1.1 Comparative blast-radius traces

**Option A — stamp `SettlementState.PENDING` at create (in the live builder).**

- **Write-path map (3 live entry sites, all through the builders):**
  1. Orchestrator hedge: `orchestrator.py:767` `build_hedge_bet_record` → `_write_with_retry` (`:787`) →
     `to_rows`/`write_bet_record` → SQLite INSERT (`store/repositories/bets.py:548-608`).
  2. Orchestrator soft-book: `racing.py:934` `log_soft_book_bet` → `orchestrator.py:1150`
     `build_soft_book_bet_record` → same INSERT path.
  3. **Direct lay path (the repro-bet path), bypasses the orchestrator:** `racing.py:1094`
     `build_hedge_bet_record(… construction=LAY_AGAINST_BACK …)` → `to_rows`/`write_bet_record` → INSERT.
  Because the stamp goes in the **builder**, all three are covered by one edit. (Note: W7's stated
  "orchestrator populates at write-time" — `domain/bets/__init__.py:318` — would *miss* site 3; the
  builder stamp is strictly more complete than W7's phrasing.)
- **Adapter is a faithful pass-through:** `bet_store_adapter.py:69-73` writes `settlement_state.value`;
  a `PENDING` write round-trips through real SQLite (proven: `test_settlement.py:1176`
  `test_sqlite_settlement_state_round_trip`).
- **Cost is low / no hidden reliance on NULL-at-create:** **zero** tests assert a freshly-created live
  bet is `None` (`test_record_builder.py`, `test_orchestrator.py`, `test_racing.py` — none reference
  `settlement_state`). No validator, BetRecord constructor, or INSERT rejects `PENDING`
  (`record_builder.py:226-264` validators never touch it; schema is plain `TEXT`, `store/schema/bets.py:39`).
  The only implicit reliance on NULL is the sweep's `IN ('pending')` itself — the bug.
- **Behaviour changes:** the intended one — PENDING bets become visible to the sweep. Latent bonus:
  `is_past_settlement_window` (`domain/bets/__init__.py:371`, returns False unless state==PENDING) starts
  working for live bets (currently NULL-blind; no runtime consumer today, so latent). All other
  consumers already treat NULL≡PENDING (balance layer `_PENDING_SETTLEMENT_STATES`; BetLog `pending`
  filter `bets.py:283`; edit/delete fences `bets.py:1103/1182` allow both NULL and "pending") → no-ops.
- **The one existing NULL repro bet is NOT covered by A alone** (A only affects *new* writes). Cover it
  with a **targeted single-row backfill** (see §1.3). No backfill/migration precedent exists to mirror,
  but `update_settlement_state` (`bets.py:783`) has no current-state guard so a one-row update applies
  cleanly.

**Option B — teach the worker/store that NULL means pending.**

- **Store surface:** add an `IS NULL` OR-branch to `SQLiteBetRecordStorage.list_unsettled_bets`
  (`bets.py:838`, mirroring the existing `_bets_filter_sql:1403-1415`); widen `settlement_states`
  `tuple[str,...] → tuple[str|None,...]` on **exactly three** signatures — Protocol (`:198-204`),
  SQLite (`:826`), in-memory (`:441`); no third implementer (`FailingStorage` inherits). (`list_bets`/
  `count_bets` are already typed `tuple[str|None,...]` — the widening is idiomatic here.)
- **Sweep:** widen the PENDING sweep (`settlement.py:1026`) to `("pending", None)`. **Leave the
  PROVISIONAL sweep (`:1289-1292`) and both `list_provisional_settlement_bets` wrappers on
  `("provisional",)`** — PROVISIONAL is always explicitly stamped, never NULL. (Adversarial: implement
  the IS NULL branch *conditionally* on `None ∈ states`, mirroring `_bets_filter_sql`; do **not**
  hardcode an unconditional `OR IS NULL`, or it would leak NULL into the PROVISIONAL pass.)
- **False-green trap (must mitigate):** the in-memory store honours `None` via set-membership
  (`bets.py:448`) while SQLite `IN ('pending',NULL)` matches **zero** NULL rows (three-valued logic).
  The F2 sweep test and every pass-loop test run **in-memory**, so a fix could go green with SQLite
  still broken. B therefore *requires* a SQLite-path regression test. Home + template:
  `tests/store/repositories/test_bets_betlog.py:168` (`test_list_bets_settlement_state_filter_includes_null`).
  The only existing SQLite test of `list_unsettled_bets` (`test_settlement.py:1233`) *is* the trap — it
  seeds only PENDING rows, never NULL.
- **Spec-citing test inverts:** `test_pass_sweeps_only_pending_bets` (`:607-639`) asserts a NULL bet is
  **not** swept, citing §2.6/§3.2. B inverts this deliberate prior decision.
- **Over-sweep hazards B introduces (A avoids):**
  - **Soft-book legs.** `build_soft_book_bet_record` leaves `settlement_state` NULL but the leg carries a
    real `betfair_market_id`, and the sweep has **no `leg_role`/`book_or_exchange` filter**. So B would
    sweep soft-book (book-side) legs and try to Betfair-settle them — a money-path behaviour change
    nobody decided. B needs an added Betfair-leg guard (`book_or_exchange='betfair'`) to prevent it.
    (side=None→BACK, so the LAY inversion doesn't touch them — but *whether they should auto-settle at
    all* is the open question; see §4.)
  - **Legacy / pre-W6.5 NULL rows.** B sweeps *all* NULL rows. The current DB has exactly one (the repro
    target), so this is empty-in-practice now, but forward-looking it wants a `placed_at` lookback floor.
- **Pros:** self-heals the existing NULL bet and any future stray-NULL Betfair rows (a real robustness
  property against the exact recurrence class); aligns the worker with the balance layer's existing NULL
  tolerance; leaves the create path frozen.

### 1.2 Recommendation — **Option A (stamp PENDING on the hedge/Betfair builder) + targeted backfill**

**I agree with the investigation's Option-A lean — but I reached it by pressure-testing, not accepting,
and I strengthen it with evidence the investigation did not have.** The pivotal corrections:

- **A's headline weakness dissolves.** The investigation's own caveat (and my interim view) was "A can't
  re-prove the existing NULL bet without B's store work or a risky blanket `UPDATE … WHERE
  settlement_state IS NULL`." But covering *one known row by `bet_id`* is a **targeted, idempotent,
  reversible, non-value state-queue move** — not the blanket update the investigation dismissed. It
  settles nothing; it just enqueues the bet for the (LAY-fixed) worker under supervision. So B is **not**
  load-bearing.
- **A scopes to exactly the right population.** Stamping PENDING only on the **hedge (Betfair) builder**
  makes "PENDING = enqueued for Betfair auto-settlement," which naturally **excludes soft-book legs**
  (not stamped → stay NULL → not swept) and **legacy NULL rows** — both of which B over-sweeps and must
  add guards to exclude. This matches the worker's purpose (the Betfair settlement worker) and DR-033.
- **A keeps the spec/test honest.** `test_pass_sweeps_only_pending_bets` and §2.6/§3.2 ("NULL is
  out-of-scope for the PENDING pass") stay **true** under A — live bets are genuinely PENDING, NULL is
  genuinely anomalous. B *inverts* that deliberate decision.
- **A sidesteps the false-green trap entirely.** A writes a real `'pending'` string both stores handle
  identically; it never depends on the in-memory-vs-SQLite `NULL-in-IN` divergence F1 flagged. B's
  central risk is A's non-issue.
- **A is cheap and complete.** Breaks 0 tests; no store/Protocol/sweep change; covers all three entry
  sites incl. the orchestrator-bypassing lay path (more complete than W7); honours the domain docstring
  ("PENDING is the default at bet entry", `domain/bets/__init__.py:110`) and realises W7's intent.

**B's one genuine advantage is self-healing** against a future create path that forgets to stamp
PENDING (the recurrence class of this very bug). If the operator values that over minimal surface, adopt
the **defense-in-depth variant** below instead — it captures self-healing *and* the soft-book exclusion.

**Defense-in-depth variant (operator's call, if self-healing is wanted):** keep A (stamp PENDING on the
hedge builder) **and** make the sweep NULL-tolerant **but guarded to Betfair legs** —
`WHERE (settlement_state='pending' OR settlement_state IS NULL) AND book_or_exchange='betfair' AND
event_start < cutoff`. This sweeps the NULL repro bet **without a backfill**, excludes soft-book, and
self-heals future stray Betfair NULLs — at the cost of the store/Protocol change, the F2 inversion, the
betfair-leg predicate, and the mandatory SQLite-path test. If adopted, the backfill is unnecessary.

**Net recommendation:** **primary = A (hedge-builder stamp) + one targeted backfill** for its minimal,
correctly-scoped, spec-preserving, trap-free surface; **optional upgrade = the guarded-NULL variant** if
self-healing is judged worth the larger store surface. Either way the create path becomes honest and the
soft-book/legacy populations stay out of the auto-sweep.

### 1.3 The repro-bet backfill (execution step, done carefully — not in this design pass)

One-time, targeted, after a DB backup, with the worker still OFF and the LAY fix landed:
`UPDATE bets SET settlement_state='pending' WHERE bet_id='bet-df31ffcd-c841-4593-a3bd-506f4dd41de2'
AND settlement_state IS NULL;` — verify exactly one row affected; reversible to NULL. It moves the bet
into the pending queue; it settles nothing (won/lost still flows through the re-proven worker under
supervision). *(Omitted entirely if the guarded-NULL variant is chosen.)*

---

## 2. Q2 — LAY fix in the resolver

### 2.1 The mapping (bet-relative, side-aware)

For `record.side == BetSideTag.LAY` (NULL side stays BACK, matching `_is_lay`,
`balance_derivation.py:164`), invert only the two **clean terminal** states:

| Runner status | BACK (unchanged) | LAY (inverted) | Lay P&L (`_bet_cash_return`) |
|---|---|---|---|
| WINNER, clean | SETTLED_WON | **SETTLED_LOST** | net −L (full liability) ✓ |
| WINNER, dead-heat / material reduction | PROVISIONAL (guard parks) | **PROVISIONAL (unchanged)** | manual reduced-liability settle |
| LOSER | SETTLED_LOST | **SETTLED_WON** | net +S(1−c) collect ✓ |
| REMOVED (runner) / market voided | VOIDED | **VOIDED (unchanged)** | net 0 ✓ |

Confirmed money math (`balance_derivation.py:190-280`): lay `settled_won → L + S(1−c)` (net +S(1−c));
`settled_lost → 0` (net −L); `voided → L` (net 0); pending reserves liability L. The pass loops do **no**
payout math — they only count states for telemetry (`settlement.py:1073`) and persist
`decision.new_state.value`. Every money-sensitive consumer (balance derivation, promo credit-gap
`credit_gap.py:81`, BetLog P&L `bets.py:558`) reads `settlement_state` **bet-relatively**; nothing
re-derives won/lost from raw runner status. **So the resolver's `new_state` is the single, sole
inversion point** — patching the balance layer instead would double-invert.

### 2.2 Both resolvers must invert (the investigation missed one)

The mapping exists in **exactly two** places, both in `workflows/bet_entry/v1/settlement.py`:

- `_resolve_settlement_for_bet` (PENDING pass): clean-WINNER → SETTLED_WON (`:714`), LOSER →
  SETTLED_LOST (`:726`).
- `_resolve_provisional_for_bet` (PROVISIONAL pass): clean-WINNER → SETTLED_WON (`:947`), LOSER →
  SETTLED_LOST (`:960`).

The investigation's file table (§3, row 2) lists **only** the PENDING resolver (`:688-736`). But a lay
parked to PROVISIONAL (unreadable-factor `fallback_flagged`, or runner-not-found) is re-resolved by the
**second** resolver on later cycles — without the inversion it would settle to the wrong state. **The
LAY inversion must be applied to both** (`record.side == LAY`, at `:714/:726` and `:947/:960`). The
Betfair-client reader (`clients/betfair_client/v1/settlement.py`) does no state mapping — nothing else
to touch.

The **manual** path `apply_manual_operator_resolution` (`:1483`) and the **settle-at-entry** manual
builder (`record_builder.py:583`) take an operator-chosen terminal state directly — **bet-relative by
construction, no inversion** (only a UI-clarity note, §2.4).

### 2.3 The guard needs no change — a refinement over the investigation

`_evaluate_winner_guard` (`settlement.py:451-550`) parks a WINNER on `dead_heat_count>0` **or** a
material/unreadable removed-runner reduction. **Those trigger conditions are *exactly* the conditions
under which a losing lay's liability is reduced** (a dead-heat or Rule-4 deduction on the winning
selection reduces what the backer is paid, hence what the layer owes). So the guard's **park** trigger
is already correct for lays with **zero modification** — only its *clean* terminal (SETTLED_WON) becomes
side-aware. The LOSER branch (a **winning** lay) needs **no** guard: a winning lay's collect `S(1−c)` is
fixed and unaffected by dead-heat/Rule-4 on other runners (a dead-heating laid selection is a WINNER,
not a LOSER, so it routes to the guarded branch). Confirmed: LOSER branch has no guard in either
resolver; voided lay nets 0 (`balance_derivation.py:244/319`; test
`test_balance_lay_branch.py:213`).

### 2.4 Interim vs compute — **park to PROVISIONAL** for reduced-liability losing lays

Recommend the **park-to-PROVISIONAL interim** (reuse the guard unchanged), **not** computing reduced lay
liability:

- Computing reduced lay liability (Rule-4 on liability, dead-heat liability division) is genuine new
  money-path math, unbuilt, and **not needed for Strategy-1 win-market proving**.
- Parking mirrors the worker's existing "park anything uncertain" posture (liveproof §7).
- Booking full −L on a reduced-liability losing lay does **not** violate the strict "never overpay"
  invariant (full −L over-states your loss — conservative), **but** it is still *incorrect*, and the
  liveproof bar is "**correct, not just settled**". So park it for manual settlement rather than book a
  knowingly-wrong full −L.

**Operational-clarity notes (not code blockers):** (a) the `RemovedRunnerVerificationRecord` prose is
backer-framed ("winner {sel} … → {action}"); for a lay, a `paid_full` record means "booked full
liability (settled_lost); winner-side reduction judged immaterial (<2.5% on a win market)" — the
factors/action are accurate, only the prose assumes a backer. Optional tidy: add `side` to the record.
(b) The manual queue (`ui/api/routers/provisional.py`) *displays* the objective runner status
(WINNER/LOSER); an operator resolving a parked **lay** must pick the bet-relative terminal — surface the
lay's perspective in the labelling. Capture both in the operator run-book.

---

## 3. Q3 — the complete bounded fix (all edits land together)

> Ordering constraint: the pending-state fix and the resolver inversion **must ship together**. Enabling
> the worker to see the repro LAY *before* the resolver inverts would settle it to the **wrong** state —
> the exact half-fix the worker-OFF hold guards against.

**Code — pending-state (recommended primary, Option A):**
- `workflows/bet_entry/v1/record_builder.py` — `build_hedge_bet_record` (return at `:324`) adds
  `settlement_state=SettlementState.PENDING`. **Leave `build_soft_book_bet_record` unstamped** (soft-book
  stays NULL → not swept → manual, as today). `build_manual_bet_record` (`:509`, terminal-only)
  untouched. → No store/Protocol/sweep change; F2 test unchanged.
- *(Guarded-NULL variant instead, if chosen: the `bets.py` IS-NULL branch + 3-signature type widen +
  `book_or_exchange='betfair'` predicate + `settlement.py:1026` widen + F2 inversion + SQLite test;
  drops the backfill.)*

**Code — LAY inversion (both resolvers):**
- `_resolve_settlement_for_bet` clean-WINNER (`:714`) + LOSER (`:726`): add `record.side == LAY`
  inversion. `_resolve_provisional_for_bet` clean-WINNER (`:947`) + LOSER (`:960`): same. Guard,
  REMOVED, and market-voided branches unchanged.

**Tests:**
- **Create-path test** — `build_hedge_bet_record` → `settlement_state == PENDING`;
  `build_soft_book_bet_record` → `settlement_state is None` (documents the deliberate asymmetric scoping).
- **SQLite-path regression** — that a builder-created (PENDING) live bet **is** swept end-to-end via the
  real `SQLiteBetRecordStorage` (extend/beside `test_settlement.py:1233`; round-trip already at `:1176`).
  *(Guarded-NULL variant: instead assert a NULL **Betfair** bet IS swept and a NULL **soft-book** bet is
  NOT — the false-green-killing test, mirroring `test_bets_betlog.py:168`.)*
- **LAY settlement tests (both resolvers)** — laid selection WINS → **SETTLED_LOST**; laid selection
  LOSES → **SETTLED_WON**; a BACK bet still maps WINNER→WON (regression); a lay with a
  dead-heat/material reduction → **PROVISIONAL** (parked); a voided lay → **VOIDED** (net 0). Note: the
  record factory `_make_record` (`test_settlement.py:138`) has no `side` param today — add LAY records;
  do **not** mutate the existing BACK mapping tests (`:267/:295`).
- **F2 test** — **unchanged** under Option A (NULL-not-swept stays true). *(Inverted only under the
  guarded-NULL variant.)*

**Governance / spec:** under Option A the §2.6/§3.2 "pending population = PENDING" definition stands and
the code is simply brought into line (PENDING now produced at entry). *(The guarded-NULL variant instead
reconciles the definition to "PENDING or NULL on a Betfair leg" and retires the F2 "NULL excluded"
wording.)*

---

## 4. Two forward-looking scope items the traces surfaced (flag for decision — not re-prove blockers)

Neither blocks the re-prove (the repro bet is a Betfair hedge lay; the DB has no soft-book or legacy
rows today), but both matter before the worker is left **on** for normal running:

1. **Should the worker auto-settle soft-book (book-side) legs at all?** DR-033 fixes Betfair as the
   settlement *outcome source* but does not clearly authorise settling **book** legs off the Betfair
   read (book void/Rule-4/promo semantics can differ). **Recommended safe default: keep soft-book
   settlement manual (as today) — Option A does this for free by not stamping the soft-book builder; the
   guarded-NULL variant needs the `book_or_exchange='betfair'` predicate.** If the operator wants
   soft-book auto-settled, that is a separate money-path decision needing its own validation of the
   soft-book P&L path.
2. **Legacy NULL rows** — none in the current DB, but if a legacy/imported DB ever carries pre-W6.5 NULL
   rows, only Option A (which ignores NULL) is safe by default; the guarded-NULL variant should add a
   `placed_at` lookback floor (as `post_settlement_void.py:70` already does) to avoid churning aged rows.

---

## 5. Q4 — money-path invariant & worker stays OFF

- Invariant held: the resolver inversion closes the catastrophic silent overpay (a losing lay booked as
  +collect). The retained guard parks reduced-liability losing lays (conservative). The only residual is
  sub-2.5% win-market reductions paid full — **symmetric** with the backer side, surfaced via
  `paid_full` verification records — unchanged and accepted for Strategy-1 proving.
- `BETHUB_SETTLEMENT_WORKER` stays **OFF** until all edits land, the backfill (if using Option A) is
  done, **and** the re-prove passes.

### Re-prove plan (against the repro LAY, after all edits land)
1. Confirm the repro LAY (`bet-df31ffcd-…`) is a **candidate** (PENDING after backfill under A; or swept
   via the guarded-NULL branch under the variant).
2. Read the actual Betfair result for Gossamer Glow (sel `100232235`, market `1.259636589`).
3. Confirm the resolved state is the correctly **inverted** LAY state: Gossamer Glow **won** →
   **SETTLED_LOST**; **lost** → **SETTLED_WON**; any dead-heat/material reduction → **PROVISIONAL**.
4. Confirm the money-path invariant held (park-not-overpay); then — and only then — proceed with the
   S220 live-proving window (`settlement_liveproof_plan.md` §4/§5). B2 stays paused until proven.

---

## Open calls that remain the operator's (money-path — not locked here)
1. **Option A (recommended) vs the guarded-NULL defense-in-depth variant** — trade minimal, spec-
   preserving, trap-free surface (+ one targeted backfill) against self-healing (+ larger store surface,
   F2 inversion, SQLite test).
2. **Soft-book auto-settle** — recommended default: keep manual (§4.1).
3. **Park vs compute reduced lay liability** — recommended: park-to-PROVISIONAL interim (§2.4).
4. Approve the bounded brief (hedge-builder stamp + both-resolver inversion + create-path & SQLite &
   LAY tests [+ backfill], or the variant), handed to Code as one all-together change; worker OFF until
   it re-proves.

## Verification of this design (before briefing)
All anchors read first-hand at HEAD `e2638fa` (dirty tree): both resolvers, the guard, both sweep
passes, both `list_unsettled_bets` impls + `_bets_filter_sql` + the Protocol, the create builders, the
store adapter (`settlement_state`/`side` pass-through + `from_rows` rehydration), `balance_derivation`
lay math + `_PENDING_SETTLEMENT_STATES`, the F2 test, the manual-resolution path, and reconciliation's
`pre_settlement_pending` (detail-only, writes `match_status` not `settlement_state`). Three read-only
blast-radius sub-agents confirmed/extended every claim; their findings are folded in above.

---

## Evidence log (all read-only)
- **HEAD `e2638fa`** — no git write op; no code, test, flag, or launcher touched. Only this rebuild-folder document was written.
- **Direct reads:** `workflows/bet_entry/v1/settlement.py` (both resolvers, `_evaluate_winner_guard`, `_is_place_market`, both pass loops, both sweep call sites, `apply_manual_operator_resolution`); `store/repositories/bets.py` (Protocol + SQLite + in-memory `list_unsettled_bets`, `_bets_filter_sql`); `workflows/bet_entry/v1/record_builder.py` (both live builders + manual builder); `workflows/bet_entry/v1/bet_store_adapter.py` (`to_rows`/`from_rows`); `workflows/balances/v1/balance_derivation.py` (lay branch, `_PENDING_SETTLEMENT_STATES`, `_is_lay`, `_lay_liability`); `domain/bets/__init__.py` (`SettlementState`, `BetSideTag`, `BetRecord.side`/`settlement_state` defaults, `is_past_settlement_window`); `ui/api/settlement_worker.py`; `workflows/bet_entry/v1/reconciliation.py` (`pre_settlement_pending` detail); `tests/workflows/bet_entry/v1/test_settlement.py` (F2 + mapping tests).
- **Three read-only blast-radius sub-agents:** Option-A create path (3 entry sites, 0 breaking tests, no NULL-reliance); Option-B NULL convention (call sites, consumer list, in-memory/SQLite divergence, Protocol surface, SQLite test home, over-sweep hazards); LAY resolver/guard/side (both resolvers, single inversion point, side plumbing, guard asymmetry, existing coverage gap).
- **Confidence:** create-path NULL mechanism, no-`"pending"`-producer, LAY P&L inversion, both-resolvers requirement, single inversion point — **certain**. Soft-book/legacy over-sweep under B — **high** (that the code would sweep them); **medium** on the soft-book behavioural intent (open call §4.1). Backfill safety — **high** (targeted, non-value, reversible).
- **Bet-safety:** worker remains OFF; no money path exercised; no live Betfair or DB write this pass; capture side untouched; bethub-v3 byte-identical.
