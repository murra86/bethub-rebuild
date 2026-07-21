# W4 follow-up Code brief — REST-fetch fallback for streaming-blocked placement + price_source field + naming canonicalisation

**Status:** locked Session 96.
**Audience:** Claude Code, single bounded session.
**Scope:** workflow-layer mini-build closing W4 report §7.4
(streaming-blocked retry behaviour) and §7.6
(`soft_book_combined_price` NULL for single-leg), with paired
paragraph-level §13 contract clarification.
**Estimated size:** 400–500 lines.
**Estimated test delta:** +8 to +12 tests; pytest baseline
232 → 240–244 expected.

---

## §1 — What this brief is and is not

This brief commissions a workflow-layer mini-build plus one
paragraph-level contract clarification. Six coordinated changes
sit inside `bethub-v3/workflows/bet_entry/v1/` plus one
contract paragraph at
`dr029/2_7_api_contract_versioning/betfair_client_contract.md`.

**This brief is:**

- A mini-build that adds a REST-fetch fallback path to the
  bet-entry orchestrator when Betfair Streaming drops mid-
  placement, so Strategy 1 entries near the jump don't fail
  when streaming connection lapses (operationally significant
  per Session 95 scope discussion — Strategy 1 is ~95% of
  current profit).
- A new optional `BetRecord.price_source` field at
  `models.py:212–215` (operational metadata block) so every
  bet record carries an honest record of which path produced
  its price.
- A NULL-handling confirmation for `soft_book_combined_price`
  on single-leg soft-book bets (closing W4 report §7.6).
- A naming canonicalisation across the W3/W4 boundary —
  three current representations of the streaming-blocked
  concept collapse to one canonical form Code chooses.
- A paragraph-level §13 contract clarification spelling out
  that the streaming-disconnect-blocks-writes rule applies
  to placements against the streaming cache; placements
  against fresh REST prices fetched at placement time
  preserve the rule's intent.

**This brief is not:**

- A real `BetfairAdapter` implementation (sequenced separately
  Session 97+; the Protocol extension landed here is what
  that adapter implements against).
- A change to W3 modules (`live_pricing.py`, `placement.py`,
  `_translation.py`, `_errors.py`). The change uses existing
  W3 capability, doesn't modify it.
- A schema change. `BetRecord.frozen=True` plus optional
  field with default `None` is backward-compatible at the
  model layer; no SQL migration needed (no SQL schema yet
  exists per Code preflight findings).
- A rewrite of `_path_b_result` modal recovery wiring at
  `orchestrator.py:942–946`. That wiring stays intact as
  cheap insurance for the Betfair-fully-down edge case
  (REST also unreachable). See §5.3 for the rationale.
- An expansion of contract surface beyond the §13 paragraph
  clarification. No new endpoints; no new typed shapes; no
  new versioned surface beyond what the optional clarification
  adds.

Surprises become findings, not blockers. Single bounded
Code session per skill discipline. Hard limits in §9.

---

## §2 — Why this work exists

W4 v1 shipped Session 90 with two open questions in the
report — §7.4 (streaming-disconnect interaction with retry)
and §7.6 (`soft_book_combined_price` for single-leg bets) —
both phrased as questions, not recommendations.

Session 95 walked the questions with operator review.

**§7.4** — operator chose Option C (REST fallback path) over
Option A (terminal-with-message) and Option B (last cached
snapshot). Reasoning: Strategy 1 entries are time-sensitive
near the jump; "terminal-with-message" reclassification
would lose live entries when streaming drops. Real profit
hit, not hypothetical. Option C keeps entries alive when
streaming drops; price-source flag keeps the bet record
honest about which path was used.

**§7.6** — operator chose NULL over duplicate-leg-price.
Honest semantic: there is no combined price for single-leg.
Downstream NULL-handling is trivial; semantic correctness
is permanent.

Session 95 also confirmed via parallel Code investigation
that the change is greenfield wiring of existing W3
capability (REST price-fetch already exists in
`live_pricing.py`; cache-first / REST-fallback routing is
the default for both `market_prices` and `runner_best_prices`).
No new W3 surface needed; only orchestrator-side wiring
plus the Protocol extension.

This brief commissions that wiring.

---

## §3 — Pre-reads

In order:

