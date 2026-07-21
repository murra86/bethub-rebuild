# Session 95 — live triage substrate

**Started:** 2026-05-07 08:49 ACST (Session 95 open)
**Purpose:** live capture of triage decisions for Code's
v1.2 contract addition report at
`dr029/w4_bet_entry/v1_2_contract_addition_report.md`.
Written and updated mid-session per `standing_instructions.md`
Cat 2 (persist drafted content to scratch) so calls don't
live in chat history alone. Contents move to canonical
`sessions/SESSION_95.md` at close.

---

## Triage decisions locked

### §7.1 deviation — W3 path-style vs library-call internals

**Tension.** Brief §6.1/§6.2/§7 prescribed library-call
internals (call `betfairlightweight` library methods
directly, mock those calls in tests). Brief §1/§3 named
the W3 v1.0 surface pattern as the reference implementation
— and W3 doesn't use library calls; it uses path-style
endpoints via `BetfairRestClient` with translation at
`_translation.py`. Brief §11 forbade editing
`_translation.py`. Brief was internally inconsistent.

**Code's choice.** Mirrored W3 path-style faithfully —
both new functions take `BetfairRestClient`; endpoints are
path-style (`/v1/account/funds`,
`/v1/market/{id}/catalogue`); tests use `MockTransport`
per `test_live_pricing.py` precedent.

**Operator decision (this session).** Confirmed Code's
W3-pattern choice. Locks in. Reasoning: pattern coherence
across all v1 read surfaces; avoids two patterns sitting
side-by-side in `clients/betfair_client/v1/`; brief's
§11 fence on private modules made library-call internals
non-viable in any case.

**Consequence carried.** Translation-layer wiring missing
for the two new path-style endpoints — see Finding 3 below.

---

### Finding 1 — brief-text mismatch at §3 cross-reference site

**What.** Brief §5.5 quoted §3 as having a paragraph
starting "No account-management surfaces."; actual §3 is
bullet-structured. Code preserved intent (acknowledge
§9.6 carve-out within §3) by editing the bullet's heading
and trailing sentence.

**Operator decision (this session).** No call required.
Cosmetic brief-drafting note: when I quote source text in
a brief, read the actual file rather than going from
memory. Carries to brief-drafting practice — not a
governance artefact change.

---

### Finding 2 — stale §2 + §14.2 surface count

**What.** Contract still says "nine surfaces — five read,
one streaming, three write" at §2 and §14.2. After v1.2
the count is eleven / seven / one / three. Brief drew a
tight cross-reference housekeeping box; Code respected it.

**Operator decision (this session).** Defer to next
contract-housekeeping sweep. Reasoning: cosmetic; readers
working day-to-day are reading §9 surface specs, not §2 or
§14.2 summary lines; queue of similar housekeeping items
already accumulated (W4 brief amendment sweep, legacy §D12
reference cleanup, jump-anchor design reframe). One sweep
cheaper than touching the contract repeatedly.

---

### Finding 3 — translation-layer entries pending

**What.** Two new path-style endpoints
(`/v1/account/funds`, `/v1/market/{id}/catalogue`) have
no translation entries in `_translation.py`. Tests pass
against `MockTransport`; against real httpx-backed
transport, calls would fail at "unknown path" today.

