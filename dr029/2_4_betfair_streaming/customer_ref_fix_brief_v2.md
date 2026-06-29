# Brief — Betfair customer-reference fix (Option B: decouple, schema-less)

**Drafted:** 2026-06-18 19:04 ACST (continuation chat, Claude
Chat, acting dev-lead)
**Supersedes:** `customer_ref_fix_brief.md` (S163 surgical draft —
under-scoped; do not execute it). This v2 is grounded in
`customer_ref_impact_review_report.md`.
**Executes against:** `bethub-v3` repo at
`/Users/tim/Desktop/Projects/bethub-v3` — **READ-WRITE**, named
anchors only, **dirty/in-flight tree** (Session 35/36 discipline).
**Brief type:** surgical fix to a known issue (Sessions 35/36
precedent).
**Output report:**
`dr029/2_4_betfair_streaming/customer_ref_fix_report.md`

---

## §1 — What this brief is and is not

A single bounded Code session that fixes the live-lay 503 by
**decoupling** the internal `bet_id` from the Betfair-bound
customer reference, capping every Betfair-bound reference within
its limit, and installing a length guard so the class of bug can
never silently recur.

**Is:**
- A surgical, anchored fix at the two placement sites + the
  translation funnel + tests.
- The **schema-less** form of Option B: `bet_id` keeps its
  natural form; a dedicated ≤32 reference is minted for Betfair;
  **no new column, no migration** (reconciliation already
  round-trips via `bets.betfair_bet_id` — report §5.3).

**Is NOT:**
- **No schema change.** Not one column. Reconciliation and
  settlement are untouched.
- **No refactor** of the `_coerce_uuid` / `_safe_uuid` parsers —
  they start working again once `bet_id` is clean; leave them be.
- **No change to the soft-book `log_bet` path** (record-only,
  never placed — report §5.1).
- **No touch to the bet-safety gate.** Stake, price, liability,
  and the gate that has refused every lay across 5 live runs are
  byte-for-byte preserved. The "no bet placed" property stays
  true through this fix.
- Surprises become findings in the report, not improvised fixes.

---

## §2 — Why this work exists, and the decision taken

S162 drove the live-lay 503 to `INVALID_INPUT_DATA — customerRef
… 32 character limit`: the app sends a 47-char reference
(`bet-record-{uuid4}`); Betfair caps it at 32. The S163 surgical
draft was found mis-scoped, and a read-only impact review
(`customer_ref_impact_review_report.md`) then established the
decisive fact: **no downstream consumer depends on the outbound
reference's value, format, or length.** Reconciliation keys off
`bets.betfair_bet_id`, settlement off `betfair_selection_id`, and
nothing reverse-maps a Betfair-returned ref to an internal
record or enum (report §5.3).

The operator's call, on that evidence, is **Option B —
decouple**, in its schema-less form: the natural `bet_id` and the
Betfair reference have conflicting length requirements, so they
are separated permanently rather than forced into one capped
value. This also **fixes a pre-existing latent bug** — the
47-char ids currently fail the UUID-recovery parsers and fall
back to a random UUID, degrading free-bet-deploy correlation
today (report §5.4); a clean `bet_id` resolves it.

---

## §3 — Pre-reads

**Required (read in full before editing):**
- This brief.
- `dr029/2_4_betfair_streaming/customer_ref_impact_review_report.md`
  — the grounding. Every anchor below traces to it.
- `dr029/2_4_betfair_streaming/placement_failure_diagnostic_report.md`
  — the S162 503 diagnostic.

**Reference-only (consult as needed):**
- `customer_ref_fix_brief.md` — the **superseded** v1 draft. Read
  only to understand what NOT to do (it patched one placement
  site and rested on unverified consumer assumptions). **Do not
  execute it.**

---

## §4 — System access & working-tree discipline

- **Filesystem:** Mac, `bethub-v3` at
  `/Users/tim/Desktop/Projects/bethub-v3`. **READ-WRITE**, limited
  to the named anchors in §5 plus their tests.