1. **`dr029/w4_bet_entry/_drafts/SESSION_95_drafts.md`** —
   Session 95 live triage substrate (461 lines). Holds the
   locked scope, structural shape, and operator decisions
   (Option C, NULL, Shape A, BetRecord-level placement,
   modal recovery wiring intact). **Required.**
2. **`dr029/w4_bet_entry/_drafts/SESSION_95_code_preflight.md`** —
   Claude Code's parallel pre-flight investigation (207
   lines). Anchored file paths, line numbers, current-state
   findings on REST surface, `price_source` field state,
   `streaming_blocked` classification site. **Required.**
3. **`dr029/w4_bet_entry/w4_bet_entry_report.md`** §7.4 +
   §7.6 — the open questions this brief closes. Required
   only for these two sections (lines 509–565).
4. **`dr029/2_7_api_contract_versioning/betfair_client_contract.md`**
   §13 (lines 1243–1285) and §9.1 (lines 283–381) — context
   for the §5.5 contract clarification and the `live_pricing`
   surface the new Protocol method exposes. Required for
   §5.5; reference-only otherwise.

**Reference-only — read on demand:**

- `decisions.md` DR-027 / DR-028 (cross-DB boundary discipline
  — context for why streaming-disconnect rule lives in
  `betfair_client` not in v3 modules).
- `decisions.md` DR-030 (v3 repo layout) — informs file
  locations.
- `decisions.md` DR-031 (v3 tech stack) — Pydantic v2,
  pytest discipline, ruff, import-linter contracts.
- `decisions.md` DR-032 (canonical reference layer for all
  bet records) — drives `price_source` placement at the
  operational metadata block on `BetRecord`.
- `decisions.md` DR-021 (timestamp anchoring, Adelaide local
  time) — applies to any timestamp surfaces touched.

---

## §4 — System access

- **Filesystem read-write** at the named anchors below.
  Read-only on all other paths.
- **No Betfair API calls** — all tests run against
  `MockBetfairAdapter` per the W4 precedent at
  `workflows/bet_entry/v1/tests/test_orchestrator.py`.
- **No git operations** — no `git add`, `git commit`,
  `git stash`, `git restore`, `git checkout`, `git reset`.
  Read working-tree state at session start; edit only named
  anchors; run `git diff <file>` after each edit; run
  `git status` at session close to confirm dirty file list
  unchanged from start.
- **Live `bethub-v3/`** at
  `/Users/tim/Desktop/Projects/bethub-v3/`. Tests run
  in-tree via `pytest` from project root.
- **Adelaide local timestamps per DR-021** for any
  time-of-day reference in the report.

---

## §5 — Substantive scope (six locked items)

Six coordinated changes. Sequencing in §6.

### §5.1 — `BetfairAdapter` Protocol extension

**Anchor:** `workflows/bet_entry/v1/orchestrator.py` —
`BetfairAdapter` Protocol (currently exposes
`get_market_status`, `get_account_funds`, `place_hedge_bet`,
`get_order_state`).

**Change:** add one new read-side method exposing the
existing W3 `live_pricing` REST capability. Method-name
canonicalisation lands here (per §5.6); Code chooses the
canonical name across the W3/W4 boundary.

**Suggested signature:**

```python
def fetch_fresh_runner_price(
    self,
    market_id: str,
    selection_id: str,
) -> RunnerBestPrices | None: ...
```

Returns the W3 `RunnerBestPrices` shape from `live_pricing.py`
(or `None` when the REST call itself fails — caller treats
as terminal per §5.3 fallback chain). `MockBetfairAdapter`
gains a matching `queue_fresh_runner_price(...)` test hook
following the existing W4 mock pattern.

**No edits to `live_pricing.py`** — the Protocol method's
real implementation (sequenced Session 97+) wraps the
existing function. `MockBetfairAdapter` returns whatever the
test queues.

### §5.2 — `BetRecord.price_source` field addition

**Anchor:** `workflows/bet_entry/v1/models.py` lines 212–215
(BetRecord operational metadata block, alongside `placed_at`,
`book_or_exchange`, `account_at_book_id`).

**Change:** add `BetRecord.price_source` — optional
`PriceSource` enum, default `None`, backward-compatible.

**New enum:**