**Operator decision (this session).** Fold into Session
96+ real `BetfairAdapter` implementation brief — that
brief touches `_translation.py` anyway. Live-API
validation (Code's §10 acceptance optional item) is
nice-to-have, not load-bearing; mocked-transport tests
already confirm the shape.

---

### Finding 4 — brief baseline test count off by 75

**What.** Brief §7 stated existing test count was 287;
actual baseline at session start was 212. Brief's 287
either over-counted or counted from a different point in
time. "Zero regression" target satisfied against actual
baseline (212 → 232 with +20 new tests).

**Operator decision (this session).** No call required.
Informational; no governance artefact change. Folds into
the same brief-drafting lesson already captured below
(brief-drafting accuracy — verify counts empirically at
brief-drafting time rather than going from memory).

---

## Carry-forward items surfaced this session

### Brief-drafting lesson (Session 95)

**Substrate.** Session 94 brief contradicted itself —
§1/§3 named W3 v1.0 as the reference implementation
pattern; §6.1/§6.2 specified library-call internals which
W3 does not use. Code resolved the tension by mirroring
W3 (faithful to the named reference), but the brief
itself shouldn't have contained the contradiction.

**Lesson.** When a brief names a "reference implementation
pattern" in its framing sections, the internals spec
(§6 implementation scope, §7 test scope) must match that
pattern. Reference-pattern fidelity is load-bearing — it
governs what Code actually builds — and a contradiction
between framing and internals leaves Code to pick, which
is exactly the kind of decision that should be the
operator's at brief-drafting time.

**Routing.** Carries to next `standing_instructions.md`
sweep — candidate for Cat 5 (operator-Claude division of
labour) or Cat 1 (call-driven surfacing during brief
drafting). Specifically: pre-flight grounding step in
`bethub-brief-drafting` skill should explicitly check
"does the implementation spec match the named reference
pattern" as a discrete verification.

---

## Forward routing (locked this session)

**Triage close.** v1.2 contract addition Code report
triaged end-to-end. §7.1 deviation confirmed (W3-pattern
choice locks in). Findings 1, 2, 4 — no operator action
required. Finding 3 — folded into Session 96+ real
`BetfairAdapter` brief.

**This session continues into brief-drafting** — small
W4 follow-up brief covering W4 report §7.4 (streaming
error reclassification + new `ErrorContext.error_kind`
value) and §7.6 (`soft_book_combined_price` NULL for
single-leg). Operator confirmed continuation; session is
fresh, mode-switch from triage to brief-drafting accepted.
Split-trigger watched per Session 11 lesson — surface
split candidate if pre-flight grounding or drafting goes
denser than expected.

**Sequence after Session 95:**

- Session 96 — real `BetfairAdapter` implementation brief
  drafting. Now folds Finding 3 (translation-layer entries
  for v1.2's two new path-style endpoints —
  `/v1/account/funds`, `/v1/market/{id}/catalogue`) into
  scope.
- Session 96 alt — v3 composition-root structural decision
  drafted standalone before adapter brief, depending on
  what adapter-brief drafting surfaces as load-bearing
  prerequisite.
- W5 brief drafting — can open whenever, parallelisable
  with adapter / composition-root work.

**Out of scope for Session 95:**

- v3 composition-root structural decision drafting —
  sequenced Session 96.
- Real `BetfairAdapter` implementation brief drafting —
  sequenced Session 96+.
- Standing-instructions sweep — deferred to fresh-mind
  session. Sweep candidates accumulating: `bash_tool`
  softening; `str_replace` namespace gotcha as Cat 3
  absorption; end-to-end-drafting-cadence-after-§1 as
  Cat 1 candidate; brief-drafting-pattern-fidelity check
  in `bethub-brief-drafting` skill (this session's
  carry-forward).

---

## Brief-drafting — small W4 follow-up brief

### Scope at session start

Originally framed as two narrow items from W4 report:

- §7.4 — streaming-blocked error reclassification.
- §7.6 — `soft_book_combined_price` NULL for single-leg.

Expected size: under 300 lines.

### Operator-driven scope expansion (Session 95)

§7.4 framing changed materially during operator review.
Initial pitch was "terminal-with-message" reclassification.
Operator surfaced the operational risk: Strategy 1 cycles
run close to the jump, Strategy 1 is 95% of current profit;
"terminal-with-message" means losing time-sensitive bets
when streaming drops. Real profit hit, not hypothetical.

Three options laid out:

- A — terminal-with-message (cleanest semantic, worst
  operationally for time-sensitive entries).
- B — fall back to last cached snapshot price, log with
  flag (cheap to build, price possibly stale).
- C — pull fresh price via REST, log with flag (most
  operationally robust, more code).

**Operator decision (Session 95).** Option C — REST
fallback path. Keeps Strategy 1 entries alive when
streaming drops; price-source flag keeps the bet record
honest about which path was used.

**Re-read of W4 report §7.4.** The report was actually
asking a question, not recommending terminal-with-message.
The question was retry-vs-wait-for-reconnect. Option C
is a stronger answer than either alternative the report
reached toward — keeps operability and keeps data
honest.

**Brief size impact.** Bumps from sub-300 lines to
~400-500 lines. Still single-bounded-Code-session
territory. §7.4 is now "add REST fallback path,
classify streaming-blocked as triggering the fallback
rather than terminating, add price-source flag to bet
record" — a slightly bigger surface than original
framing.

### §7.6 — NULL vs duplicate-leg-price call

W4 report §7.6 was also a question, not a
recommendation. Two options: NULL (clean semantic,
downstream NULL-handling needed) or duplicate the
leg price (no NULL handling, semantically misleading
for single-leg).

**Operator decision (Session 95).** NULL. Honest
semantic — there is no combined price for single-leg.
Downstream NULL-handling is trivial; semantic
correctness is permanent.

### Pre-flight grounding — consolidated findings

**Document-side findings (operator-Claude).**

- W4 report §7.4 was a question (retry vs wait-for-reconnect),
  not a terminal-with-message recommendation.
- W4 report §7.6 was a question (NULL vs duplicate-leg-price),
  not a recommendation.
- Contract §13 (streaming-disconnect-blocks-writes) rule:
  "betfair_client blocks bet placement during streaming gap
  because v3 doesn't have current price visibility, and
  placing into stale prices is a money-risk failure mode."
  Option C preserves the rule's intent — fresh REST price is
  not stale.

**Code-side findings (`SESSION_95_code_preflight.md`).**

- **Q1 REST price-fetch.** Already exists in `live_pricing.py`.
  Cache-first / REST-fallback routing is the default; both
  `market_prices` and `runner_best_prices` work this way today.
  **No new contract surface needed. No new client module
  needed.** Only `BetfairAdapter` Protocol extension —
  one new "fetch fresh price" read-side method exposing the
  existing capability.

- **Q2 `price_source` field.** Doesn't exist anywhere. Slots
  into `BetRecord` operational metadata block at
  `models.py:212-215` alongside `placed_at` /
  `book_or_exchange` / `account_at_book_id`. Backward-compatible
  if optional with default `None`. No SQL schema exists yet
  (placeholders empty) — no DB-side coordination needed.

- **Q3 streaming-blocked classification.** Centralised at one
  production site (`placement.py:155-186` — W3 contract §13
  pre-check). W4 Protocol slot exists but is **currently
  unreachable** — no production code path produces it because
  no real `BetfairAdapter` exists yet. **The change is greenfield
  wiring, not a refactor.**

- Code §4 adjacent observations:
  - `PlacementOutcome.raw` slot or new `rest_fetch_price` field —
    brief names which.
  - Modal recovery wiring (`_path_b_result:942`) may go
    unreachable post-change — brief names whether to prune.
  - Naming inconsistency (`betfair_streaming_disconnected` vs
    `streaming_blocked` vs `BETFAIR_STREAMING_DISCONNECTED`) —
    three surface representations of one concept; brief names
    canonicalisation.
  - `price_source` per-record vs per-leg — operator-Claude call.
    Code's flag: W4 v1 ships single-leg, brief framing says
    "flag the record" → BetRecord placement matches.
  - §7.6 not investigated by Code per operator scope; flag only:
    `BetRecord.soft_book_combined_price` is already
    `float | None` (`models.py:210`) — no shape change needed
    for NULL-for-single-leg.

### Shape A vs Shape B call

Originally framed as two-brief vs single-brief decision —
contract amendment was the load-bearing reason to split.

**Code's investigation evaporated the split rationale.**
No contract amendment is needed (or only a paragraph-level
§13 clarification to spell out "rule applies to streaming-
cache prices; fresh REST prices at placement time preserve
the rule's intent"). All other work is workflow-layer.

**Operator decision (Session 95).** Shape A — single combined
brief. Mode-coherent (workflow-layer changes); single Code
session; ~400-500 lines.

### Brief scope locked

Three coordinated workflow-layer changes plus §7.6 NULL
plus optional contract clarification:

1. `BetfairAdapter` Protocol — new "fetch fresh price"
   read-side method exposing existing `live_pricing` REST
   capability.
2. Orchestrator `_place_with_retry` — adds REST-fetch branch
   when `streaming_blocked` outcome arrives, replacing the
   current retry-safe-collapse behaviour. Flagging
   path-b modal recovery wiring (`_path_b_result:942`) for
   pruning if it goes unreachable.
3. `BetRecord` — adds optional `price_source` field at
   `models.py:212-215` (BetRecord-level, not per-leg).
   Default `None`; backward-compatible.
4. `BetRecord.soft_book_combined_price` — confirm NULL for
   single-leg in `record_builder.py` (no shape change; logic
   change only).
5. Optional: §13 contract clarification paragraph naming
   the REST-fallback exception.
6. Naming canonicalisation across W3/W4 boundary —
   `streaming_blocked` vs `BETFAIR_STREAMING_DISCONNECTED`
   vs lowercase variants. Brief names canonical form.

[Brief drafting commences next round — structural shape
lock per skill Step 3.]

---

## Brief structural shape — locked Session 95

**Skill Step 3 — operator confirmed dev-lead call.** Closest
precedent is the v1.2 brief itself (mini-build with paired
contract amendment); this brief is the same hybrid shape,
thinner on the contract side, heavier on workflow.

**Section spine (12 sections):**

1. What this brief is and is not — workflow-layer mini-build
   with optional paragraph-level §13 contract clarification.
   Single bounded Code session. Surprises become findings.
2. Why this work exists — closes W4 report §7.4 (operator-
   Claude chose Option C in Session 95: REST fallback when
   streaming blocked) + §7.6 (NULL for single-leg).
3. Pre-reads — W4 report §7.4 + §7.6 (`w4_bet_entry_report.md`);
   `betfair_client_contract.md` §13 + §9.1 (live-pricing
   surface); `SESSION_95_code_preflight.md` (the parallel Code
   investigation); `SESSION_95_drafts.md` (this scratch, for
   the locked decisions).
4. System access — bethub-v3 filesystem read-write at named
   anchors; no Betfair API calls; no git operations; no real
   live-pricing fetches (mocked transport throughout).
5. Substantive scope (six locked items):
   - §5.1 — `BetfairAdapter` Protocol extension. New read-side
     method exposing existing `live_pricing` REST capability.
     Method-name canonicalisation lands here (per §5.6).
   - §5.2 — `BetRecord.price_source` field addition at
     `models.py:212-215` block. `Optional[PriceSource]` enum
     with values `STREAMING_CACHE` / `REST_FETCH` /
     `OPERATOR_TYPED`. Default `None`; backward-compatible.
     BetRecord-level (not per-leg) per Session 95 call.
   - §5.3 — Orchestrator `_place_with_retry` REST-fetch branch.
     When `streaming_blocked` outcome arrives, fetch fresh
     REST price, place with that price, log with
     `price_source=REST_FETCH`. Replaces current
     retry-safe-collapse behaviour. Modal recovery wiring
     (`_path_b_result:942`) pruned if unreachable post-change.
   - §5.4 — `record_builder.py` NULL handling. Single-leg soft-
     book bets get `soft_book_combined_price=None`. No model
     shape change (already `float | None`); logic change in
     builder only.
   - §5.5 — Optional contract §13 paragraph clarification.
     Spells out: "the rule applies to placements against the
     streaming cache; placements against fresh REST prices
     fetched at placement time are allowed because they
     preserve the rule's intent." Paired backward-compatible
     amendment per §14.4 if landing; v1.3 history row.
   - §5.6 — Naming canonicalisation across W3/W4 boundary.
     Three current representations
     (`betfair_streaming_disconnected` lowercase reason;
     `streaming_blocked` PlacementOutcome; `BETFAIR_STREAMING_
     DISCONNECTED` uppercase recovery key) collapse to
     canonical form Code chooses. Brief names the choice.
6. Sequencing within session — Protocol extension first
   (everything depends on it); field addition; orchestrator
   wiring; NULL handling; naming sweep; optional contract
   clarification last (Phase-1 lock if landing).
7. Test scope — orchestrator tests for REST-fetch branch
   (replace existing retry-safe-collapse test); record-builder
   test for NULL single-leg; Protocol contract tests; naming-
   canonicalisation regression check. Expected delta:
   approximately +8 to +12 tests.
8. Empirical verification — pytest baseline 232 (post-v1.2);
   expected total 240-244 after this brief. Zero regression
   on the existing 232.
9. Hard limits — no edits to `live_pricing.py`,
   `placement.py`, `_translation.py`, `_errors.py`, or other
   W3 modules (change uses existing W3 capability, doesn't
   modify it). No schema changes. No new contract surfaces
   (only optional §13 clarification paragraph). Single bounded
   Code session.
10. Output spec — single report at
    `dr029/w4_bet_entry/w4_followup_report.md`. 300-450 line
    target.
11. What happens after — Session 97 operator-Claude triage
    of report; Session 96+ real `BetfairAdapter` brief
    drafting now unblocked (the Protocol extension lands
    here, so the real adapter brief inherits the locked
    Protocol shape).
12. Cross-references — W4 report §7.4 / §7.6; Code preflight
    report; contract §13 + §9.1; DR-032 (canonical-reference-
    layer — `price_source` lives alongside DR-032's per-leg
    snapshots in the operational metadata block); DR-021
    (timestamp anchoring per envelope `as_of` and
    `cache_as_of`).

**Anchored counts.** Six scope sections; ~400-500 line brief
target; 8-12 test additions; 232 → 240-244 pytest expected.

**Anchored paths.** Edit anchors in
`bethub-v3/workflows/bet_entry/v1/`: `models.py:212-215`
(price_source field); `models.py:177-222` (BetRecord
container); `orchestrator.py:147` (PlacementOutcome enum);
`orchestrator.py:645-685` (_place_with_retry); `orchestrator.py:942-946`
(_path_b_result modal recovery); `record_builder.py` (NULL
handling site TBD by Code at drafting). Read-only anchors:
`clients/betfair_client/v1/live_pricing.py:112-207` (REST
path source); `clients/betfair_client/v1/placement.py:155-186`
(W3 §13 implementation site).

**Open question for Session 96 drafting:** does the §5.5
contract clarification land in this brief, or is it deferred?
Argument for landing: it's one paragraph, the brief touches
the contract anyway via cross-reference, paired with the
behaviour change keeps governance clean. Argument for
deferring: keeps the brief workflow-only mode-coherent;
contract amendment carries v1.3 history row separately.
Operator-Claude call at Session 96 open.