- **Dirty tree (Session 35/36 discipline).** The tree is
  in-flight by design; the review flagged uncommitted work in
  `_translation.py` (the function moved off its documented
  lines). Therefore:
  - **No git mutation** — no `add` / `commit` / `stash` /
    `restore` / `checkout` / `reset`.
  - Read working-tree state at session start (`git status`,
    `git diff --stat`); record it in the report.
  - **Locate every anchor by symbol/grep, not by the line
    numbers in this brief** — they are report-time references and
    the tree has moved since. Grep for the function names and the
    literal strings named in §5.
  - After each edit, run `git diff <file>` and confirm only the
    intended hunk changed.
  - At session close, `git status` must show the **same set of
    dirty files** as at start plus only the files §5 authorises.
  - **If an edit region intersects pre-existing uncommitted work**
    in a way that's ambiguous (especially in `_translation.py`),
    do **not** guess — surface it as a finding and make the
    minimal safe edit, or stop and report.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021.

---

## §5 — The fix (changes in dependency order)

Four code changes + tests. Anchors are report-time references;
re-ground each by grep before editing.

### §5.1 — Unify `bet_id` to the clean canonical form (lay route)

**Why:** the lay route is the only path that stamps the 47-char
`bet-record-{uuid4}`; every other path already uses the canonical
`bet-{uuid4}` (40) via `record_builder._resolve_id(prefix="bet")`.
Unifying makes `bet_id` uniformly `bet-{uuid4}`, which fixes the
silent `_coerce_uuid`/`_safe_uuid` fallback.

**Anchor:** `ui/api/routers/racing.py:981` (`place_lay`),
`body.bet_id or f"bet-record-{uuid4()}"`.

**Change:** when the modal supplies no `bet_id`, generate the
canonical `bet-{uuid4}` form (reuse `_resolve_id(prefix="bet")`
if importable without a layering violation — see §5.2 on
placement of shared helpers; otherwise generate `f"bet-{uuid4()}"`
inline). Keep honouring a modal-supplied `body.bet_id` if present.
**`bet_id` has no Betfair cap** — it is the internal PK; do not
shorten it, only de-`record-` it.

### §5.2 — Mint a dedicated ≤32 Betfair reference (both sites)

**Why:** this is the decouple. The Betfair reference stops being
`bet_id` and becomes its own short, unique, recognisable token.

**The reference scheme (dev-lead call):** a single helper mints
`f"bh-{uuid4().hex[:26]}"` — `bh-` (BetHub, recognisable on the
Betfair statement) + 26 hex chars = **29 chars**, comfortably
under 32, ~104 bits of entropy (collision-free at any realistic
volume). One helper, used by both placement sites.

**Helper placement (architecture constraint):** define a single
`make_betfair_customer_ref()` in a module **both** placement
sites can import **without violating the import-linter contracts**
(`.importlinter`). If no such shared location exists without a
contract change, surface that as a finding and fall back to the
same tiny helper defined at each site's nearest in-layer util —
**do not edit `.importlinter`** and do not introduce a layering
violation.

**Stability across retries (the one real constraint — report
§5.2):** the reference doubles as Betfair's top-level `customerRef`
de-dupe token, which the orchestrator reuses across retry
attempts within a cycle. So the reference must be minted **once
per logical order** and threaded through retries — exactly where
`customer_order_ref` flows today. Do not regenerate it per
attempt.

**Anchors:**
- **Lay route** — `ui/api/routers/racing.py:990`,
  `customer_order_ref=bet_id`. Change to mint the dedicated ref
  once per request and pass that. Confirm the lay path has no
  internal retry that would re-mint; if it does, hoist the mint
  above the retry.
- **Hedge orchestrator** —
  `workflows/bet_entry/v1/orchestrator.py:743`,
  `request.customer_order_ref or f"bet-record-{uuid.uuid4()}"`.
  Replace the `bet-record-{uuid4}` fallback with the helper. The
  existing reuse across retries (L855/871/935) is preserved
  because only the minted value changes, not the threading.