```python
class PriceSource(str, Enum):
    """Brief §5.2 — bet-record-level flag identifying which
    path produced the bet's price.

    Populated at bet-record construction time. NULL for
    historic records constructed before this field existed
    (backward-compatible per Pydantic optional default).
    """

    STREAMING_CACHE = "streaming_cache"
    REST_FETCH = "rest_fetch"
    OPERATOR_TYPED = "operator_typed"  # soft-book entries
```

**BetRecord field** (insert at lines 212–215 in the
operational metadata block):

```python
price_source: PriceSource | None = None
```

**Placement is bet-record-level, not per-leg.** Operator
locked Session 96. Reasoning: W4 v1 ships single-leg only;
single-leg bets carry one source per bet; per-leg placement
is future-proofing for Strategy 3 SGM that isn't built yet.
Shifting to per-leg later is one model-shape edit when SGM
mechanics arrive (W4.1+). DR-019 (derived state on read)
discipline applies — don't model what isn't needed yet.

**Backward-compatibility:** `BetRecord.frozen=True` plus
optional field with default `None` means existing test
fixtures and direct-construction sites continue to work
unchanged. `record_builder.py` populates the field at
construction time per §5.4. No SQL schema exists yet
(`store/schema/`, `store/repositories/`, `domain/bets/`
are empty `__init__.py` placeholders per Code preflight),
so no DB-side coordination needed.

### §5.3 — Orchestrator REST-fetch branch

**Anchor:** `workflows/bet_entry/v1/orchestrator.py`
`_place_with_retry` at lines 645–685, plus
`PlacementOutcome` enum at line 147.

**Change:** when `_place_with_retry` receives a
`PlacementOutcome.outcome == "streaming_blocked"`, fetch a
fresh REST price via the new Protocol method (§5.1), place
with that price, and write the bet record with
`price_source=PriceSource.REST_FETCH`. Replaces the current
"streaming_blocked treated as retry-safe" behaviour
(orchestrator.py:677, plus the docstring at line 654).

**Fallback chain:**

1. Streaming cache fresh → place with cached price; bet
   record carries `price_source=STREAMING_CACHE`.
2. Streaming cache unavailable (`streaming_blocked`
   outcome) → call
   `adapter.fetch_fresh_runner_price(market_id, selection_id)`.
   If the REST call returns a price → place with that
   price; bet record carries `price_source=REST_FETCH`.
3. REST call returns `None` (Betfair fully unreachable —
   no streaming, no REST) → fall through to the existing
   modal recovery wiring at `_path_b_result:942–946`.
   Bet record never lands; modal surfaces "Wait and retry"
   per the existing `BETFAIR_STREAMING_DISCONNECTED`
   recovery branch.

**Modal recovery wiring stays intact.** Operator locked
Session 96. The branch at `_path_b_result:942–946`
special-cases `BETFAIR_STREAMING_DISCONNECTED` for recovery
messaging; with REST-fallback succeeding most of the time,
this branch is now rarely-reached. It remains as cheap
insurance for the Betfair-fully-down edge case where REST
also fails. Operationally, if Betfair is fully down the
operator has a bigger problem than recovery messaging
anyway; pruning saves nothing and removes a fallback.
Code names the branch with a one-line comment in the
report explaining why it's retained as a rare-path
fallback.

**Backoff schedule discipline:** the existing
`DEFAULT_BACKOFF_SCHEDULE_MS = (50, 200, 500)` retry
schedule applies to the REST-fetch attempt the same way it
applies to placement attempts — REST-fetch failure is
retried per the same schedule before falling through to
modal recovery. (Streaming-blocked is no longer retried at
the placement layer because step 2 is now the response, not
"retry placement against stale cache.")

**`customer_order_ref` round-trip discipline holds.** Per
contract §11.1 and existing W4 behaviour (Session 95 W4
report §9.2(b)), the same `customer_order_ref` is reused
across all placement attempts within a cycle, including
the REST-fetch branch. Betfair's idempotency key recognises
duplicate-submit attempts as the same intended placement.

### §5.4 — `record_builder.py` NULL handling for single-leg

**Anchor:** `workflows/bet_entry/v1/record_builder.py` —
NULL-handling site for `soft_book_combined_price`. Code's
preflight investigation flagged the model field is already
`float | None` at `models.py:210`; no model shape change
needed. Logic change is in the builder only.

**Change:** when building a single-leg soft-book bet
record, set `soft_book_combined_price = None`. When
building a multi-leg SGM record (W4.1+ territory; raises
today per `BetRecordBuilderError` strategy_tag check),
preserve existing logic — `soft_book_combined_price`
populated from operator input.

**Discriminator:** the `legs` tuple length on the
`SoftBookRecordInputs` shape. Length 1 → single-leg → NULL.
Length > 1 → multi-leg → operator-supplied combined price.

This closes W4 report §7.6's question. Honest semantic per
Session 95 operator decision: there is no combined price
for single-leg; NULL is the correct value.

### §5.5 — §13 contract clarification paragraph

**Anchor:** `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
§13 (lines 1243–1285).

**Change:** add one paragraph clarifying the rule's scope
post-REST-fetch fallback. Existing §13.1 names the trigger
(non-`SUBSCRIBED` state); §13.2 names block behaviour; §13.3
names why the rule lives in `betfair_client`; §13.4 names
what's not blocked (cancellation, replacement, reads).
Post-clarification, the rule's intent (don't place into
stale prices) is preserved both by the existing block and
by the new REST-fetch path.

**Suggested paragraph (insert as §13.5 or as a closing
paragraph in §13.3 — Code's choice):**

> The streaming-disconnect-blocks-writes rule applies to
> placements against the streaming cache. v3 callers are
> permitted to fetch a fresh REST price at placement time
> via the live-pricing read surface (§9.1) and place
> against that price even when the streaming connection is
> non-`SUBSCRIBED`, because the rule's intent — preventing
> placement into stale prices — is preserved by the fresh
> REST fetch. The `betfair_client` block at the placement
> surface (§11.1) operates on streaming state alone;
> v3-side logic that explicitly fetches fresh REST prices
> is not the failure mode the rule prevents. The bet record
> at v3 carries `price_source=REST_FETCH` for transparency
> per the bet-record schema (W4 §5.2).

**Version-bump bookkeeping.** This is a paragraph-level
clarification, not a behaviour change at the contract
surface — `betfair_client` itself is unchanged. Per §14.4
backward-compatible-additions discipline, this lands as
v1.3 with a §6 history-row entry:

```
| 2026-05-07 | Session 96 W4 follow-up Code | **v1.3
backward-compatible clarification.** §13 paragraph added
clarifying that the streaming-disconnect-blocks-writes rule
applies to streaming-cache placements; placements against
fresh REST prices fetched at placement time are permitted
because they preserve the rule's intent. No surface
changes; no signature changes; v3 callers using the
existing surfaces are unaffected. Closes W4 follow-up
brief §5.5. |
```

Status header at top of contract file updates from
`**Status:** v1.1` to `**Status:** v1.3` with the v1.2 +
v1.3 amendment notes appended.

### §5.6 — Naming canonicalisation across W3/W4 boundary

**Three current surface representations of the
streaming-blocked concept** (per Code preflight §4):

- W3 reason — `betfair_streaming_disconnected` (lowercase
  enum value in `BetfairReadUnavailableReason` at
  `clients/betfair_client/v1/_envelopes.py` or equivalent).
- W4 outcome — `"streaming_blocked"` (literal string in
  `PlacementOutcome.outcome` at `orchestrator.py:147`).
- Modal recovery key — `BETFAIR_STREAMING_DISCONNECTED`
  (uppercase string at `orchestrator.py:942–946`).

**Change:** Code chooses the canonical form and aligns the
W4-side surfaces. W3 reason stays as-is (it's the contract
surface; v1.0 locked).

Code's call. Two reasonable options:

- **Align on W3** — W4 `PlacementOutcome.outcome` becomes
  `"betfair_streaming_disconnected"`; modal recovery key
  matches case (lowercase). Pro: matches contract surface.
  Con: longer string; renames a literal in
  `_place_with_retry`.
- **Align on W4** — W3 reason stays unchanged (locked
  contract); W4 outcome and modal recovery key become
  `"streaming_blocked"` (lowercase, consistent). Pro:
  short, operationally readable. Con: doesn't match the
  W3 contract reason name.

Code picks per code-shape coherence; brief surfaces the
choice in the report's §6 deviations / decisions section.
Tests adjust accordingly.

---

## §6 — Sequencing within session

Build order, dependency-driven:

1. **§5.1 — `BetfairAdapter` Protocol extension first.**
   The new method's signature and `RunnerBestPrices` import
   land first; everything downstream depends on it.
   `MockBetfairAdapter` test hook lands in the same edit.
2. **§5.2 — `PriceSource` enum + `BetRecord.price_source`
   field.** Pure model addition; no behaviour wiring yet.
   Existing tests still pass (optional default `None`).
3. **§5.3 — Orchestrator REST-fetch branch.** The biggest
   change in the brief; depends on §5.1 (Protocol method
   exists) and §5.2 (field exists to populate). New
   `_place_with_retry` branch logic; modal recovery wiring
   at `:942–946` stays untouched.
4. **§5.4 — `record_builder.py` NULL handling.** Pure
   logic change; depends on §5.2 (model field exists with
   `None` default). Tests confirm NULL for single-leg
   (existing builder tests + one new case).
5. **§5.6 — Naming canonicalisation.** Mechanical search-
   and-replace across W4-side files (orchestrator.py +
   tests + any other site); Code picks form per §5.6.
   Lands after §5.3 so the wiring change settles first
   and only one rename pass is needed.
6. **§5.5 — Contract paragraph clarification.** Last,
   independent of code changes. Standalone artefact edit
   on the contract file. Status header + §6 history row +
   the §13 paragraph itself. Run after all code is green.

§5.4 (NULL handling) and §5.5 (contract clarification) are
both small enough that order between them doesn't matter
operationally — Code picks the order that fits the session
flow best.

---

## §7 — Test scope

**Expected pytest delta:** +8 to +12 new tests; baseline
232 → 240–244 expected. Zero regression on the existing
232.

**Test categories:**

- **Orchestrator tests** at
  `workflows/bet_entry/v1/tests/test_orchestrator.py`.
  Replace the existing test_orchestrator.py case for
  `streaming_blocked → retry-safe-collapse` with the new
  REST-fetch-branch behaviour. Add cases:
  - `test_streaming_blocked_rest_fetch_succeeds` —
    streaming-blocked outcome, REST fetch returns price,
    placement lands, bet record has
    `price_source=REST_FETCH`.
  - `test_streaming_blocked_rest_fetch_fails_modal_recovery` —
    streaming-blocked outcome, REST fetch returns None,
    falls through to modal recovery wiring (existing
    behaviour).
  - `test_happy_path_carries_streaming_cache_source` —
    cache-fresh placement, bet record has
    `price_source=STREAMING_CACHE`.
- **Record-builder tests** at
  `workflows/bet_entry/v1/tests/test_record_builder.py`.
  Add cases:
  - `test_single_leg_soft_book_combined_price_is_null` —
    single-leg soft-book input; record has
    `soft_book_combined_price=None`.
  - `test_single_leg_hedge_record_carries_price_source` —
    hedge record built with `price_source` parameter;
    field round-trips correctly.
  - `test_single_leg_soft_book_record_carries_operator_typed_source` —
    soft-book record built with
    `price_source=OPERATOR_TYPED`; field round-trips.
- **Protocol contract tests** at
  `workflows/bet_entry/v1/tests/test_orchestrator.py` (or
  a sibling file Code chooses):
  - `test_betfair_adapter_protocol_has_fetch_fresh_runner_price` —
    Protocol method exists with the expected signature;
    `MockBetfairAdapter` implements it.
- **Naming-canonicalisation regression check** — existing
  tests that reference the old names (e.g.
  `outcome="streaming_blocked"` literals in test fixtures)
  rename per §5.6 outcome. No new tests; the renamed
  fixtures still pass.

**Test count target:** 8 new tests minimum, 12 maximum.
If Code's implementation surfaces additional cases worth
covering (e.g. REST-fetch returning malformed prices), add
them and flag in the report's §3 — Tests Built section.

---

## §8 — Empirical verification

**Pre-change baseline (capture at session start):**

```
$ cd /Users/tim/Desktop/Projects/bethub-v3
$ python -m pytest --co -q 2>&1 | tail -5
$ python -m pytest 2>&1 | tail -10
```

Confirm: 232 tests collected, 232 passing, 0 failures, 0
xfails, 0 skips. If the baseline differs from 232, **stop
and surface as finding** — the brief's expected delta
arithmetic depends on this baseline.

**Post-change verification (capture at session close):**

```
$ python -m pytest 2>&1 | tail -10
$ python -m ruff check . 2>&1 | tail -5
$ python -m lint_imports 2>&1 | tail -10
```

Confirm:

- pytest passes 240–244 tests (zero regression on baseline
  232 + 8–12 new). If outside this range, surface as
  finding.
- ruff clean across project.
- All 5 import-linter contracts kept (per W4 v1 baseline).

**Manual spot-check** — open `models.py` and confirm
`BetRecord.price_source` lands in the operational metadata
block at the expected line range (it'll shift down by a
few lines after the field insert, but should sit
adjacent to `placed_at` / `book_or_exchange` /
`account_at_book_id`, not in some unrelated block).

---

## §9 — Hard limits

Non-negotiable list of what's NOT in scope.

- **No edits to W3 modules.** `live_pricing.py`,
  `placement.py`, `_translation.py`, `_errors.py`,
  `_envelopes.py`, `_auth.py`, `consumer.py` — read-only.
  The change uses existing W3 capability through the
  Protocol; doesn't modify W3 itself.
- **No SQL schema changes.** No migrations, no Alembic,
  no DDL. The model-layer field addition is
  backward-compatible per Pydantic optional default; SQL
  schema doesn't exist yet (empty placeholders per Code
  preflight).
- **No new contract surfaces.** No new endpoints, no new
  typed shapes beyond `PriceSource` enum, no new
  versioned surface. The §5.5 paragraph clarification is
  contract-text-only — no code surface change at the
  contract level.
- **No real `BetfairAdapter` implementation.** The Protocol
  extension lands here; the real adapter that wraps
  `clients.betfair_client.v1.live_pricing` is sequenced
  Session 97+. Tests run against `MockBetfairAdapter`
  throughout.
- **No edits to `_path_b_result` modal recovery wiring**
  beyond the one-line comment naming why it's retained.
  The branch stays intact; Session 96 operator call
  locked.
- **No scope expansion to other W4 report items.** §7.1
  (path-(a) routing), §7.2 (provisional_pending +30s),
  §7.3 (real adapter location), §7.5 (`customer_strategy_ref`
  vs `strategy_tag`) — all out of this brief's scope. They
  route through separate triage or separate briefs as the
  arc progresses.
- **No git operations.** Per §4.
- **No Betfair API calls.** Per §4. All tests against
  `MockBetfairAdapter`.
- **No operator escalation mid-session.** Code runs end-
  to-end; surfaces findings in the report; doesn't ping
  operator-Claude mid-flight asking for direction. If the
  brief has a gap, name it as a finding in §6 deviations
  or §7 open questions of the report.
- **No DB-side coordination.** No writes to any DB; no
  reads either. The change is model-layer only on the
  v3 side; the contract-layer §13 paragraph is text-only.
- **Single bounded Code session.** If the work doesn't fit
  in one bounded session, that's a finding — don't
  continue past budget. Partial-but-coherent beats
  complete-but-lost-coherence.

---

## §10 — Output spec

**Single output file:**
`dr029/w4_bet_entry/w4_followup_report.md`.

**Length target:** 300–450 lines. The W4 brief's report
ran 837 lines for a much larger build; this brief's report
should sit closer to the v1.2 contract addition report
(~440 lines) given comparable scope.

**Section structure (anchored on the universal report
shape):**

1. Header / summary of what shipped.
2. Modules edited (per file, with line range and change
   summary).
3. Tests built (table per file with case count and
   highlights).
4. Test results (pytest, ruff, import-linter output).
5. Linting + import-linter results (already covered in
   §4 above; expand if any contract drift).
6. Deviations from brief (Code's call when ambiguity
   surfaced — §5.6 canonical form choice, modal recovery
   comment wording, etc.).
7. Open questions (residual ambiguity for operator-Claude
   triage; one per question, scoped tightly).
8. Findings (operational observations and contract-shape
   items that aren't deviations or open questions but
   matter for next-stage work — typically empty for a
   surgical mini-build like this).
9. Self-assessment (session-budget fit, confidence
   regions, length-range overrun if any, what the
   operator should look at first).

**What the report does not contain:**

- No proposed remediations or follow-up briefs. Code
  reports findings and questions; operator-Claude triages.
- No scope creep into adjacent W4 report items (§7.1,
  §7.2, §7.3, §7.5).
- No conclusions or overall verdict beyond the
  self-assessment's "did the build fit" framing.
- No real-API integration claims. All tests run against
  mocks; real-API behaviour is operator-side acceptance
  work post-merge.

---

## §11 — What happens after Code's session

**Session 97 (operator-Claude triage):**

1. Read the report end-to-end.
2. Walk deviations (§6) — confirm Code's calls.
3. Walk open questions (§7) one per round, plain-operator-
   language framing per Cat 1.
4. Walk findings (§8) — route each (no action / fold into
   existing carry / new brief / contract-housekeeping
   sweep).
5. Lock close-out: brief closed; W4 follow-up arc
   complete; carry-forward items into `current_state.md`.

**Sequence after Session 97:**

- Real `BetfairAdapter` implementation brief drafting now
  fully unblocked. The Protocol extension and `price_source`
  field both ship in this brief; the real adapter brief
  inherits both shapes and wires `live_pricing` through to
  the new method.
- v3 composition-root structural decision drafting
  remains sequenced for whenever it next slots in
  (Session 97+ depending on real adapter brief sequencing).

**Code does not produce the next brief.** That's
operator-Claude's work in Session 97 onward.

---

## §12 — Cross-references

- **W4 report §7.4** at
  `dr029/w4_bet_entry/w4_bet_entry_report.md` lines 509–528
  (streaming-disconnect retry interaction question — closed
  by §5.3).
- **W4 report §7.6** at
  `dr029/w4_bet_entry/w4_bet_entry_report.md` lines 552–565
  (soft-book combined price single-leg question — closed
  by §5.4).
- **`betfair_client_contract.md` §13** at
  `dr029/2_7_api_contract_versioning/betfair_client_contract.md`
  lines 1243–1285 (streaming-disconnect-blocks-writes —
  clarified by §5.5).
- **`betfair_client_contract.md` §9.1** at same file lines
  283–381 (operational live-pricing reads — the surface the
  new Protocol method exposes).
- **`betfair_client_contract.md` §6** at same file lines
  156–172 (version history table — gets a v1.3 row per
  §5.5).
- **DR-027** (the two-database architecture decision: BetHub
  owns operational state, capture.db owns analytical/source
  data) — context for why streaming-disconnect rule lives
  in `betfair_client` not in v3 modules.
- **DR-028** (the cross-database integration boundary
  discipline decision: no caching, no denormalisation, no
  second integration point, four lean structural protections)
  — same.
- **DR-030** (v3 repo layout and module-boundary discipline)
  — informs file locations.
- **DR-031** (v3 tech stack: Python 3.12+, Pydantic v2,
  pytest, ruff, import-linter) — Pydantic v2 discipline for
  the new field; pytest for tests.
- **DR-032** (canonical reference layer for all bet records)
  — drives `price_source` placement at the operational
  metadata block on `BetRecord` per §5.2.
- **DR-021** (timestamp anchoring, Adelaide local time) —
  applies to the report's timestamps.
- **Session 95** at `sessions/SESSION_95.md` — v1.2 triage
  closed; W4 follow-up brief scope (Shape A) and 12-section
  structural shape locked; brief drafting deferred to
  Session 96.
- **Session 95 drafts** at
  `dr029/w4_bet_entry/_drafts/SESSION_95_drafts.md` (461
  lines) — locked scope, structural shape, operator
  decisions.
- **Session 95 Code preflight** at
  `dr029/w4_bet_entry/_drafts/SESSION_95_code_preflight.md`
  (207 lines) — anchored file paths, line numbers,
  current-state findings.
- **W4 brief precedent** at
  `dr029/w4_bet_entry/w4_bet_entry_brief.md` (2121 lines) —
  the original W4 build commission whose §7 open questions
  this brief closes.
- **v1.2 contract addition brief** at
  `dr029/w4_bet_entry/v1_2_contract_addition_brief.md` —
  the closest brief precedent (mini-build with paired
  contract amendment shape).

**Parking-lot items excluded from this brief:**

- W4 report §7.1 (path-(a) routing across modal/orchestrator
  boundary).
- W4 report §7.2 (provisional_pending +30s follow-up).
- W4 report §7.3 (real `BetfairAdapter` implementation
  location).
- W4 report §7.5 (`customer_strategy_ref` vs `strategy_tag`).
- W4 report §8.x findings except §8.1 and §8.2 (already
  closed by v1.2 contract addition).
- v3 composition-root structural decision drafting.
- Standing-instructions sweep.

---

**End of brief.**