**Note:** `bet_id` and the new reference are now independent
values. Nothing reads the reference back to match a record
(report §5.3), so this breaks no consumer.

### §5.3 — Strategy reference ≤15 boundary map

**Why:** `customerStrategyRef` is capped at 15. Only
`StrategyTag.SYNTHETIC_EACH_WAY` (`synthetic_each_way`, 18)
breaches, lay-route only (the hedge path sends `None`). The
stored enum and `bets.strategy_tag` column must stay full (a
reverse-map would break — though none exists today; report §5.3).

**Change:** at the point the body's `customer_strategy_ref` is
assigned (lay route `racing.py:995`, or centrally in
`_translation.py` where `customerStrategyRef` is set), apply a
boundary map `StrategyTag → ≤15 code`. Read the **actual**
`StrategyTag` enum; build an **exhaustive** `dict[StrategyTag,
str]` covering every member — prefer the existing value where it
is already ≤15, define a short recognisable code where it is not
(`synthetic_each_way` → a ≤15 form such as `synth_ew`). An
unmapped tag must fail loudly (explicit raise), not silently
pass an over-length value — the guard in §5.4 backstops this.
Leave the enum definition and the DB column untouched (no
migration).

### §5.4 — Client-side length guard (close the class)

**Why:** today the only enforcement of 32/32/15 is Betfair's 503.
That cost two sessions of digging. A local guard turns a silent
remote rejection into an immediate, named, local failure.

**Change:** in `_translation.py._build_place_orders_params` (the
single funnel all placement paths pass through — re-locate by
symbol, the tree has moved), after the three references are
assigned, validate each against its cap
(`customerOrderRef` 32, `customerRef` 32, `customerStrategyRef`
15). On breach, **raise** — do not truncate (truncation reraises
the collision risk and masks bugs). Use the betfair client's
existing error type (read `_errors.py`); the message must name
the offending field, the cap, and the actual length, so any
future breach is diagnosable on sight. Define the caps as named
constants at the top of the funnel.

### §5.5 — Tests

- **Update format-assuming tests:**
  `tests/workflows/bet_entry/v1/test_orchestrator.py` (the
  `startswith("bet-record-")` assertion — the hedge ref is no
  longer `bet-record-`). Re-ground the test against the new
  reference shape and the clean `bet_id`.
  `tests/ui/api/test_racing.py` (`startswith("bet-")`) should
  still hold for `bet_id` (now `bet-{uuid4}`) — confirm, don't
  weaken.
- **Add tests:**
  - the minted reference is ≤32 at **both** placement sites;
  - the reference is **stable across a retry cycle** (minted
    once, reused — guards the de-dupe contract);
  - the strategy boundary map yields ≤15 for every `StrategyTag`,
    `synthetic_each_way` included;
  - the guard **raises** (named error) when any reference exceeds
    its cap, for all three fields;
  - `bet_id` is the canonical `bet-{uuid4}` (40) on the lay route,
    and `_coerce_uuid`/`_safe_uuid` now recover the UUID from it
    (the latent-bug fix is exercised, not assumed).
- Establish the current full-suite baseline empirically at
  session start (do **not** hard-code a count); re-run the full
  suite after; report both numbers and account for every delta.

---

## §6 — Sequencing within the session

1. Read working-tree state (§4) and the test baseline (§5.5).
2. §5.1 (clean `bet_id`) → §5.2 (mint + decouple the reference) —
   §5.2's lay-route edit sits right beside §5.1's, do them
   together.
3. §5.3 (strategy map), then §5.4 (guard) — the guard last so it
   validates the now-correct values and would have caught the
   originals.
4. §5.5 tests; full-suite re-run.

Code may reorder with reason, but the guard (§5.4) lands after
the value fixes so a green run proves the guard passes legal
values rather than masking a missed one.

## §7 — Empirical verification (pre / post)

Capture both states in the report:
- **Pre:** grep-confirm both placement sites emit a 47-char
  reference; the strategy value `synthetic_each_way` is 18; no
  length guard exists. Full-suite baseline count.
- **Post:** both sites emit a ≤32 reference (show the literal
  lengths); every mapped strategy code is ≤15; the guard raises
  on a synthetic over-length input (show the error); full suite
  green at the accounted-for count.
- **Carve-out (cannot verify in-session):** the live $5 lay
  actually placing is an **operator-side** check against live
  Betfair — out of Code's scope. The report states the fix is
  code-complete and names the live lay as the remaining gate.

## §8 — Output spec

**Single file:**
`dr029/2_4_betfair_streaming/customer_ref_fix_report.md`.

Sections: working-tree attestation (start vs end `git status`);
per-anchor change summary (file, symbol, before/after); the
reference scheme and helper location actually used (+ any
import-linter finding); the strategy map as built; the guard +
error type used; test changes and pre/post suite counts; the
§7 pre/post evidence; an explicit "live $5 lay is the remaining
operator gate" line. Length ≈ 200–350 lines.

**Does NOT contain:** a schema change; any edit outside the §5
anchors + their tests; any git mutation; recommendations beyond
the named remaining gate.

## §9 — Hard limits

- **No schema change.** No new column, no migration. The
  reference is not persisted (report §5.4); reconciliation
  already round-trips via `bets.betfair_bet_id`.
- **Named anchors only** — the four §5 changes + their tests.
  No drift into adjacent code "while we're here".
- **No git mutation** (per §4 dirty-tree discipline).
- **Do not refactor** `_coerce_uuid` / `_safe_uuid` — they self-
  heal once `bet_id` is clean. Leave them as-is.
- **Do not touch the soft-book `log_bet` path** (`racing.py:877`)
  — record-only, never placed.
- **Do not edit `.importlinter`** or introduce a layering
  violation to place the helper (§5.2).
- **Bet-safety gate** — byte-for-byte preserved. The fix changes
  only the reference string, the `bet_id` format, the strategy
  code, and adds a guard. Nothing touches stake, price,
  liability, or the gate. The "5 live runs, no bet placed"
  property must remain true.
- **No scope creep** into other §2.x items, the broader `bet_id`
  scheme harmonisation, sports placement (W18), or cutover (W16).
- **Single bounded Code session.** If it doesn't fit, that's a
  finding — partial-but-coherent beats complete-but-lost.
- Adelaide local timestamps per DR-021.

## §10 — What happens after Code's session

The next Claude Chat session triages `customer_ref_fix_report.md`:
reads it, confirms the working-tree attestation is clean and the
suite is green, and surfaces the result. If clean, the operator
re-runs the **live $5 lay** — which should now place, since the
reference is finally Betfair-legal at both sites. A successful
lay clears the last validation gate before the **W16 v2→v3
cutover** decision. Code does not run the live lay and does not
write the next artefact.

## §11 — Cross-references

- **Scope doc:** `2_4_betfair_streaming.md` (§2.4 Betfair
  Streaming).
- **Grounding:** `customer_ref_impact_review_report.md` (the
  read-only map and options analysis this fix enacts).
- **Supersedes:** `customer_ref_fix_brief.md` (S163 surgical
  draft — do not execute).
- **Prior reports:** `placement_failure_diagnostic_report.md`
  (S162, named the `customerRef` 503).
- **DRs:** DR-021 (timestamp anchoring, Adelaide local time).
- **Decision enacted:** Option B (decouple), schema-less form —
  operator's call on the impact-review evidence, 2026-06-18.
- **Parking lot (excluded):** broader `bet_id` scheme
  harmonisation; a formal `betfair_ref` column (deferred —
  unneeded for any consumer); sports path (W18); cutover (W16).

---

*End of brief.*
